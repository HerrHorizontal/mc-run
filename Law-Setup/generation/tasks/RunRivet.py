

import law
import luigi
import os
import random

from subprocess import PIPE
from law.util import interruptable_popen

from law.contrib.htcondor.job import HTCondorJobManager
from generation.framework import Task, HTCondorWorkflow

from HerwigRun import HerwigRun

class RunRivet(Task, HTCondorWorkflow):
    """
    Analyze generated HEPMC files with Rivet and create YODA files
    """

    # configuration variables
    input_file_name = luigi.Parameter()
    number_of_jobs = luigi.Parameter()


    def workflow_requires(self):
        # analyzing requires successfully generated events
        return {
            'HerwigRun': HerwigRun()
        }

    def create_branch_map(self):
        # each analysis job is indexed by the according number of generated HEPMC files
        
        return {
            jobnum: intjobnum for jobnum, intjobnum in enumerate(range(int(self.number_of_jobs)))
        }

    def requires(self):
        # each branch task requires existent HEPMC files to analyze
        return HerwigRun.req(self)

    def output(self):
        # 
        return self.remote_target("{INPUT_FILE_NAME}job{JOB_NUMBER}.yoda".format(
            INPUT_FILE_NAME=str(self.input_file_name),
            JOB_NUMBER=str(self.branch)
            ))

    def run(self):

        # branch data

