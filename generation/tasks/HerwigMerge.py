

import law
import luigi
import os

from subprocess import PIPE
from law.util import interruptable_popen

from generation.framework import Task

from HerwigIntegrate import HerwigIntegrate
from HerwigBuild import HerwigBuild


class HerwigMerge(Task):
    """
    Merge grid files from subprocess 'Herwig integrate' generation and complete Herwig-cache 
    """

    # configuration variables
    input_file_name = luigi.Parameter()

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
        code, out, error = interruptable_popen("source {}; env".format(os.path.join("$ANALYSIS_PATH","setup","setup_herwig.sh")),
                                               shell=True, 
                                               stdout=PIPE, 
                                               stderr=PIPE
                                               )
        my_env = self.convert_env_to_dict(out)
        return my_env

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
        _my_input_file_name = str(self.input_file_name)

        # ensure that the output directory exists
        output = self.output()
        output.parent.touch()


        # actual payload:
        print("=======================================================")
        print("Starting merge step to finish Herwig-cache and run file")
        print("=======================================================")

        # set environment variables
        my_env = self.set_environment_variables()

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
            "{INPUT_FILE_NAME}.run".format(INPUT_FILE_NAME=_my_input_file_name)
        ]

        print('Executable: {}'.format(" ".join(_herwig_exec + _herwig_args)))

        code, out, error = interruptable_popen(
            _herwig_exec + _herwig_args,
            stdout=PIPE,
            stderr=PIPE,
            env=my_env
        )

        # if successful save final Herwig-cache and run-file as tar.gz
        if(code != 0):
            raise Exception('Error: ' + error + 'Output: ' + out + '\nHerwig mergegrids returned non-zero exit status {}'.format(code))
        else:
            print('Output: ' + out)

            output_file = "Herwig-cache.tar.gz"

            os.system('tar -czf {OUTPUT_FILE} Herwig-cache {INPUT_FILE_NAME}.run'.format(
                OUTPUT_FILE=output_file,
                INPUT_FILE_NAME=_my_input_file_name
            ))

            if os.path.exists(output_file):
                output.copy_from_local(output_file)
                os.system('rm Herwig-cache.tar.gz {INPUT_FILE_NAME}.run'.format(
                    INPUT_FILE_NAME=_my_input_file_name
                ))
            else:
                raise Exception("Output file '{}' doesn't exist! Abort!".format(output_file))

        print("=======================================================")
        
