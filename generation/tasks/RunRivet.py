import glob
import os

import law
import luigi
from generation.framework.htcondor import HTCondorWorkflow
from generation.framework.tasks import GenerationScenarioConfig, GenRivetTask
from generation.framework.utils import run_command, set_environment_variables
from law.logger import get_logger
from luigi.util import inherits

from .HerwigRun import HerwigRun
from .RivetBuild import RivetBuild
from .SherpaRun import SherpaRun

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
                At the same time don't overdo it, since the files might be quite large and fill the scratch space.",
    )  # from RunRivet
    rivet_analyses = luigi.ListParameter(
        default=["MC_XS", "MC_WEIGHTS"],
        description="List of IDs of Rivet analyses to run.",
    )
    mc_generator = luigi.Parameter(
        default="herwig",
        description="Name of the MC generator used for event generation.",
    )

    # dummy parameter for run step
    number_of_gen_jobs = luigi.IntParameter()

    exclude_params_req = HTCondorWorkflow.exclude_params_req | {
        "files_per_job",
    }

    def workflow_requires(self):
        # Every task requires the Rivet analyses to be compiled
        return {"analyses": RivetBuild.req(self, _exclude={"branch"})}

    def create_branch_map(self):
        # each analysis job analyzes a chunk of HepMC files
        if str(self.mc_generator).lower() == "herwig":
            return HerwigRun.req(
                self, number_of_jobs=self.number_of_gen_jobs
            ).get_all_branch_chunks(self.files_per_job)
        elif str(self.mc_generator).lower() == "sherpa":
            return SherpaRun.req(
                self, number_of_jobs=self.number_of_gen_jobs
            ).get_all_branch_chunks(self.files_per_job)
        raise ValueError("Unknown MC generator: {}".format(self.mc_generator))

    def requires(self):
        # each branch task requires existent HEPMC files to analyze
        if str(self.mc_generator).lower() == "herwig":
            return HerwigRun.req(
                self,
                number_of_jobs=self.number_of_gen_jobs,
                branch=-1,
                branches=self.branch_data,
            )
        elif str(self.mc_generator).lower() == "sherpa":
            return SherpaRun.req(
                self,
                number_of_jobs=self.number_of_gen_jobs,
                branch=-1,
                branches=self.branch_data,
            )
        raise NotImplementedError("Unknown MC generator: {}".format(self.mc_generator))

    def remote_path(self, *path):
        parts = (
            self.__class__.__name__,
            str(self.mc_generator).lower(),
            self.campaign,
            self.mc_setting,
        ) + path
        return os.path.join(*parts)

    def output(self):
        #
        dir_number = int(self.branch) / 1000
        return self.remote_target(
            "_".join(sorted(self.rivet_analyses)),
            "{DIR_NUMBER}/{INPUT_FILE_NAME}job{JOB_NUMBER}.yoda".format(
                DIR_NUMBER=int(dir_number),
                INPUT_FILE_NAME=str(self.campaign),
                JOB_NUMBER=str(self.branch),
            ),
        )

    def run(self):
        # branch data
        _map = {
            "Dijet_3_lowpt": "Dijet_3",
            "Dijet_3_highpt": "Dijet_3",
        }
        _rivet_analyses = list(self.rivet_analyses)
        _mapped_analyses = [
            _map.get(analysis, analysis) for analysis in _rivet_analyses
        ]

        # actual payload:
        print("=======================================================")
        print("Running Rivet analyses on HEPMC files ")
        print("=======================================================")

        # set environment variables
        tmp_dir = law.LocalDirectoryTarget(is_tmp=True)
        my_env = set_environment_variables("$ANALYSIS_PATH/setup/setup_rivet.sh")
        my_env["RIVET_ANALYSIS_PATH"] = ":".join(
            (tmp_dir.abspath, my_env.get("RIVET_ANALYSIS_PATH", ""))
        )

        # identify and get the compiled Rivet analyses
        logger.info(
            "Shared object Rivet files: {}".format(
                self.workflow_input()["analyses"]["collection"].targets.values()
            )
        )
        local_so_files = []
        for so_file in self.workflow_input()["analyses"]["collection"].iter_existing():
            local_path = os.path.join(tmp_dir.abspath, so_file.basename)
            so_file.copy_to_local(local_path)
            local_so_files.append(local_path)

        # identify and get the HEPMC files for analyzing
        logger.info("Input events: {}".format(self.input()["collection"]))
        for target in self.input()["collection"].iter_existing():
            with target.localize("r") as input_file:
                os.system(f"tar -xjf {input_file.abspath} -C {tmp_dir.abspath}/")

        input_files = glob.glob(f"{tmp_dir.abspath}/*.hepmc")
        output_file = law.LocalFileTarget(is_tmp="yoda")

        # run Rivet analysis
        _rivet_exec = ["rivet"]
        _rivet_args = (
            [
                "--analysis={RIVET_ANALYSIS}".format(RIVET_ANALYSIS=_rivet_analysis)
                for _rivet_analysis in _mapped_analyses
            ]
            + [f"--histo-file={output_file.abspath}"]
            + input_files
        )

        logger.info("Executable: {}".format(" ".join(_rivet_exec + _rivet_args)))
        run_command(_rivet_exec + _rivet_args, env=my_env, cwd=tmp_dir.abspath)

        self.output().move_from_local(output_file)

        print("=======================================================")
