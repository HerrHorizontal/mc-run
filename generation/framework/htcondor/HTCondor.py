import os
import socket
import math
from enum import Enum

import law
import law.config
import luigi
from generation.framework.htcondor.BundleSoftware import BundleRepo
from law.contrib.htcondor.job import HTCondorJobManager
from law.util import merge_dicts

law.contrib.load("tasks", "wlcg", "git", "htcondor")


class HTCondorWorkflow(law.htcondor.HTCondorWorkflow):
    ConfigParser = luigi.configuration.cfg_parser.LuigiConfigParser.instance()
    # ConfigParser = law.config.Config.instance()
    transfer_logs = luigi.BoolParameter(
        default=True,
        significant=False,
        description="transfer job logs to the output directory; default: True",
    )
    htcondor_logs = luigi.BoolParameter(
        default=False,
        significant=False,
        description="transfer htcondor internal submission logs to the output directory; "
        "default: False",
    )
    htcondor_accounting_group = luigi.Parameter(
        default=ConfigParser.get("HTCondorDefaults", "htcondor_accounting_group"),
        # default=ConfigParser.get_expanded("luigi_HTCondor","htcondor_accounting_group"),
        significant=False,
        description="HTCondor accounting group jobs are submitted.",
    )
    htcondor_requirements = luigi.Parameter(
        default=ConfigParser.get("HTCondorDefaults", "htcondor_requirements"),
        significant=False,
        description="Additional requirements on e.g. the target machines to run the jobs.",
    )
    htcondor_remote_job = luigi.Parameter(
        default=ConfigParser.get("HTCondorDefaults", "htcondor_remote_job"),
        significant=False,
        description="ETP HTCondor specific flag to allow jobs to run on remote resources.",
    )
    htcondor_walltime = law.DurationParameter(
        default=1.0,
        unit="h",
        significant=False,
        description="Maximum runtime for jobs. Default unit is hours. Defaults to 1h.",
    )
    htcondor_request_cpus = luigi.IntParameter(
        default=ConfigParser.get("HTCondorDefaults", "htcondor_request_cpus"),
        significant=False,
        description="Number of CPU cores to request for each job.",
    )
    htcondor_request_memory = law.BytesParameter(
        default=law.NO_FLOAT,
        unit="MB",
        significant=False,
        description="Requested memory in MB. Default is empty, which uses the cluster default.",
    )
    htcondor_request_disk = law.BytesParameter(
        default=law.NO_FLOAT,
        significant=False,
        unit="kB",
        description="Disk scratch space to request for each job in kB.",
    )
    htcondor_universe = luigi.Parameter(
        default=ConfigParser.get("HTCondorDefaults", "htcondor_universe"),
        significant=False,
        description="HTcondor universe to run jobs in.",
    )
    htcondor_docker_image = luigi.Parameter(
        default=ConfigParser.get("HTCondorDefaults", "htcondor_docker_image"),
        significant=False,
        description="Docker image to use for running docker jobs.",
    )
    bootstrap_file = luigi.Parameter(
        default="bootstrap.sh",
        significant=False,
        description="Path to the source script providing the software environment to source at job start.",
    )

    # identify the domain on which HTCondor scheduler is running for job classad adjustments
    class Domain(Enum):
        CERN = 1
        ETP = 2
        OTHERS = -1

    domain = socket.getfqdn()
    if str(domain).endswith("cern.ch"):
        domain = Domain.CERN
    elif str(domain).endswith(("etp.kit.edu", "darwin.kit.edu", "gridka.de", "bwforcluster")):
        domain = Domain.ETP
    else:
        raise RuntimeError(
            f"HTCondor batch settings not implemented for domain {domain}!"
        )
        domain = Domain.OTHERS

    # set Law options
    output_collection_cls = law.SiblingFileCollection
    create_branch_map_before_repr = True

    def htcondor_workflow_requires(self):
        reqs = super().htcondor_workflow_requires()
        reqs["repo"] = BundleRepo.req(self, replicas=3)

        return reqs

    def htcondor_output_directory(self):
        job_dir = law.config.get_expanded("job", "job_file_dir")
        return law.LocalDirectoryTarget(f"{job_dir}/{self.task_id}/")

    def htcondor_create_job_file_factory(self):
        factory = super().htcondor_create_job_file_factory(
            dir=self.htcondor_output_directory().abspath
        )
        return factory

    def htcondor_bootstrap_file(self):
        bootstrap_file = law.util.rel_path(__file__, self.bootstrap_file)
        return law.JobInputFile(bootstrap_file, share=True, render_job=True)

    def htcondor_job_config(self, config, job_num, branches):
        # setup logging
        # some htcondor setups require a "log" config, but we can safely use /dev/null by default
        config.log = "/dev/null"
        if self.htcondor_logs:
            config.log = "job.log"
            config.stdout = "stdout.log"
            config.stderr = "stderr.log"
        # set unique batch name for bettter identification
        config.custom_content.append(("JobBatchName", self.task_id))
        # set htcondor universe to docker
        config.universe = self.htcondor_universe
        config.custom_content.append(("docker_image", self.htcondor_docker_image))
        config.custom_content.append(("x509userproxy", law.wlcg.get_vomsproxy_file()))
        # request runtime
        if self.htcondor_walltime is not None and self.htcondor_walltime > 0:
            max_runtime = int(math.floor(self.htcondor_walltime * 3600)) - 1
            config.custom_content.append(("+MaxRuntime", max_runtime))  # CERN
            config.custom_content.append(("+RequestRuntime", max_runtime))  # NAF?
            config.custom_content.append(("+RequestWalltime", max_runtime))  # ETP
        # request cpus
        config.custom_content.append(("RequestCpus", self.htcondor_request_cpus))
        # request memory
        if self.htcondor_request_memory is not None and self.htcondor_request_memory > 0:
            config.custom_content.append(("RequestMemory", self.htcondor_request_memory))
        # request disk space
        if self.htcondor_request_disk is not None and self.htcondor_request_disk > 0:
            config.custom_content.append(("RequestDisk", self.htcondor_request_disk))
        # further custom htcondor requirements
        config.custom_content.append(("Requirements", self.htcondor_requirements))
        # custom ETP stuff
        if self.domain == self.Domain.ETP:
            config.custom_content.append(
                ("accounting_group", self.htcondor_accounting_group)
            )
            config.custom_content.append(("+RemoteJob", self.htcondor_remote_job))
            # config.custom_content.append(("+RequestWalltime", max_runtime))

        # include the wlcg specific tools script in the input sandbox
        tools_file = law.util.law_src_path("contrib/wlcg/scripts/law_wlcg_tools.sh")
        config.input_files["wlcg_tools"] = law.JobInputFile(
            tools_file, share=True, render=False
        )
        
        # load software bundles from grid storage
        reqs = self.htcondor_workflow_requires()
        def get_bundle_info(task):
            uris = task.output().dir.uri(return_all=True)
            pattern = os.path.basename(task.get_file_pattern())
            return ",".join(uris), pattern
        # add repo bundle variables
        uris, pattern = get_bundle_info(reqs["repo"])
        config.render_variables["repo_uris"] = uris
        config.render_variables["repo_pattern"] = pattern

        return config
