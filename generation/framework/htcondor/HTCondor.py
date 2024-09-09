import os
import re

import law
import luigi
from generation.framework.htcondor.BundleSoftware import BundleRepo
from law.util import merge_dicts

law.contrib.load("tasks", "wlcg", "git", "htcondor")


class HTCondorJobManager(law.htcondor.HTCondorJobManager):
    status_line_cre = re.compile(
        r"^(\d+\.\d+)" + 4 * r"\s+[^\s]+" + r"\s+([UIRXSCHE<>])\s+.*$"
    )

    def get_htcondor_version(cls):
        return (8, 6, 5)

    @classmethod
    def map_status(cls, status_flag):
        if status_flag in ("0", "1", "U", "I"):
            return cls.PENDING
        elif status_flag in ("2", "7", "R", "<", ">", "S"):
            return cls.RUNNING
        elif status_flag in ("4", "C"):
            return cls.FINISHED
        elif status_flag in ("5", "6", "H", "E"):
            return cls.FAILED
        else:
            return cls.FAILED


class HTCondorWorkflow(law.htcondor.HTCondorWorkflow):
    htcondor_accounting_group = luigi.Parameter(
        significant=False,
        description="HTCondor accounting group jobs are submitted.",
    )
    htcondor_requirements = luigi.Parameter(
        significant=False,
        description="Additional requirements on e.g. the target machines to run the jobs.",
    )
    htcondor_remote_job = luigi.Parameter(
        default="True",
        significant=False,
        description="ETP HTCondor specific flag to allow jobs to run on remote resources.",
    )
    htcondor_walltime = luigi.Parameter(
        significant=False,
        description="Requested walltime for the jobs.",
    )
    htcondor_request_cpus = luigi.Parameter(
        default="1",
        significant=False,
        description="Number of CPU cores to request for each job.",
    )
    htcondor_request_memory = luigi.Parameter(
        default="2500",
        significant=False,
        description="Amount of memory to request for each job.",
    )
    htcondor_request_disk = luigi.Parameter(
        significant=False,
        description="Amount of disk scratch space to request for each job.",
    )
    htcondor_universe = luigi.Parameter(
        default="docker",
        significant=False,
        description="HTcondor universe to run jobs in.",
    )
    htcondor_docker_image = luigi.Parameter(
        default="mschnepf/slc7-condocker",
        significant=False,
        description="Docker image to use for running docker jobs.",
    )
    bootstrap_file = luigi.Parameter(
        default="bootstrap.sh",
        description="Path to the source script providing the software environment to source at job start.",
    )

    # set Law options
    output_collection_cls = law.SiblingFileCollection
    create_branch_map_before_repr = True

    def htcondor_workflow_requires(self):
        reqs = law.htcondor.HTCondorWorkflow.htcondor_workflow_requires(self)
        # add repo and software bundling as requirements when getenv is not requested
        reqs["repo"] = BundleRepo.req(self, replicas=3)

        return reqs

    def htcondor_create_job_manager(self, **kwargs):
        kwargs = merge_dicts(self.htcondor_job_manager_defaults, kwargs)
        job_manager = super().htcondor_create_job_manager(**kwargs)
        job_manager.job_grouping_submit = False
        job_manager.chunk_size_submit = 0
        return job_manager

    def htcondor_output_directory(self):
        job_dir = law.config.get_expanded("job", "job_file_dir")
        return law.LocalDirectoryTarget(f"{job_dir}/{self.task_id}")

    def htcondor_create_job_file_factory(self):
        factory = super(HTCondorWorkflow, self).htcondor_create_job_file_factory()
        factory.is_tmp = False
        return factory

    def htcondor_bootstrap_file(self):
        return law.util.rel_path(__file__, self.bootstrap_file)

    def htcondor_job_config(self, config, job_num, branches):
        config.log = os.path.join("Log.txt")
        config.stdout = os.path.join("Output.txt")
        config.stderr = os.path.join("Error.txt")
        config.custom_content = []
        config.custom_content.append(
            ("accounting_group", self.htcondor_accounting_group)
        )
        config.custom_content.append(("stream_error", "True"))
        config.custom_content.append(("stream_output", "True"))
        config.custom_content.append(("Requirements", self.htcondor_requirements))
        config.custom_content.append(("+RemoteJob", self.htcondor_remote_job))
        config.custom_content.append(("universe", self.htcondor_universe))
        config.custom_content.append(("docker_image", self.htcondor_docker_image))
        config.custom_content.append(("+RequestWalltime", self.htcondor_walltime))
        config.custom_content.append(("x509userproxy", law.wlcg.get_vomsproxy_file()))
        config.custom_content.append(("request_cpus", self.htcondor_request_cpus))
        config.custom_content.append(("RequestMemory", self.htcondor_request_memory))
        config.custom_content.append(("RequestDisk", self.htcondor_request_disk))

        config.custom_content.append(("JobBatchName", self.task_id))

        # include the wlcg specific tools script in the input sandbox
        tools_file = law.util.law_src_path("contrib/wlcg/scripts/law_wlcg_tools.sh")
        config.input_files["wlcg_tools"] = law.JobInputFile(
            tools_file, share=True, render=False
        )

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
