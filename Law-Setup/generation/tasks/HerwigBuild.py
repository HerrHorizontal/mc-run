

import law
import luigi
import os
from termcolor import colored

from subprocess import PIPE
from law.util import interruptable_popen

from generation.framework import Task


class HerwigBuild(Task, law.LocalWorkflow):
    """
    Gather and compile all necessary libraries and prepare the integration lists 
    for the chosen Matchbox defined in the '[input_file_name].in' file 
    by running 'Herwig build', which will create the Herwig-cache directory 
    and the '[input_file_name].run' file
    """
    
    # configuration variables
    input_file_name = luigi.Parameter()
    mc_setting = luigi.Parameter()
    integration_maxjobs = luigi.Parameter()

    def output(self):
        return self.remote_target("Herwig-cache.tar.gz")

    def run(self):
        # data
        _my_input_file_name = str(self.input_file_name)
        _max_integration_jobs = str(self.integration_maxjobs)


        # ensure that the output directory exists
        output = self.output()
        output.parent.touch()


        # actual payload:
        print(colored("=========================================================", 'green'))
        print(colored("Starting build step to generate Herwig-cache and run file", 'green'))
        print(colored("=========================================================", 'green'))

        # set environment variables
        my_env = os.environ

        # run Herwig build step 
        _herwig_exec = "Herwig build"
        _herwig_args = "--maxjobs={MAXJOBS} " \
            "{INPUT_FILE_NAME}.in ".format(
            MAXJOBS=_max_integration_jobs,
            INPUT_FILE_NAME=_my_input_file_name
        )

        print(colored('Executable: {} {}'.format(_herwig_exec, _herwig_args).replace(' -', ' \\\n    -'), 'yellow'))

        code, out, error = interruptable_popen(
            " ".join([_herwig_exec, _herwig_args]),
            stdout=PIPE,
            stderr=PIPE,
            env=my_env
        )

        # if successful save tar and save Herwig-cache
        if(code != 0):
            raise Exception('Error: ' + error + 'Outpur: ' + out + '\nHerwig integrate returned non-zero exit status {}'.format(code))
        else:
            os.system('tar -czvf Herwig-int.tar.gz Herwig-cache')

            if output.exists():
                output.copy_from_local("Herwig-cache.tar.gz")
                output.copy_from_local("{INPUT_FILE_NAME}.run".format(INPUT_FILE_NAME=_my_input_file_name))




