

import law
import luigi
from luigi.util import inherits
import os, shutil
import random
import glob

from subprocess import PIPE
from generation.framework.utils import run_command, set_environment_variables

from generation.framework.tasks import GenRivetTask, GenerationScenarioConfig
from generation.framework.htcondor import HTCondorWorkflow

from .HerwigRun import HerwigRun
from .SherpaRun import SherpaRun
from .RivetBuild import RivetBuild

from law.logger import get_logger


logger = get_logger(__name__)


@inherits(GenerationScenarioConfig)
class RunRivet(GenRivetTask, HTCondorWorkflow, law.LocalWorkflow):
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
    mc_generator = luigi.Parameter(
        default="herwig",
        description="Name of the MC generator used for event generation."
    )

    # dummy parameter for run step
    number_of_gen_jobs = luigi.IntParameter()


    exclude_params_req = {
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
        if str(self.mc_generator).lower() == "herwig":
            reqs["MCRun"] = HerwigRun.req(
                self,
                number_of_jobs=self.number_of_gen_jobs,
                branches=branches,
                _exclude=[
                    "start_branch", "end_branch",
                    "bootstrap_file",
                    "htcondor_walltime", "htcondor_request_memory",
                    "htcondor_requirements", "htcondor_request_disk"
                    ]
                )
        elif str(self.mc_generator).lower() == "sherpa":
            reqs["MCRun"] = SherpaRun.req(
                self,
                number_of_jobs=self.number_of_gen_jobs,
                branches=branches,
                _exclude=[
                    "start_branch", "end_branch",
                    "bootstrap_file",
                    "htcondor_walltime", "htcondor_request_memory",
                    "htcondor_requirements", "htcondor_request_disk"
                    ]
                )
        else:
            raise ValueError("Unknown MC generator: {}".format(self.mc_generator))
        # also make sure the Rivet analyses exist
        reqs["analyses"] = RivetBuild.req(self)
        return reqs


    def create_branch_map(self):
        # each analysis job analyzes a chunk of HepMC files
        if str(self.mc_generator).lower() == "herwig":
            branch_chunks = HerwigRun.req(
                self,
                number_of_jobs=self.number_of_gen_jobs
            ).get_all_branch_chunks(self.files_per_job)
        elif str(self.mc_generator).lower() == "sherpa":
            branch_chunks = SherpaRun.req(
                self,
                number_of_jobs=self.number_of_gen_jobs
            ).get_all_branch_chunks(self.files_per_job)
        else:
            raise ValueError("Unknown MC generator: {}".format(self.mc_generator))
        # one by one job to inputfile matching
        return {
            jobnum: branch_chunk 
            for jobnum, branch_chunk in enumerate(branch_chunks)
        }


    def requires(self):
        # each branch task requires existent HEPMC files to analyze
        req = dict()
        if str(self.mc_generator).lower() == "herwig":
            req["MCRun"] = [
                    HerwigRun.req(
                        self,
                        number_of_jobs=self.number_of_gen_jobs,
                        branch=b
                    )
                    for b in self.branch_data
                ]
        elif str(self.mc_generator).lower() == "sherpa":
            req["MCRun"] = [
                    SherpaRun.req(
                        self,
                        number_of_jobs=self.number_of_gen_jobs,
                        branch=b
                    )
                    for b in self.branch_data
                ]
        # and all the Rivet analyses to be built
        req["analyses"] = RivetBuild.req(self, branch=-1)
        return req


    def remote_path(self, *path):
        parts = (self.__class__.__name__,str(self.mc_generator).lower(),self.campaign, self.mc_setting,) + path
        return os.path.join(*parts)


    def output(self):
        # 
        dir_number = int(self.branch)/1000
        return self.remote_target("{DIR_NUMBER}/{INPUT_FILE_NAME}job{JOB_NUMBER}.yoda".format(
            DIR_NUMBER=int(dir_number),
            INPUT_FILE_NAME=str(self.campaign),
            JOB_NUMBER=str(self.branch)
            ))


    def run(self):
        # branch data
        _rivet_analyses = list(self.rivet_analyses)

        # ensure that the output directory exists
        output = self.output()
        try:
            output.parent.touch()
        except IOError:
            logger.error("Output target doesn't exist!")

        # actual payload:
        print("=======================================================")
        print("Running Rivet analyses on HEPMC files ")
        print("=======================================================")

        # set environment variables
        my_env = set_environment_variables("$ANALYSIS_PATH/setup/setup_rivet.sh")
        dirname = os.path.expandvars("$ANALYSIS_PATH")
        my_env["RIVET_ANALYSIS_PATH"] = ":".join((dirname, my_env.get("RIVET_ANALYSIS_PATH","")))

        # identify and get the compiled Rivet analyses
        logger.info("Shared object Rivet files: {}".format(self.input()["analyses"]["collection"].targets.values()))
        for target in self.input()["analyses"]["collection"].targets.values():
            with target.localize('r') as so_file:
                so_file.copy_to_local(
                    os.path.join(dirname, str(os.path.basename(so_file.path)).split("_",1)[1])
                )

        # identify and get the HEPMC files for analyzing
        logger.info("Input events: {}".format(self.input()['MCRun']))
        for target in self.input()['MCRun']:
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
        ] + input_files

        logger.info('Executable: {}'.format(" ".join(_rivet_exec + _rivet_args)))
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
