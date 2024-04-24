import law
import luigi
from luigi.util import inherits
from law.util import interruptable_popen
import os
import multiprocessing  # for cpu_count

from subprocess import PIPE
from generation.framework.utils import run_command, identify_inputfile, set_environment_variables

from generation.framework import Task, CommonConfig


class SherpaSetup(law.Task):
    """Setup CMSSW environment for Sherpa"""

    mc_generator = "sherpa"

    def output(self):
        return law.LocalDirectoryTarget(
            os.path.join(
                "$ANALYSIS_PATH",
                "software",
                "CMSSW_10_6_40",
            )
        )

    def run(self):
        print("=======================================================")
        print("Setting up CMSSW environment for Sherpa")
        print("=======================================================")

        # create base dir if it does not exist
        base_dir = self.output().parent
        base_dir.touch()

        # set environment variables
        cms_env = set_environment_variables("/cvmfs/cms.cern.ch/cmsset_default.sh")
        try:
            run_command(
                ["scram", "project", "CMSSW_10_6_40"],
                env=cms_env,
                cwd=base_dir.path,
            )
        except RuntimeError as e:
            self.output().remove()
            raise e


@inherits(CommonConfig)
class SherpaConfig(law.ExternalTask):

    mc_generator = "sherpa"

    config_path = luigi.Parameter(
        significant=True,
        default="default",
        description="Directory where the Sherpa config file resides. Default translates to `inputfiles/sherpa/[input_file_name]`."
    )

    def output(self):
        return law.law.LocalFileTarget(
            identify_inputfile(self.input_file_name, self.config_path, self.mc_generator)
        )


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
            'SherpaSetup': SherpaSetup.req(self),
            'SherpaConfig': SherpaConfig.req(self),
        }

    def output(self):
        return {
            "Process": law.LocalDirectoryTarget(
                os.path.join(
                    "$ANALYSIS_PATH",
                    "inputfiles",
                    "sherpa",
                    self.input_file_name,
                    "Process"
                )
            ),
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
            "Sherpa",
            "-f",
            self.input()['SherpaConfig'].path,
            "-e 0",
        ]

        # TODO: check uf the init step is needed for NLO, definetly not for LO
        # _sherpa_prep = ["INIT_ONLY=1"]
        # print('Executable: {}'.format(" ".join(_sherpa_exec + _sherpa_prep)))
        # code, out, error = interruptable_popen(
        #     _sherpa_exec + _sherpa_prep,
        #     stdout=PIPE,
        #     stderr=PIPE,
        #     env=sherpa_env,
        #     cwd=os.path.dirname(self.input()['SherpaConfig'].path),
        # )
        # if code != 1:
        #     self.output().remove()
        #     raise RuntimeError(
        #         'Sherpa INIT returned unexpected exit status {code}!\n'.format(code=code)
        #         + '\tOutput:\n{}\n'.format(out)
        #         + '\tError:\n{}\n'.format(error)
        #     )
        # print(out)

        mpirun = ["mpirun", "-n", str(self.ncores)]
        try:
            run_command(
                mpirun + _sherpa_exec,
                env=sherpa_env,
                cwd=self.input()['SherpaConfig'].parent.path,
            )
        except RuntimeError as e:
            for output in self.output().values():
                output.remove()
            raise e

        print("=======================================================")
