

import law
import luigi
import os
import random
import glob

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
        """
        # Method to identify the HepMC inputfile splitting.
        # It returns a list of file identifiers (int), which define the lower and upper borders 
        # of the filelist for all branch tasks.
        """
        _files_per_job = int(self.files_per_job)
        _number_of_jobs = int(self.number_of_jobs)
        # remaining number of files not matched to job
        # _remaining_files = _number_of_jobs % _files_per_job

        incr_filenumber_list = list(range(_number_of_jobs)[::_files_per_job])
        # add the total number of jobs as right border
        incr_filenumber_list.append(int(self.number_of_jobs))

        #print("Incremental file number list: {}".format(incr_filenumber_list))
        
        return incr_filenumber_list


    def workflow_requires(self):
        # analyzing requires successfully generated events
        return {
            #"HerwigRun": HerwigRun.req(self, branches=range(self.get_incr_filelist()[self.branch],self.get_incr_filelist()[self.branch+1]))
            "HerwigRun": HerwigRun.req(self,branch=self.branch)
        }

    def create_branch_map(self):
        # each analysis job is indexed by the according number of HEPMC files to analyze  
        # print("Branch map: {}".format(dict(enumerate(self.get_incr_filelist()[:-1]))))              
        # return {
        #     i: fileident for i, fileident in enumerate(self.get_incr_filelist()[:-1])
        # }

        # one by one job to inputfile matching
        return {
            jobnum: intjobnum for jobnum, intjobnum in enumerate(range(int(self.number_of_jobs))) 
        }

    def requires(self):
        # each branch task requires existent HEPMC files to analyze
        # print("Branches: {}".format(range(self.get_incr_filelist()[self.branch],self.get_incr_filelist()[self.branch+1])))
        # print(dir(self))
        # print("Requirements start/end: {}".format(HerwigRun.req(self, start_branch=self.get_incr_filelist()[self.branch], end_branch=self.get_incr_filelist()[self.branch+1]-1)))
        # print("Requirements 1,2,5: {}".format(HerwigRun.req(self, branches="1,2,5")))
        # return [
        #     HerwigRun.req(self, branch=_branch) for _branch in range(self.get_incr_filelist()[self.branch], self.get_incr_filelist()[self.branch+1])
        # ]
        return {
            "HerwigRun": HerwigRun.req(self,branch=self.branch)
        }

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
        print("Inputs: {}".format(self.input()))
        # for target in self.input()['HerwigRun']:
        #     with target.localize('r') as input_file:
        #         os.system('tar -xvjf {}'.format(input_file.path))
        with self.input()['HerwigRun'].localize('r') as input_file:
            os.system('tar -xvjf {}'.format(input_file.path))

        input_files = glob.glob('*.hepmc')

        # run Rivet analysis
        _rivet_exec = ["rivet"]
        _rivet_args = [
            "--analysis={RIVET_ANALYSIS}".format(RIVET_ANALYSIS=_rivet_analysis) for _rivet_analysis in _rivet_analyses
        ] + [
            "--histo-file={OUTPUT_NAME}".format(OUTPUT_NAME="Rivet.yoda")
        ] + glob.glob('*.hepmc')

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
