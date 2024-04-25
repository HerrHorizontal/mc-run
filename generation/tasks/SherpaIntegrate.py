import law
import luigi
from luigi.util import inherits
from law.util import interruptable_popen
import os
import multiprocessing  # for cpu_count

from subprocess import PIPE
from generation.framework.utils import run_command, identify_inputfile, set_environment_variables

from generation.framework import Task, CommonConfig

from SherpaBuild import SherpaConfig, SherpaBuild


class SherpaIntegrate(Task):
    """
    Create Sherpa Matrix Elements and Grids for the chosen process.
    """
    ncores = luigi.IntParameter(
        default=int(multiprocessing.cpu_count()/4),
        description="Number of cores used for the Sherpa integration step."
    )

    def requires(self):
        return {
            "SherpaConfig": SherpaConfig.req(self),
            "SherpaBuild": SherpaBuild.req(self),
        }

    def output(self):
        return {
            "Results": law.LocalFileTarget(
                os.path.join(
                    "$ANALYSIS_PATH",
                    "inputfiles",
                    "sherpa",
                    self.input_file_name,
                    "Results.db"
                )
            ),
        }

    def run(self):
        # actual payload:
        print("=======================================================")
        print("Starting integration step to generate integration grids")
        print("=======================================================")

        # set environment variables
        sherpa_env = set_environment_variables(
            os.path.expandvars("$ANALYSIS_PATH/setup/setup_sherpa.sh")
        )

        # prepare Sherpa for multicore integration
        _sherpa_exec = [
            "mpirun", "-n", str(self.ncores),
            "Sherpa",
            "-f",
            self.input()['SherpaConfig'].path,
            "-e 0",
        ]

        try:
            run_command(
                _sherpa_exec,
                env=sherpa_env,
                cwd=self.input()['SherpaConfig'].parent.path,
            )
        except RuntimeError as e:
            for output in self.output().values():
                output.remove()
            raise e

        print("=======================================================")
