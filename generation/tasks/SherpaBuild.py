import os
from subprocess import PIPE

import law
import luigi
from generation.framework import GenerationScenarioConfig, GenRivetTask
from generation.framework.utils import (
    identify_inputfile,
    run_command,
    set_environment_variables,
)
from law.logger import get_logger
from law.util import interruptable_popen
from luigi.util import inherits

logger = get_logger(__name__)


@inherits(GenerationScenarioConfig)
class SherpaConfig(law.ExternalTask):

    mc_generator = "sherpa"

    config_path = luigi.Parameter(
        significant=True,
        default="default",
        description="Directory where the Sherpa config file resides. Default translates to `inputfiles/sherpa/[campaign]`.",
    )

    exclude_params_req = {"config_path"}
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

    def output(self):
        return law.LocalFileTarget(
            identify_inputfile(self.campaign, self.config_path, self.mc_generator)
        )


class SherpaBuild(GenRivetTask):
    """
    Create Sherpa Matrix Elements and Grids for the chosen process.
    """

    def requires(self):
        return {
            "SherpaConfig": SherpaConfig.req(self),
        }

    def output(self):
        return {
            "Process": law.LocalDirectoryTarget(
                os.path.join(
                    "$ANALYSIS_PATH", "inputfiles", "sherpa", self.campaign, "Process"
                )
            ),
        }

    def run(self):
        # actual payload:
        print("=============================================")
        print("Initializing Sherpa Matrix Element Generation")
        print("=============================================")

        # set environment variables
        sherpa_env = set_environment_variables(
            os.path.expandvars("$ANALYSIS_PATH/setup/setup_sherpa.sh")
        )

        # Initialize Sherpa
        work_dir = self.input()["SherpaConfig"].parent.path
        sherpa_init = [
            "Sherpa",
            "-f",
            self.input()["SherpaConfig"].path,
            "INIT_ONLY=1",
        ]
        logger.info('Running command: "{}"'.format(" ".join(sherpa_init)))
        code, out, error = interruptable_popen(
            sherpa_init,
            stdout=PIPE,
            stderr=PIPE,
            env=sherpa_env,
            cwd=work_dir,
        )
        if code != 1:  # init willr return 1 for normal exit
            raise RuntimeError(
                "Sherpa initialization failed with error code {}!\n".format(code)
                + "Output:\n{}\n".format(out)
                + "Error:\n{}\n".format(error)
            )
        else:
            logger.info("Sherpa initialization successful.")

        # Build missing matrix elements (loops)
        if os.path.exists(os.path.join(work_dir, "makelibs")):
            print("================================")
            print("Building missing matrix elements")
            print("================================")
            run_command(["./makelibs"], env=sherpa_env, cwd=work_dir)
            os.remove(os.path.join(work_dir, "makelibs"))

        print("=======================================================")
