# -*- coding: utf-8 -*-

import os

import re
from subprocess import PIPE
import luigi
import law
from luigi.util import inherits
import law.contrib.htcondor
from law.util import merge_dicts

law.contrib.load("wlcg")


class CommonConfig(luigi.Config):

    wlcg_path = luigi.Parameter(
        description="Protocol and path suffix pointing to the remote parent directory for generation outputs, \
                e.g. `srm://cmssrm-kit.gridka.de:8443/srm/managerv2?SFN=/pnfs/gridka.de/cms/disk-only/store/user/<USER_NAME>`."
    )
    input_file_name = luigi.Parameter(
        description="Name of the Herwig input file used for event generation without file extension `.in`. \
                Per default saved in the `inputfiles` directory."
    )


@inherits(CommonConfig)
class GenerationScenarioConfig(luigi.Config):

    mc_setting = luigi.Parameter(
        description="Scenario of the MC production. Typically one of the following: `withNP`, `NPoff`, `MPIoff` or `Hadoff`. \
                Used to differentiate between output-paths for different generation scenarios."
    )



@inherits(CommonConfig)
class Task(law.Task):

    _wlcg_file_systems = {}

    @classmethod
    def get_wlcg_file_system(cls, wlcg_path):
        if wlcg_path not in cls._wlcg_file_systems:
            cls._wlcg_file_systems[wlcg_path] = law.wlcg.WLCGFileSystem(None, base=wlcg_path)

        return cls._wlcg_file_systems[wlcg_path]

    def local_path(self, *path):
        parts = (os.getenv("ANALYSIS_DATA_PATH"),) + (self.__class__.__name__,  self.input_file_name,) + path
        return os.path.join(*parts)

    def local_target(self, *path):
        return law.LocalFileTarget(self.local_path(*path))

    def remote_path(self, *path):
        parts = (self.__class__.__name__, self.input_file_name,) + path
        return os.path.join(*parts)

    def remote_target(self, *path):
        return law.wlcg.WLCGFileTarget(
            self.remote_path(*path),
            self.get_wlcg_file_system(self.wlcg_path),
        )


class HTCondorJobManager(law.contrib.htcondor.HTCondorJobManager):

    status_line_cre = re.compile("^(\d+\.\d+)" + 4 * "\s+[^\s]+" + "\s+([UIRXSCHE<>])\s+.*$")

    def get_htcondor_version(cls):
        return (8, 6, 5)

#    @classmethod
#    def map_status(cls, status_flag):
#        if status_flag in ("U", "I", "S"):
#            return cls.PENDING
#        elif status_flag in ("R","<",">"):
#            return cls.RUNNING
#        elif status_flag in ("C"):
#            return cls.FINISHED
#        elif status_flag in ("H", "E"):
#            return cls.FAILED
#        else:
#            return cls.FAILED


@inherits(CommonConfig)
class HTCondorWorkflow(law.contrib.htcondor.HTCondorWorkflow):

    htcondor_accounting_group = luigi.Parameter(
        significant=False,
        description="HTCondor accounting group jobs are submitted."
    )
    htcondor_requirements = luigi.Parameter(
        significant=False,
        description="Additional requirements on e.g. the target machines to run the jobs."
    )
    htcondor_remote_job = luigi.Parameter(
        default="True",
        significant=False,
        description="ETP HTCondor specific flag to allow jobs to run on remote resources."
    )
    htcondor_user_proxy = luigi.Parameter(
        significant=False,
        description="X509 user proxy certificate to authenticate towards grid resources."
    )
    htcondor_walltime = luigi.Parameter(
        significant=False,
        description="Requested walltime for the jobs."
    )
    htcondor_request_cpus = luigi.Parameter(
        default="1",
        significant=False,
        description="Number of CPU cores to request for each job."
    )
    htcondor_request_memory = luigi.Parameter(
        default="2500",
        significant=False,
        description="Amount of memory to request for each job."
    )
    htcondor_request_disk = luigi.Parameter(
        significant=False,
        description="Amount of disk scratch space to request for each job."
    )
    htcondor_universe = luigi.Parameter(
        default="docker",
        significant=False,
        description="HTcondor universe to run jobs in."
    )
    htcondor_docker_image = luigi.Parameter(
        default="mschnepf/slc7-condocker",
        significant=False,
        description="Docker image to use for running docker jobs."
    )
    bootstrap_file = luigi.Parameter(
        description="Path to the source script providing the software environment to source at job start."
    )

    # set Law options
    output_collection_cls = law.SiblingFileCollection
    create_branch_map_before_repr = True

    def htcondor_create_job_manager(self, **kwargs):
        kwargs = merge_dicts(self.htcondor_job_manager_defaults, kwargs)
        return HTCondorJobManager(**kwargs)

    #def htcondor_output_postfix(self):
    #    return "_{}To{}".format(self.start_branch, self.end_branch)

    def htcondor_output_directory(self):
        return law.wlcg.WLCGDirectoryTarget(
            self.remote_path(),
            law.wlcg.WLCGFileSystem(None, base="{}".format(self.wlcg_path))
            )

    def htcondor_create_job_file_factory(self):
        factory = super(
            HTCondorWorkflow,
            self
        ).htcondor_create_job_file_factory()
        factory.is_tmp = False
        return factory

    def htcondor_bootstrap_file(self):
        return law.util.rel_path(__file__, "..", self.bootstrap_file)

    def htcondor_job_config(self, config, job_num, branches):
        config.custom_content = []
        config.custom_content.append(("accounting_group", self.htcondor_accounting_group))
        # config.custom_content.append(("getenv", "true"))
        config.render_variables["analysis_path"] = os.getenv("ANALYSIS_PATH")
        config.custom_content.append(("Requirements", self.htcondor_requirements))
        config.custom_content.append(("+RemoteJob", self.htcondor_remote_job))
        config.custom_content.append(("universe", self.htcondor_universe))
        config.custom_content.append(("docker_image", self.htcondor_docker_image))
        config.custom_content.append(("+RequestWalltime", self.htcondor_walltime))
        config.custom_content.append(("x509userproxy", self.htcondor_user_proxy))
        config.custom_content.append(("request_cpus", self.htcondor_request_cpus))
        config.custom_content.append(("RequestMemory", self.htcondor_request_memory))
        config.custom_content.append(("RequestDisk", self.htcondor_request_disk))

        if self.branch == -1:
            prevdir = os.getcwd()
            os.system('cd $ANALYSIS_PATH')
            if not os.path.isfile('generation.tar.gz'):
                # if os.path.isfile('generation.tar.gz'):
                #     from shutil import move
                    # move('generation.tar.gz', 'old_generation.tar.gz')
                    # print("Tarball already exists! Preparing a new one!")
                os.system(
                    "tar --exclude=*.git* "
                    + "-czf generation.tar.gz "
                    + "generation analyses inputfiles setup luigi.cfg law.cfg luigi law six enum34-1.1.10"
                )
            os.chdir(prevdir)

        config.input_files["TARBALL"] = law.util.rel_path(__file__, '..', '../generation.tar.gz')

        return config
