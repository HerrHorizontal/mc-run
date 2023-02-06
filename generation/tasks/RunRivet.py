

import law
import luigi
from luigi.util import inherits
import os
import random
import glob

from subprocess import PIPE
from generation.framework.utils import run_command

from law.contrib.htcondor.job import HTCondorJobManager
from generation.framework.tasks import Task, HTCondorWorkflow, GenerationScenarioConfig

from HerwigRun import HerwigRun


@inherits(GenerationScenarioConfig)
class RunRivet(Task, HTCondorWorkflow):
    """
    Analyze generated HEPMC files with Rivet and create YODA files
    """

    # allow outputs in nested directory structure
    output_collection_cls = law.NestedSiblingFileCollection

    # configuration variables
    files_per_job = luigi.IntParameter(
        default=10,
        description="Number of HepMC files analyzed per Rivet job. \
                Rivet is very fast analyzing HepMC files, so a sufficient high number should be given. \
                At the same time don't overdo it, since the files might be quite large and fill the scratch space."
    ) # from RunRivet
    rivet_analyses = luigi.ListParameter(
        default=["MC_XS","MC_WEIGHTS"],
        description="List of IDs of Rivet analyses to run."
    )

    exclude_params_req = {
        "rivet_analyses",
        "files_per_job",
        "bootstrap_file", 
        "htcondor_walltime", "htcondor_request_memory", 
        "htcondor_requirements", "htcondor_request_disk"
    }


    def workflow_requires(self):
        reqs = super(RunRivet, self).workflow_requires()
        # analyzing requires successfully generated events
        # require the parent workflow and inform it about the branches to produce by passing
        # the "branches" parameter and simultaneously preventing {start,end}_branch being used
        branches = sum(self.branch_map.values(), [])
        reqs["HerwigRun"] = HerwigRun.req(
            self, 
            branches=branches,
            _exclude=[
                "start_branch", "end_branch",
                "bootstrap_file", 
                "htcondor_walltime", "htcondor_request_memory", 
                "htcondor_requirements", "htcondor_request_disk"
                ]
            )
        return reqs


    def create_branch_map(self):
        # each analysis job analyzes a chunk of HepMC files  
        branch_chunks = HerwigRun.req(self).get_all_branch_chunks(self.files_per_job)
        # one by one job to inputfile matching
        return {
            jobnum: branch_chunk 
            for jobnum, branch_chunk in enumerate(branch_chunks) 
        }


    def requires(self):
        # each branch task requires existent HEPMC files to analyze
        req = dict()
        req["HerwigRun"] = [
                HerwigRun.req(self, branch=b)
                for b in self.branch_data
            ]
        return req


    def remote_path(self, *path):
        parts = (self.__class__.__name__,self.input_file_name, self.mc_setting, ) + path
        return os.path.join(*parts)


    def output(self):
        # 
        dir_number = int(self.branch)/1000
        return self.remote_target("{DIR_NUMBER}/{INPUT_FILE_NAME}job{JOB_NUMBER}.yoda".format(
            DIR_NUMBER=str(dir_number),
            INPUT_FILE_NAME=str(self.input_file_name),
            JOB_NUMBER=str(self.branch)
            ))


    def run(self):
        # branch data
        _my_config = str(self.input_file_name)
        _rivet_analyses = list(self.rivet_analyses)

        # ensure that the output directory exists
        output = self.output()
        try:
            output.parent.touch()
        except IOError:
            print("Output target doesn't exist!")

        # actual payload:
        print("=======================================================")
        print("Running Rivet analyses on HEPMC files ")
        print("=======================================================")

        # set environment variables
        my_env = os.environ
        
        # identify and get the HEPMC files for analyzing
        print("Inputs: {}".format(self.input()))
        for target in self.input()['HerwigRun']:
            with target.localize('r') as input_file:
                os.system('tar -xvjf {}'.format(input_file.path))

        input_files = glob.glob('*.hepmc')
        output_file = "Rivet.yoda"

        # run Rivet analysis
        _rivet_exec = ["rivet"]
        _rivet_args = [
            "--analysis={RIVET_ANALYSIS}".format(RIVET_ANALYSIS=_rivet_analysis) for _rivet_analysis in _rivet_analyses
        ] + [
            "--histo-file={OUTPUT_NAME}".format(OUTPUT_NAME=output_file)
        ] + glob.glob('*.hepmc')

        print('Executable: {}'.format(" ".join(_rivet_exec + _rivet_args)))

        try:
            run_command(_rivet_exec + _rivet_args, env=my_env)
        except RuntimeError as e:
            output.remove()
            raise e

        _output_file = os.path.abspath(output_file)

        if os.path.exists(_output_file):
            output.copy_from_local(_output_file)
        else:
            raise IOError("Could not find output file {}!".format(_output_file))


        print("=======================================================")
