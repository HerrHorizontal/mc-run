
import law
import luigi
import os

from subprocess import PIPE
from law.util import interruptable_popen

from generation.framework import Task

from ConvertYodaToRoot import ConvertYodaToRoot


class PalisadeNPCorr(Task, law.LocalWorkflow):
    """
    plotting class for NP-correction factor plots with Palisade
    """

    # configuration variables
    input_file_names = luigi.ListParameter(default=[])
    mc_setting_full = luigi.Parameter(default="withNP")
    mc_setting_NPoff = luigi.Parameter(default="NPoff")

    mc_setting_pairs = [mc_setting_full, mc_setting_NPoff]

    exclude_params_req = {
        "bootstrap_file"
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
                    "setup_karma.sh"
                    )
                ),
            shell=True,
            stdout=PIPE,
            stderr=PIPE
        )
        my_env = self.convert_env_to_dict(out)
        return my_env

    def create_branch_map(self):
        pass

    def workflow_requires(self):
        pass

    def requires(self):
        pass

    def output(self):
        pass

    def run(self):
        pass
