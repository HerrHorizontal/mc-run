

import law
import luigi
import os
from termcolor import colored

from subprocess import PIPE
from law.util import interruptable_popen

from generation.framework import Task


class HerwigBuild(Task):
    """
    Gather and compile all necessary libraries and prepare the integration lists 
    for the chosen Matchbox defined in the '[input_file_name].in' file 
    by running 'Herwig build', which will create the Herwig-cache directory 
    and the '[input_file_name].run' file
    """
    
    # configuration variables
    input_file_name = luigi.Parameter()
    integration_maxjobs = luigi.Parameter()
    config_path = luigi.Parameter()

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
        code, out, error = interruptable_popen("source {}; env".format(os.path.join(__file__,"..","setup_herwig.sh")),
                                               shell=True, 
                                               stdout=PIPE, 
                                               stderr=PIPE
                                               )
        my_env = self.convert_env_to_dict(out)
        return my_env

    def output(self):
        return self.remote_target("Herwig-build.tar.gz")

    def run(self):
        # data
        _my_input_file = os.path.join(__file__, "..", "..", "{}.in".format(self.input_file_name))
        _my_input_file_name = str(self.input_file_name)
        _max_integration_jobs = str(self.integration_maxjobs)
        _config_path = str(self.config_path)


        # ensure that the output directory exists
        output = self.output()
        output.parent.touch()


        # actual payload:
        print(colored("=========================================================", 'green'))
        print(colored("Starting build step to generate Herwig-cache and run file", 'green'))
        print(colored("=========================================================", 'green'))

        # set environment variables
        my_env = self.set_environment_variables()

        # run Herwig build step 
        _herwig_exec = "Herwig build"
        _herwig_args = "--maxjobs={MAXJOBS} " \
            "{INPUT_FILE} ".format(
            MAXJOBS=_max_integration_jobs,
            INPUT_FILE=_my_input_file
        )

        print(colored('Executable: {} {}'.format(_herwig_exec, _herwig_args).replace(' -', ' \\\n    -'), 'yellow'))

        code, out, error = interruptable_popen(
            " ".join([_herwig_exec, _herwig_args]),
            stdout=PIPE,
            stderr=PIPE,
            env=my_env
        )

        # if successful save Herwig-cache and run-file as tar.gz
        if(code != 0):
            raise Exception('Error: ' + error + 'Outpur: ' + out + '\nHerwig integrate returned non-zero exit status {}'.format(code))
        else:
            os.system('tar -czf Herwig-build.tar.gz Herwig-cache {INPUT_FILE_NAME}.run'.format(INPUT_FILE_NAME=_my_input_file_name))

            if os.path.exists("Herwig-build.tar.gz"):
                output.copy_from_local("Herwig-build.tar.gz")

