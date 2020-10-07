# -*- coding: utf-8 -*-

import os

import re
import luigi
import law
import law.contrib.htcondor

law.contrib.load("wlcg")

class Task(law.Task):

    wlcg_path = luigi.Parameter()
    input_file_name = luigi.Parameter()
    mc_setting = luigi.Parameter()

    def local_path(self, *path):
        parts = (os.getenv("ANALYSIS_DATA_PATH"),) + (self.__class__.__name__,) + path
        return os.path.join(*parts)

    def local_target(self, *path):
        return law.LocalFileTarget(self.local_path(*path))

    def remote_path(self, *path):
        parts = (self.__class__.__name__,) + path
        return os.path.join(*parts)

    def remote_target(self, *path):
        return law.WLCGFileTarget(self.remote_path(*path),
                                  law.WLCGFileSystem(None, "{}/{}/{}".format(self.wlcg_path, self.input_file_name, self.mc_setting)))

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

class HTCondorWorkflow(law.contrib.htcondor.HTCondorWorkflow):

    htcondor_accounting_group = luigi.Parameter()
    htcondor_requirements = luigi.Parameter()
    htcondor_remote_job = luigi.Parameter()
    htcondor_user_proxy = luigi.Parameter()
    htcondor_walltime = luigi.Parameter()
    htcondor_request_cpus = luigi.Parameter()
    htcondor_request_memory = luigi.Parameter()
    htcondor_universe = luigi.Parameter()
    htcondor_docker_image = luigi.Parameter()
    htcondor_request_disk = luigi.Parameter()
    wlcg_path = luigi.Parameter()
    bootstrap_file = luigi.Parameter()
    mc_setting = luigi.Parameter()

    outputs_siblings = True

    def htcondor_create_job_manager(self):
        return HTCondorJobManager()

    # def htcondor_output_postfix(self):
    #     return "_{}To{}".format(self.start_branch, self.end_branch)

    def htcondor_output_directory(self):
          return law.WLCGDirectoryTarget(
          self.remote_path(),
          law.WLCGFileSystem(None, "{}_{}".format(self.wlcg_path,self.mc_setting)))

    def htcondor_create_job_file_factory(self):
        factory = super(HTCondorWorkflow, self).htcondor_create_job_file_factory()
        factory.is_tmp = False
        return factory

    def htcondor_bootstrap_file(self):
        return law.util.rel_path(__file__, self.bootstrap_file)

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

        prevdir = os.getcwd()
        os.system('cd $ANALYSIS_PATH')
        if not os.path.isfile('generation.tar.gz'):
            os.system('tar --exclude=luigi/.git -czvf generation.tar.gz generation luigi.cfg law.cfg luigi law six enum34-1.1.6')
	    os.chdir(prevdir)

        config.input_files.append(law.util.rel_path(__file__, '../generation.tar.gz'))
        return config
