
import law
import luigi
import os

from subprocess import PIPE
from law.util import interruptable_popen

from generation.framework import Task

# from ConvertYodaToRoot import ConvertYodaToRoot
from RivetMerge import RivetMerge


class YodaNPCorr(Task, law.LocalWorkflow):
    """
    Plotting class for NP-correction factor plots with YODA
    """

    # configuration variables
    input_file_name = luigi.Parameter()
    mc_setting_full = luigi.Parameter(default="withNP")
    mc_setting_partial = luigi.Parameter(default="NPoff")

    exclude_params_req = {
        "bootstrap_file",
        "mc_setting_full",
        "mc_setting_partial"
    }

    def convert_env_to_dict(self, env):
        my_env = {}
        for line in env.splitlines():
            if line.find(" ") < 0:
                try:
                    key, value = line.split("=", 1)
                    my_env[key] = value
                except ValueError:
                    pass
        return my_env

    def set_environment_variables(self):
        code, out, error = interruptable_popen(
            "source {}; env".format(
                os.path.join(
                    os.path.dirname(__file__),
                    "..", "..", "..",
                    "setup",
                    "setup_rivet.sh"
                    )
                ),
            shell=True,
            stdout=PIPE,
            stderr=PIPE
        )
        my_env = self.convert_env_to_dict(out)
        return my_env

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
            output.parent.touch()
        except IOError:
            print("Output target doesn't exist!")

        # actual payload:
        print("=======================================================")
        print("Starting NP-factor calculation with YODA")
        print("=======================================================")

        # set environment variables
        my_env = self.set_environment_variables()

        # localize the separate YODA files on grid storage
        input_yoda_file_full = self.input()["full"].load()
        input_yoda_file_partial = self.input()["partial"].load()

        output_yoda = "{full}-{partial}-Ratio.yoda".format(
            full = self.mc_setting_full,
            partial = self.mc_setting_partial
        )

        code, out, error = interruptable_popen(
            [
                "python", "$ANALYSIS_PATH/scripts/yoda_calc_NPcorr.py",
                "--full", "{}".format(input_yoda_file_full.path),
                "--partial", "{}".format(input_yoda_file_partial.path),
                "--output", "{}".format(output_yoda)
            ],
            stdout=PIPE,
            stderr=PIPE,
            env=my_env
        )

        # if successful return merged YODA file
        if(code != 0):
            raise Exception('Error:\n' + error + '\nOutput:\n' + out + '\nYodaNPCorr returned non-zero exit status {}'.format(code))
        else:
            print('Output:\n' + out)

        try:
            os.path.exists(output_yoda)
        except:
            print("Could not find output file {}!".format(output_yoda))

        output.copy_from_local(output_yoda)
        os.system('rm {OUTPUT_FILE}'.format(
            OUTPUT_FILE=output_yoda
        ))
        # TODO: add plot folder
        
        print("-------------------------------------------------------")
