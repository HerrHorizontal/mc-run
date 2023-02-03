
import luigi
from luigi.util import inherits
import os

from subprocess import PIPE
from generation.framework.utils import run_command, rivet_env

from generation.framework.tasks import Task, CommonConfig

from RivetMerge import RivetMerge


@inherits(CommonConfig)
class DeriveNPCorr(Task):
    """
    Plotting class for NP-correction factor plots using the YODA API
    """

    # configuration variables
    mc_setting_full = luigi.Parameter(
        default="withNP",
        description="Scenario identifier for the full MC production, typically `withNP`. \
                Used to identify the output-paths for the full generation scenario."
    )
    mc_setting_partial = luigi.Parameter(
        default="NPoff",
        description="Scenario identifier for the partial MC production, typically `NPoff`, `MPIoff` or `Hadoff`. \
                Used to identify the output-paths for the partial generation scenario, \
                where parts of the generation chain are turned off."
    )
    match = luigi.Parameter(
        # significant=False,
        default=None,
        description="Include analysis objects which name matches this regex."
    )
    unmatch = luigi.Parameter(
        # significant=False,
        default=None,
        description="Exclude analysis objects which name matches this regex."
    )

    exclude_params_req = {
        "source_script",
        "mc_setting_full",
        "mc_setting_partial",
        "match",
        "unmatch"
    }


    def requires(self):
        req = dict()
        req["full"] = RivetMerge.req(
            self, 
            mc_setting = self.mc_setting_full
        )
        req["partial"] = RivetMerge.req(
            self,
            mc_setting = self.mc_setting_partial
        )
        return req


    def output(self):
        output = self.remote_target(
            "w-{match}-wo-{unmatch}/{full}-{partial}-Ratio.yoda".format(
                match = self.match,
                unmatch = self.unmatch,
                full = self.mc_setting_full,
                partial = self.mc_setting_partial
            )
        )
        return output

    def run(self):
        # ensure that the output directory exists
        output = self.output()
        try:
            output.parent.touch()
        except IOError:
            print("Output target doesn't exist!")

        # actual payload:
        print("=======================================================")
        print("Starting NP-factor calculation with YODA")
        print("=======================================================")

        # localize the separate YODA files on grid storage
        print("Inputs:")
        with self.input()["full"].localize('r') as _file:
            print("\tfull: {} cached at {}".format(self.input()["full"], _file.path))
            input_yoda_file_full = _file.path
        with self.input()["partial"].localize('r') as _file:
            print("\tpartial: {} cached at {}".format(self.input()["partial"], _file.path))
            input_yoda_file_partial = _file.path

        # assign paths for output YODA file and plots
        output_yoda = "{full}-{partial}-Ratio.yoda".format(
            full = self.mc_setting_full,
            partial = self.mc_setting_partial
        )
        # execute the script deriving the NP correction plots and files
        executable = [
            "python", os.path.expandvars("$ANALYSIS_PATH/scripts/yodaDeriveNPCorr.py"),
            "--full", "{}".format(input_yoda_file_full),
            "--partial", "{}".format(input_yoda_file_partial),
            "--output-file", "{}".format(output_yoda)
        ]
        executable += ["--match", self.match] if self.match else []
        executable += ["--unmatch", self.unmatch] if self.unmatch else []

        print("Executable: {}".format(" ".join(executable)))

        try:
            run_command(executable, env=rivet_env, cwd=os.path.expandvars("$ANALYSIS_PATH"))
            output_yoda = os.path.abspath(output_yoda)
            if not os.path.exists(output_yoda):
                raise IOError("Could not find output file {}!".format(output_yoda))
            output.copy_from_local(output_yoda)
            os.remove(output_yoda)
        except RuntimeError as e:
            output.remove()
            raise e

        print("-------------------------------------------------------")
