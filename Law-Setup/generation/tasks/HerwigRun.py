

import law
import luigi
import os
import random

from subprocess import PIPE
from law.util import interruptable_popen

from law.contrib.htcondor.job import HTCondorJobManager
from generation.framework import Task, HTCondorWorkflow

from HerwigMerge import HerwigMerge

class HerwigRun(Task, HTCondorWorkflow):
    """
    Use the prepared grids in Herwig-cache to generate HEP particle collision events
    """

    # configuration variables
    input_file_name = luigi.Parameter()
    start_seed = luigi.Parameter()
    number_of_jobs = luigi.Parameter()
    events_per_job = luigi.Parameter()

    def workflow_requires(self):
        # integration requires successful build step
        return {
            'HerwigMerge': HerwigMerge()
        }

    def create_branch_map(self):
        # create list of seeds
        _seed_list = []
        if(False):
            random.seed(self.start_seed)
            for jobnum in range(0, int(self.number_of_jobs)):
                _seed_list.append(random.randint(1,int(9e9)))
        else:
            _seed_list = range(int(self.number_of_jobs))
        # each run job is refrenced to a seed
        return {jobnum: seed for jobnum, seed in enumerate(_seed_list)}

    def requires(self):
        # current branch task requires existing Herwig-cache and run-file
        return {
            'HerwigMerge': HerwigMerge()
        }
        
    def output(self):
        # 
        return self.remote_target("{INPUT_FILE_NAME}job{JOB_NUMBER}.hepmc".format(
            INPUT_FILE_NAME=str(self.input_file_name),
            JOB_NUMBER=str(self.branch)
            ))

    def run(self):
        
        # branch data
        _job_num = str(self.branch)
        _my_config = str(self.input_file_name)
        _num_events = str(self.events_per_job)
        _seed = str(self.branch_data)


        # ensure that the output directory exists
        output = self.output()
        output.parent.touch()


        # actual payload:
        print("=======================================================")
        print("Producing events ")
        print("=======================================================")

        # set environment variables
        my_env = os.environ

        # get the prepared Herwig-cache and runfiles and unpack them
        with self.input()['HerwigMerge'].localize('r') as _file:
            os.system('tar -xzf {}'.format(_file.path))


        # run Herwig integration
        _herwig_exec = ["Herwig", "run"]
        _herwig_args = [
            "-q", 
            "--seed={SEED}".format(SEED=_seed),
            "--numevents={NEVENTS}".format(NEVENTS=_num_events),
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
            raise Exception('Error: ' + error + 'Output: ' + out + '\nHerwig run returned non-zero exit status {}'.format(code))
        else:
            print('Output: ' + out)

            _output_file = "{INPUT_FILE_NAME}-S{SEED}.hepmc".format(
                    INPUT_FILE_NAME=_my_config,
                    SEED=_seed)

            if os.path.exists(_output_file):
                output.copy_from_local(_output_file)


        print("=======================================================")

