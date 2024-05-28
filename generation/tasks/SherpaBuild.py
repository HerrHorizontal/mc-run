import law
import luigi
from luigi.util import inherits
from law.util import interruptable_popen
import os

from subprocess import PIPE
from generation.framework.utils import run_command, identify_inputfile, set_environment_variables

from generation.framework import GenRivetTask, GenerationScenarioConfig

from law.logger import get_logger


logger = get_logger(__name__)


@inherits(GenerationScenarioConfig)
class SherpaConfig(law.ExternalTask):

    mc_generator = "sherpa"

    config_path = luigi.Parameter(
        significant=True,
        default="default",
        description="Directory where the Sherpa config file resides. Default translates to `inputfiles/sherpa/[campaign]`."
    )

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
            'SherpaConfig': SherpaConfig.req(self),
        }

    def output(self):
        return {
            "Process": law.LocalDirectoryTarget(
                os.path.join(
                    "$ANALYSIS_PATH",
                    "inputfiles",
                    "sherpa",
                    self.campaign,
                    "Process"
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
        work_dir = self.input()['SherpaConfig'].parent.path
        sherpa_init = [
            "Sherpa",
            "-f",
            self.input()['SherpaConfig'].path,
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
                'Sherpa initialization failed with error code {}!\n'.format(code)
                + 'Output:\n{}\n'.format(out)
                + 'Error:\n{}\n'.format(error)
            )
        else:
            logger.info("Sherpa initialization successful.")

        # Build missing matrix elements (loops)
        if os.path.exists(os.path.join(work_dir, "makelibs")):
            print("================================")
            print("Building missing matrix elements")
            print("================================")
            run_command(["./makelibs"], env=sherpa_env, cwd=work_dir)

        print("=======================================================")
