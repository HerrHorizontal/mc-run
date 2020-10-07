

import law
import luigi
import os
from termcolor import colored

from subprocess import PIPE
from law.util import interruptable_popen

from generation.framework import Task

from HerwigIntegrate import HerwigIntegrate
from HerwigBuild import HerwigBuild


class HerwigMerge(Task, law.LocalWorkflow):
    """
    Merge grid files from subprocess 'Herwig integrate' generation and complete Herwig-cache 
    """

    # configuration variables
    integration_maxjobs = luigi.Parameter() # number of prepared integration directories
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
        code, out, error = interruptable_popen("source {}; env".format(os.path.join(os.path.dirname(__file__),"..","..","..","setup","setup_herwig.sh")),
                                               shell=True, 
                                               stdout=PIPE, 
                                               stderr=PIPE
                                               )
        my_env = self.convert_env_to_dict(out)
        return my_env

    def requires(self):
        return {
            'HerwigIntegrate': HerwigIntegrate(),
            'HerwigBuild': HerwigBuild()
        }
    
    def output(self):
        return self.local_target("Herwig-cache.tar.gz")

    def run(self):
        # data
        _my_input_file_name = str(self.input_file_name)
        _max_integration_jobs = str(self.integration_maxjobs)

        # ensure that the output directory exists
        output = self.output()
        output.parent.touch()


        # actual payload:
        print(colored("=======================================================", 'green'))
        print(colored("Starting merge step to finish Herwig-cache and run file", 'green'))
        print(colored("=======================================================", 'green'))

        # set environment variables
        my_env = self.set_environment_variables()

        # download the packed files from grid and unpack
        with self.input()['HerwigBuild'].localize('r') as _file:
            os.system('tar -xzf {}'.format(_file.path))

        for branch in self.input()['HerwigIntegrate']["collection"].targets:
            with branch.localize('r') as _file:
                os.system('tar -xzf {}'.format(_file.path))

        # run Herwig build step 
        _herwig_exec = ["Herwig", "mergegrids"]
        _herwig_args = [
            "{INPUT_FILE_NAME}.run ".format(INPUT_FILE_NAME=_my_input_file_name)
        ]

        print(colored('Executable: {}'.format(" ".join(_herwig_exec + _herwig_args)), 'yellow'))

        code, out, error = interruptable_popen(
            _herwig_exec + _herwig_args,
            stdout=PIPE,
            stderr=PIPE,
            env=my_env
        )

        # if successful save final Herwig-cache and run-file as tar.gz
        if(code != 0):
            raise Exception(colored('Error: ' + error + 'Output: ' + out + '\nHerwig mergegrids returned non-zero exit status {}'.format(code), 'red'))
        else:
            print(colored('Output: ' + out, 'yellow'))
            os.system('tar -czvf Herwig-cache.tar.gz Herwig-cache {INPUT_FILE_NAME}.run'.format(INPUT_FILE_NAME=_my_input_file_name))

            if os.path.exists("Herwig-cache.tar.gz"):
                output.copy_from_local("Herwig-cache.tar.gz")

        print(colored("=======================================================", 'green'))
        
