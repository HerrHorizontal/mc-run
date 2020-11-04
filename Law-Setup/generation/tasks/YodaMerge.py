

import law
import luigi
import os

from subprocess import PIPE
from law.util import interruptable_popen

from generation.framework import Task

from RunRivet import RunRivet


class YodaMerge(Task):
    """
    Merge separate YODA files from Rivet analysis runs to a single YODA file 
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
        code, out, error = interruptable_popen("source {}; env".format(os.path.join(os.path.dirname(__file__),"..","..","..","setup","setup_rivet.sh")),
                                               shell=True, 
                                               stdout=PIPE, 
                                               stderr=PIPE
                                               )
        my_env = self.convert_env_to_dict(out)
        return my_env

    def requires(self):
        return {
            'RunRivet': RunRivet(),
        }
    
    def output(self):
        return self.remote_target("{INPUT_FILE_NAME}.yoda".format(INPUT_FILE_NAME=self.input_file_name))

    def run(self):
        # data
        _my_input_file_name = str(self.input_file_name)

        # ensure that the output directory exists
        output = self.output()
        output.parent.touch()


        # actual payload:
        print("=======================================================")
        print("Starting merging of YODA files")
        print("=======================================================")

        # set environment variables
        my_env = self.set_environment_variables()

        # localize the separate YODA files on grid storage
        inputfile_list = []
        for branch, target in self.input()['RunRivet']["collection"].targets.items():
            inputfile_list.append(target.localize('r').path)

        # merge the YODA files 
        _output_file = "{OUTPUT_FILE_NAME}.yoda".format(OUTPUT_FILE_NAME=_my_input_file_name)

        _rivet_exec = ["yodamerge"]
        _rivet_args = [
            "-o {OUTPUT_FILE}".format(OUTPUT_FILE=_output_file),
            "{YODA_FILES}".format(YODA_FILES=" ".join(inputfile_list))
        ]

        print('Executable: {}'.format(" ".join(_rivet_exec + _rivet_args)))

        code, out, error = interruptable_popen(
            _rivet_exec + _rivet_args,
            stdout=PIPE,
            stderr=PIPE,
            env=my_env
        )

        # if successful save final YODA file
        if(code != 0):
            raise Exception('Error: ' + error + 'Output: ' + out + '\nYodamerge returned non-zero exit status {}'.format(code))
        else:
            print('Output: ' + out)

            if os.path.exists(_output_file):
                output.copy_from_local(_output_file)
                os.system('rm {OUTPUT_FILE}'.format(
                    OUTPUT_FILE=_output_file
                ))

        print("=======================================================")
        
