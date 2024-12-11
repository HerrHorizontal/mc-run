import os
from copy import copy
from functools import cache

import law
import luigi
from generation.framework.htcondor import HTCondorWorkflow
from generation.framework.tasks import BaseTask
from generation.framework.utils import run_command, set_environment_variables
from law.logger import get_logger

logger = get_logger(__name__)
rivet_env = set_environment_variables(
    os.path.expandvars("$ANALYSIS_PATH/setup/setup_rivet.sh")
)


@cache
def get_default_rivet_analyses():
    utils_logger = get_logger("generation.framework.utils")
    default_rivet_env = copy(rivet_env).update({"RIVET_ANALYSIS_PATH": ""})
    old_level = utils_logger.getEffectiveLevel()
    utils_logger.setLevel("WARNING")
    rivet_list = run_command(["rivet", "--list"], env=default_rivet_env)[1]
    utils_logger.setLevel(old_level)
    return set([line.split(" ")[0] for line in rivet_list.split("\n")])


class RivetBuild(HTCondorWorkflow, law.LocalWorkflow, BaseTask):
    """
    Build/Compile  Rivet analyses
    """

    rivet_analyses = luigi.ListParameter(
        description="List of IDs of Rivet analyses to compile."
    )

    compiler_flags = luigi.ListParameter(
        default=[],
        significant=False,
        description="List of compiler flags to add to the build command.",
    )

    rivet_os_version = rivet_env["RIVET_OS_DISTRO"]

    exclude_params_req = {"compiler_flags"}
    exclude_params_req_get = {
        "htcondor_remote_job",
        "htcondor_accounting_group",
        "htcondor_request_cpus",
        "htcondor_universe",
        "htcondor_docker_image",
        "transfer_logs",
        "local_scheduler",
        "tolerance",
        "acceptance",
        "only_missing",
    }

    def create_branch_map(self):
        # check whether configured analyses are built-in, only build missing
        rivet_default_anas = get_default_rivet_analyses()
        missing_anas = set(self.rivet_analyses) - rivet_default_anas
        return {branch: str(ana) for branch, ana in enumerate(missing_anas)}

    def remote_path(self, *path):
        parts = (
            self.__class__.__name__,
            self.rivet_os_version,
        ) + path
        return os.path.join(*parts)

    def output(self):
        return self.remote_target(f"Rivet{self.branch_data}.so")

    def run(self):
        # branch data
        analysis = self.branch_data

        # ensure that the output directory exists
        self.output().parent.touch()

        # actual payload:
        print("=======================================================")
        print(f"Building missing Rivet analysis {analysis}")
        print("=======================================================")

        cwd = law.LocalDirectoryTarget(is_tmp=True)
        cwd.touch()
        so_path = os.path.join(cwd.abspath, f"Rivet{analysis}.so")
        code_path = os.path.abspath(
            os.path.join(
                os.path.expandvars("$ANALYSIS_PATH"), "analyses", f"{analysis}.cc"
            )
        )
        if not os.path.isfile(code_path):
            raise FileNotFoundError(
                f"Rivet code {code_path} for analysis {analysis} not found!"
                + "Add the .cc file to analyses directory!"
            )

        _rivet_exec = (
            ["rivet-build"]
            + [str(flag) for flag in self.compiler_flags]
            + [so_path, code_path]
        )
        run_command(_rivet_exec, env=rivet_env)
        self.output().move_from_local(so_path)

        print("=======================================================")
