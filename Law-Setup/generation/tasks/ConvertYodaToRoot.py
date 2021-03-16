

import law
import luigi
import os

from subprocess import PIPE
from law.util import interruptable_popen

from generation.framework import Task

from YodaMerge import YodaMerge

class ConvertYodaToRoot(Task, law.LocalWorkflow):
    """
    Convert Yoda files with YODA objects to ROOT files with Root objects
    """

    # configuration variables
    input_file_names = luigi.ListParameter(default=[])
    mc_setting_full = luigi.Parameter(default="withNP")
    mc_setting_NPoff = luigi.Parameter(default="NPoff")

    mc_setting_pairs = [mc_setting_full,mc_setting_NPoff]

    exclude_params_req = {
        "bootstrap_file"
    }


    def convert_env_to_dict(self, env):
        my_env = {}
        for line in env.splitlines():
            if line.find(" ") < 0 :
                try:
                    key, value = line.split("=", 1)
                    my_env[key] = value
                except ValueError:
                    pass
        return my_env


    def set_environment_variables(self):
        code, out, error = interruptable_popen("source {}; env".format(os.path.join(os.path.dirname(__file__),"..","..","..","setup","setup_rivet.sh")),
                                               shell=True, 
                                               stdout=PIPE, 
                                               stderr=PIPE
                                               )
        my_env = self.convert_env_to_dict(out)
        return my_env


    def create_branch_map(self):
        return {
            jobnum: {
                "mc_setting": mc_setting,
                "input_file_name": input_file_name
            }
            for jobnum, mc_setting, input_file_name in enumerate(itertools.product(self.mc_setting_pairs,self.input_file_names))
        }


    def workflow_requires(self):
        reqs = super(ConvertYodaToRoot, self).workflow_requires()
        reqs["YodaMerge"] = YodaMerge.req(self)
        return reqs


    def requires(self):
        req = dict()
        req["YodaMerge"] = YodaMerge.req(
            self,
            mc_setting = self.branch_data["mc_setting"],
            input_file_name = self.branch_data["input_file_name"]
        )
        return req


    def remote_path(self, *path):
        parts = (self.__class__.__name__, ) + path
        return os.path.join(*parts)


    def output(self):
        return self.remote_target(
            "{MC_SETTING}/{INPUT_FILE_NAME}.root".format(
                MC_SETTING = self.branch_data["mc_setting"],
                INPUT_FILE_NAME = self.branch_data["input_file_name"]
            )
        )


    def run(self):

        # ensure that the output directory exists
        output = self.output()
        try:
            output.parent.touch()
        except IOError:
            print("Output target doesn't exist!")

        # actual payload:
        print("=======================================================")
        print("Starting converting of YODA to ROOT files")
        print("=======================================================")

        # localize the separate YODA files on grid storage
        input_yoda_file = self.input()['YodaMerge'].load()

        code, out, error = interruptable_popen(
            ["yoda2root", "output.root", "{}".format(input_yoda_file.path)],
            stdout=PIPE,
            stderr=PIPE,
            env=my_env
        )

        output_root_file = "output.root"
        output.copy_from_local(output_root_file)
            

