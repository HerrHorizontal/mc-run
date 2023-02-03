
from luigi.util import inherits
import os

from subprocess import PIPE
from generation.framework.utils import run_command, herwig_env

from generation.framework.tasks import Task, CommonConfig

from HerwigIntegrate import HerwigIntegrate
from HerwigBuild import HerwigBuild


@inherits(CommonConfig)
class HerwigMerge(Task):
    """
    Merge grid files from subprocess 'Herwig integrate' generation and complete Herwig-cache 
    """

    exclude_params_req = {
        "source_script"
    }


    def requires(self):
        t = HerwigIntegrate.req(self)
        return {
            'HerwigIntegrate': t,
            'HerwigBuild': HerwigBuild.req(t)
        }


    def output(self):
        return self.remote_target("Herwig-cache.tar.gz")


    def run(self):
        # data
        input_file = str(self.input_file_name)

        # ensure that the output directory exists
        output = self.output()
        output.parent.touch()

        # actual payload:
        print("=======================================================")
        print("Starting merge step to finish Herwig-cache and run file")
        print("=======================================================")

        # download the packed files from grid and unpack
        with self.input()['HerwigBuild'].localize('r') as _file:
            os.system('tar -xzf {}'.format(_file.path))

        for branch, target in self.input()['HerwigIntegrate']["collection"].targets.items():
            if branch <=10:
                print('Getting Herwig integration file: {}'.format(target))
            with target.localize('r') as _file:
                os.system('tar -xzf {}'.format(_file.path))

        # run Herwig build step 
        _herwig_exec = ["Herwig", "mergegrids"]
        _herwig_args = [
            "{INPUT_FILE_NAME}.run".format(INPUT_FILE_NAME=input_file)
        ]

        print('Executable: {}'.format(" ".join(_herwig_exec + _herwig_args)))

        try:
            run_command(_herwig_exec + _herwig_args, env=herwig_env, cwd=os.path.expandvars("$ANALYSIS_PATH"))
        except RuntimeError as e:
            output.remove()
            raise e

        output_file = os.path.abspath(os.path.expandvars("$ANALYSIS_PATH/Herwig-cache.tar.gz"))
        run_file = os.path.abspath("{INPUT_FILE_NAME}.run".format(INPUT_FILE_NAME=input_file))
        os.system('tar -czf {OUTPUT_FILE} Herwig-cache {RUN_FILE}'.format(
            OUTPUT_FILE=output_file,
            RUN_FILE=os.path.relpath(run_file)
        ))
        if os.path.exists(output_file):
            output.copy_from_local(output_file)
            os.remove(output_file)
            os.remove(run_file)
        else:
            raise IOError("Output file '{}' doesn't exist! Abort!".format(output_file))

        print("=======================================================")
        
