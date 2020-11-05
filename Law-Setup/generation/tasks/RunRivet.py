

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
    number_of_jobs = luigi.Parameter() # from HerwigRun
    files_per_job = luigi.Parameter() # from RunRivet
    rivet_analyses = luigi.ListParameter()

    def get_incr_filelist(self):

        incr_filenumber_list = list(range(int(self.number_of_jobs))[::int(self.files_per_job)])

        # remaining number of files not matched to job
        _remaining_files = int(self.number_of_jobs)%int(self.files_per_job)
        # if some files are not matched to a job, add them
        if _remaining_files != 0:
            incr_filenumber_list.append(int(self.number_of_jobs))
        
        return incr_filenumber_list


    def workflow_requires(self):
        # analyzing requires successfully generated events
        return HerwigRun.req(self)

    def create_branch_map(self):
        # each analysis job is indexed by the according number of HEPMC files to analyze                
        return dict(enumerate(self.get_incr_filelist()[:-1]))

    def requires(self):
        # each branch task requires existent HEPMC files to analyze
        return HerwigRun.req(self, branches=range(self.get_incr_filelist()[self.branch],self.get_incr_filelist()[self.branch+1]))

    def output(self):
        # 
        return self.remote_target("{INPUT_FILE_NAME}job{JOB_NUMBER}.yoda".format(
            INPUT_FILE_NAME=str(self.input_file_name),
            JOB_NUMBER=str(self.branch)
            ))

    def run(self):

        # branch data
        _my_config = str(self.input_file_name)
        _rivet_analyses = list(self.rivet_analyses)


        # ensure that the output directory exists
        output = self.output()
        output.parent.touch()


        # actual payload:
        print("=======================================================")
        print("Running Rivet analyses on HEPMC files ")
        print("=======================================================")

        # set environment variables
        my_env = os.environ
        
        # identify and get the HEPMC files for analyzing
        inputfile_list = []
        for branch, target in self.input()['HerwigRun']["collection"].targets.items():
            inputfile_list.append(target.localize('r').path)

        # run Rivet analysis
        _rivet_exec = ["rivet"]
        _rivet_args = [
            "-a {RIVET_ANALYSES}".format(RIVET_ANALYSES=" -a ".join(_rivet_analyses)),
            "-o {OUTPUT_NAME}".format(OUTPUT_NAME="Rivet.yoda"),
            "{HEPMC_FILES}".format(HEPMC_FILES=" ".join(inputfile_list))
        ]

        print('Executable: {}'.format(" ".join(_rivet_exec + _rivet_args)))

        code, out, error = interruptable_popen(
            _rivet_exec + _rivet_args,
            stdout=PIPE,
            stderr=PIPE,
            env=my_env
        )

        # if successful save YODA output
        if(code != 0):
            raise Exception('Error: ' + error + 'Output: ' + out + '\nRivet returned non-zero exit status {}'.format(code))
        else:
            print('Output: ' + out)

            _output_file = "Rivet.yoda"

            if os.path.exists(_output_file):
                output.copy_from_local(_output_file)


        print("=======================================================")
