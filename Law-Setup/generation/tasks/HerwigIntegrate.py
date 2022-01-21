

import law
import luigi
import os

from subprocess import PIPE
from law.util import interruptable_popen

from law.contrib.htcondor.job import HTCondorJobManager
from generation.framework import Task, HTCondorWorkflow

from HerwigBuild import HerwigBuild

class HerwigIntegrate(Task, HTCondorWorkflow):
    """
    Create jobwise integration grids from 'Herwig build' preparations gathered in the Herwig-cache directory
    using 'Herwig integrate' (and add them to a corresponding Herwig-cache directory)
    """

    # configuration variables
    input_file_name = luigi.Parameter()
    integration_maxjobs = luigi.Parameter() # number of prepared integration jobs

    exclude_params_req = {
        "bootstrap_file",
        "htcondor_walltime", "htcondor_request_memory", 
        "htcondor_requirements", "htcondor_request_disk"
    }

    def workflow_requires(self):
        # integration requires successful build step
        return {
            'HerwigBuild': HerwigBuild.req(self)
        }

    def create_branch_map(self):
        # each integration job is indexed by it's job number
        return {jobnum: intjobnum for jobnum, intjobnum in enumerate(range(int(self.integration_maxjobs)))}

    def requires(self):
        # current branch task requires existing integrationList
        return {
            'HerwigBuild': HerwigBuild.req(self)
        }
        
    def output(self):
        return self.remote_target("Herwig-int{}.tar.gz".format(self.branch))

    def run(self):
        
        # branch data
        _jobid = str(self.branch)
        _my_config = str(self.input_file_name)


        # ensure that the output directory exists
        output = self.output()
        output.parent.touch()
        

        # actual payload:
        print("=======================================================")
        print("Starting integration step to generate integration grids")
        print("=======================================================")

        # set environment variables
        my_env = os.environ

        # get the prepared Herwig-cache and runfiles and unpack them
        with self.input()['HerwigBuild'].localize('r') as _file:
            os.system('tar -xzf {}'.format(_file.path))

        # run Herwig integration
        _herwig_exec = ["Herwig", "integrate"]
        _herwig_args = [
            "--jobid={JOBID}".format(JOBID=_jobid),
            "{INPUT_FILE_NAME}.run".format(INPUT_FILE_NAME=_my_config)
        ]

        print('Executable: {}'.format(" ".join(_herwig_exec + _herwig_args)))

        code, out, error = interruptable_popen(
            _herwig_exec + _herwig_args,
            stdout=PIPE,
            stderr=PIPE,
            env=my_env
        )

        # if successful tar and save integration
        if(code != 0):
            raise Exception('Error: ' + error + 'Output: ' + out + '\nHerwig integrate returned non-zero exit status {}'.format(code))
        else:
            print('Output: ' + out)
            _output_file = "Herwig-cache/{INPUT_FILE_NAME}/integrationJob{JOBID}".format(
                JOBID=_jobid,
                INPUT_FILE_NAME=_my_config
            )

            if os.path.exists(os.path.join(_output_file,"HerwigGrids.xml")):
                os.system(
                    'tar -czf Herwig-int.tar.gz {OUTPUT_FILE}'.format(
                        OUTPUT_FILE=_output_file
                    )
                )
            else:
                raise Exception('Error: Grid file {} is not existent. Something went wrong in integration step! Abort!'.format(os.path.join(_output_file,"HerwigGrids.xml")))

            if os.path.exists("Herwig-int.tar.gz"):
                output.copy_from_local("Herwig-int.tar.gz")

        print("=======================================================")

        