import math
import socket
from enum import Enum

import law
import law.config
import luigi
from generation.framework.htcondor.BundleSoftware import BundleRepo
from law.logger import get_logger

logger = get_logger(__name__)

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
    htcondor_container_image = luigi.Parameter(
        default=ConfigParser.get("HTCondorDefaults", "htcondor_container_image"),
        significant=False,
        description="Container/Docker image to use for running docker jobs. Depending on the chosen universe.",
    )
    bootstrap_file = luigi.Parameter(
        default="bootstrap.sh",
        significant=False,
        description="Path to the source script providing the software environment to source at job start.",
    )

    exclude_params_req = {
        "htcondor_requirements",
        "htcondor_remote_job",
        "htcondor_walltime",
        "htcondor_request_cpus",
        "htcondor_request_memory",
        "htcondor_request_disk",
    }

    # identify the domain on which HTCondor scheduler is running for job classad adjustments
    class Domain(Enum):
        CERN = 1
        ETP = 2
        NAF = 3
        OTHERS = -1

    domain = socket.getfqdn()
    if str(domain).endswith("cern.ch"):
        domain = Domain.CERN
    elif str(domain).endswith(
        ("etp.kit.edu", "darwin.kit.edu", "gridka.de", "bwforcluster")
    ) or "nemo" in str(domain):
        domain = Domain.ETP
    elif str(domain).endswith("desy.de"):
        domain = Domain.NAF
    else:
        raise RuntimeError(
            f"HTCondor batch settings not implemented for domain {domain}!"
        )
        domain = Domain.OTHERS

    # set Law options
    output_collection_cls = law.SiblingFileCollection
    create_branch_map_before_repr = True

    def htcondor_output_directory(self):
        job_dir = law.config.get_expanded("job", "job_file_dir")
        return law.LocalDirectoryTarget(f"{job_dir}/{self.task_id}/")

    def htcondor_log_directory(self):
        log_dir = law.config.get_expanded("job", "job_log_dir")
        return law.LocalDirectoryTarget(f"{log_dir}/{self.task_id}/")

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
        if config.universe == "docker":
            config.custom_content.append(
                ("docker_image", self.htcondor_container_image)
            )
        elif config.universe == "container":
            config.custom_content.append(
                ("container_image", self.htcondor_container_image)
            )
        else:
            logger.warning(
                f"HTCondor universe {config.universe} not supported for containerization."
            )
        config.custom_content.append(("x509userproxy", law.wlcg.get_vomsproxy_file()))
        # request runtime
        max_runtime = int(math.floor(self.htcondor_walltime * 3600)) - 1
        # request cpus
        config.custom_content.append(("RequestCpus", self.htcondor_request_cpus))
        # request memory
        if (
            self.htcondor_request_memory is not None
            and self.htcondor_request_memory > 0
        ):
            config.custom_content.append(
                ("RequestMemory", self.htcondor_request_memory)
            )
        # request disk space
        if self.htcondor_request_disk is not None and self.htcondor_request_disk > 0:
            config.custom_content.append(("RequestDisk", self.htcondor_request_disk))
        # further custom htcondor requirements
        config.custom_content.append(("Requirements", self.htcondor_requirements))
        # custom stuff
        if self.domain == self.Domain.CERN:
            config.custom_content.append(("+MaxRuntime", max_runtime))
        if self.domain == self.Domain.ETP:
            config.custom_content.append(("+RequestWalltime", max_runtime))
            config.custom_content.append(
                ("accounting_group", self.htcondor_accounting_group)
            )
            config.custom_content.append(("+RemoteJob", self.htcondor_remote_job))
            # config.custom_content.append(("+RequestWalltime", max_runtime))
        if self.domain == self.Domain.NAF:
            config.custom_content.append(("+RequestRuntime", max_runtime))  # NAF
            # NAF has some custom stuff for containers...
            if self.htcondor_universe == "docker":
                raise NotImplementedError(
                    "Docker via HTCondor is not supported on NAF! Use 'container' universe instead."
                )
            if self.htcondor_universe == "container":
                for i in range(len(config.custom_content)):
                    if config.custom_content[i][0] == "container_image":
                        del config.custom_content[i]
                        break
                config.universe = "vanilla"
                config.custom_content.append(
                    ("+MySingularityImage", f'"{self.htcondor_container_image}"')
                )

        # the repository bundle is small and is therefore shipped via HTCondor with each job,
        # share=True copies it only once into the submission directory instead of once per job;
        # the bundle is created here instead of being a workflow requirement, as this method is only
        # called on submission, while workflow requirements are also resolved inside of jobs
        repo = BundleRepo.req(self)
        if not repo.complete():
            repo.run()
        config.input_files["repo_bundle"] = law.JobInputFile(
            repo.output().abspath, share=True, render=False
        )
        logger.debug(f"HTCondor config:\n{config}")

        return config
