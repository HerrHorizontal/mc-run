
import luigi
from luigi.util import inherits
import os

from subprocess import PIPE
from law.util import interruptable_popen

from generation.framework import Task, CommonConfig

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
    source_script = luigi.Parameter(
        significant=False,
        default=os.path.join("$ANALYSIS_PATH","setup","setup_rivet.sh"),
        description="Path to the source script providing the local Herwig environment to use."
    )
    match = luigi.Parameter(
        significant=False,
        default=None,
        description="Include analysis objects which name matches this regex."
    )
    unmatch = luigi.Parameter(
        significant=False,
        default=None,
        description="Exclude analysis objects which name matches this regex."
    )
    xlabel = luigi.Parameter(
        significant=False,
        default="Observable",
        description="Label to print for the x-axis of the plots"
    )
    ylabel = luigi.Parameter(
        significant=False,
        default="NP corr.",
        description="Label to print for the y-axis of the plots"
    )

    exclude_params_req = {
        "source_script",
        "mc_setting_full",
        "mc_setting_partial",
        "match",
        "unmatch",
        "xlabel",
        "ylabel"
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
        outputs = dict()
        outputs["yoda"] = self.remote_target(
            "{full}-{partial}-Ratio.yoda".format(
                full = self.mc_setting_full,
                partial = self.mc_setting_partial
            )
        )
        outputs["plots"] = self.remote_target(
            "{full}-{partial}-Ratio-Plots.tar.gz".format(
                full = self.mc_setting_full,
                partial = self.mc_setting_partial
            )
        )
        return outputs

    def run(self):
        # ensure that the output directory exists
        output = self.output()
        try:
            for o in output.values():
                o.parent.touch()
        except IOError:
            print("Output target doesn't exist!")

        # actual payload:
        print("=======================================================")
        print("Starting NP-factor calculation with YODA")
        print("=======================================================")

        # set environment variables
        my_env = self.set_environment_variables(source_script_path=self.source_script)

        # localize the separate YODA files on grid storage
        print("Inputs: {}".format(self.input()["full"]))
        with self.input()["full"].localize('r') as _file:
            print("full: {}".format(_file.path))
            input_yoda_file_full = _file.path
        with self.input()["partial"].localize('r') as _file:
            print("partial: {}".format(_file.path))
            input_yoda_file_partial = _file.path

        # assign paths for output YODA file and plots
        output_yoda = "{full}-{partial}-Ratio.yoda".format(
            full = self.mc_setting_full,
            partial = self.mc_setting_partial
        )
        plot_dir = os.path.abspath("plots-{full}-{partial}".format(
            full=self.mc_setting_full,
            partial = self.mc_setting_partial
        ))

        # execute the script deriving the NP correction plots and files
        executable = [
            "python", os.path.expandvars("$ANALYSIS_PATH/scripts/yodaDeriveNPCorr.py"),
            "--full", "{}".format(input_yoda_file_full),
            "--partial", "{}".format(input_yoda_file_partial),
            "--output-file", "{}".format(output_yoda),
            "--plot-dir", "{}".format(plot_dir)
        ]
        executable += ["--match", self.match] if self.match else []
        executable += ["--unmatch", self.unmatch] if self.unmatch else []
        executable += ["--xlabel", self.xlabel] if self.xlabel else []
        executable += ["--ylabel", self.ylabel] if self.ylabel else []

        print("Executable: {}".format(" ".join(executable)))

        code, out, error = interruptable_popen(
            executable,
            stdout=PIPE,
            stderr=PIPE,
            env=my_env
        )

        # if successful return merged YODA file and plots
        if(code != 0):
            raise Exception('Error:\n' + error + '\nOutput:\n' + out + '\nYodaNPCorr returned non-zero exit status {}'.format(code))
        else:
            print('Output:\n' + out)

        output_yoda = os.path.abspath(output_yoda)

        if not os.path.exists(output_yoda):
            raise FileNotFoundError("Could not find output file {}!".format(output_yoda))

        output["yoda"].copy_from_local(output_yoda)
        os.system('rm {OUTPUT_FILE}'.format(
            OUTPUT_FILE=output_yoda
        ))
        
        if not os.listdir(plot_dir):
            raise LookupError("Plot directory {} is empty!".format(plot_dir))

        output["plots"].dump(plot_dir)
        os.system('rm -r {OUTPUT_DIR}'.format(
            OUTPUT_DIR=plot_dir
        ))

        print("-------------------------------------------------------")