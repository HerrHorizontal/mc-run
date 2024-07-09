import law
import luigi
import os

from subprocess import PIPE
from generation.framework.utils import (
    run_command,
    set_environment_variables,
)
from generation.framework.tasks import BaseTask
from generation.framework.htcondor import HTCondorWorkflow

from law.logger import get_logger


logger = get_logger(__name__)


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

    rivet_env = set_environment_variables(
        os.path.expandvars("$ANALYSIS_PATH/setup/setup_rivet.sh")
    )
    rivet_os_version = rivet_env["RIVET_OS_DISTRO"]


    exclude_params_req = {
        "compiler_flags"
    }
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
        "only_missing"
    }


    def create_branch_map(self):
        # check whether configured analyses are built-in, only build missing
        missing_anas = []
        for ana in self.rivet_analyses:
            if os.popen(f"rivet --list {ana} | grep {ana}").read() != "":
                logger.info(f"Built-in Rivet analysis {ana}. Skip building...")
            else:
                missing_anas.append(ana)
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
        output = self.output()
        output.parent.touch()

        # actual payload:
        print("=======================================================")
        print(f"Building missing Rivet analysis {analysis}")
        print("=======================================================")

        so_path = os.path.abspath(os.path.join(f"Rivet{analysis}.so"))
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
            [
                "rivet-build",
            ]
            + [str(flag) for flag in self.compiler_flags]
            + [so_path, code_path]
        )

        print("Executable: {}".format(" ".join(_rivet_exec)))

        try:
            code, out, error = run_command(_rivet_exec, env=self.rivet_env)
        except RuntimeError as e:
            logger.error(f"Building of Rivet analysis {analysis} failed!")
            raise e

        if os.path.exists(so_path):
            output.copy_from_local(so_path)

        try:
            os.remove(so_path)
        except:
            logger.error(f"Shared object file {so_path} not created!")

        print("=======================================================")
