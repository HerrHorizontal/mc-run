import os
import random
import shutil
from subprocess import PIPE

import law
import luigi
from generation.framework.htcondor import HTCondorWorkflow
from generation.framework.tasks import GenerationScenarioConfig, GenRivetTask
from generation.framework.utils import identify_setupfile, run_command
from law.logger import get_logger
from luigi.util import inherits

from .HerwigMerge import HerwigMerge

logger = get_logger(__name__)


@inherits(GenerationScenarioConfig)
class HerwigRun(GenRivetTask, HTCondorWorkflow, law.LocalWorkflow):
    """
    Use the prepared grids in Herwig-cache to generate HEP particle collision \
    events
    """

    # allow outputs in nested directory structure
    output_collection_cls = law.NestedSiblingFileCollection

    # configuration variables
    mc_generator = "herwig"

    start_seed = luigi.IntParameter(
        default=42,
        description="Start seed for random generation of individual job seeds. Currently not used!",
    )
    number_of_jobs = luigi.IntParameter(
        default=1,
        description="Number of individual generation jobs. Each will generate statistically independent events.",
    )
    events_per_job = luigi.IntParameter(
        default=10000, description="Number of events generated in each job."
    )
    setupfile = luigi.Parameter(
        default="None",
        description="Overwrite setupfile to adjust Herwig parameters in the event generation. \
                Default setupfile will be chosen according to mc_setting. \
                Those parameters should not involve the hard process generation. \
                Setupfiles have to be stored in `inputfiles/setupfiles/`.",
    )

    exclude_params_req = {
        # "setupfile",
        # "number_of_jobs",
        "events_per_job",
        "start_seed",
        "htcondor_walltime",
        "htcondor_request_memory",
        "htcondor_requirements",
        "htcondor_request_disk",
    }
    exclude_params_req_get = {"bootstrap_file"}

    def workflow_requires(self):
        # integration requires successful build step
        mc_setting = self.mc_setting
        if self.mc_setting != "PSoff":
            mc_setting = None
        return {"HerwigMerge": HerwigMerge.req(self, mc_setting=mc_setting)}

    def create_branch_map(self):
        # create list of seeds
        seed_list = []
        if False:
            random.seed(self.startseed)
            for _jobnum in range(0, int(self.number_of_jobs)):
                seed_list.append(random.randint(1, int(9e9)))
        else:
            seed_list = range(int(self.number_of_jobs))
        # each run job is refrenced to a seed
        return {jobnum: seed for jobnum, seed in enumerate(seed_list)}

    def requires(self):
        # current branch task requires existing Herwig-cache and run-file
        mc_setting = self.mc_setting
        if self.mc_setting != "PSoff":
            mc_setting = None
        return {"HerwigMerge": HerwigMerge.req(self, mc_setting=mc_setting)}

    def remote_path(self, *path):
        parts = (
            self.__class__.__name__,
            self.campaign,
            self.mc_setting,
        ) + path
        return os.path.join(*parts)

    def output(self):
        #
        dir_number = int(self.branch) / 1000
        return self.remote_target(
            "{DIR_NUMBER}/{INPUT_FILE_NAME}job{JOB_NUMBER}.tar.bz2".format(
                DIR_NUMBER=int(dir_number),
                INPUT_FILE_NAME=str(self.campaign),
                JOB_NUMBER=str(self.branch),
            )
        )

    def run(self):
        # branch data
        _job_num = str(self.branch)
        _my_config = str(self.campaign)
        _num_events = str(self.events_per_job)
        seed = int(self.branch_data)

        # ensure that the output directory exists
        output = self.output()
        try:
            output.parent.touch()
        except IOError:
            logger.error("Output target doesn't exist!")

        # actual payload:
        print("=======================================================")
        print("Producing events ")
        print("=======================================================")

        # set environment variables
        my_env = os.environ

        # get the prepared Herwig-cache and runfiles and unpack them
        with self.input()["HerwigMerge"].localize("r") as _file:
            os.system("tar -xzf {}".format(_file.path))

        # run Herwig event generation
        _herwig_exec = ["Herwig", "run"]
        _herwig_args = [
            "-q",
            "--seed={SEED}".format(SEED=seed),
            "--numevents={NEVENTS}".format(NEVENTS=_num_events),
            "{INPUT_FILE_NAME}.run".format(INPUT_FILE_NAME=_my_config),
        ]

        # identify the setupfile if specified and copy it to working directory
        work_dir = os.getcwd()
        _setupfile_path = identify_setupfile(
            self.setupfile, self.mc_generator, self.mc_setting, work_dir
        )
        _setupfile_suffix = "-" + _setupfile_path
        _herwig_args.append("--setupfile={SETUPFILE}".format(SETUPFILE=_setupfile_path))

        logger.info("Executable: {}".format(" ".join(_herwig_exec + _herwig_args)))

        try:
            run_command(_herwig_exec + _herwig_args, env=my_env, cwd=work_dir)
            logger.info("Seed: {}".format(seed))
        except RuntimeError as e:
            output.remove()
            raise e

        output_file = "{INPUT_FILE_NAME}.tar.bz2".format(INPUT_FILE_NAME=_my_config)
        if int(seed) != 0:
            output_file_hepmc = (
                "{INPUT_FILE_NAME}-S{SEED}{SETUPFILE_SUFFIX}.hepmc".format(
                    INPUT_FILE_NAME=_my_config,
                    SEED=seed,
                    SETUPFILE_SUFFIX=_setupfile_suffix,
                )
            )
            output_file_yoda = (
                "{INPUT_FILE_NAME}-S{SEED}{SETUPFILE_SUFFIX}.yoda".format(
                    INPUT_FILE_NAME=_my_config,
                    SEED=seed,
                    SETUPFILE_SUFFIX=_setupfile_suffix,
                )
            )
        else:
            output_file_hepmc = "{INPUT_FILE_NAME}{SETUPFILE_SUFFIX}.hepmc".format(
                INPUT_FILE_NAME=_my_config, SETUPFILE_SUFFIX=_setupfile_suffix
            )
            output_file_yoda = "{INPUT_FILE_NAME}{SETUPFILE_SUFFIX}.yoda".format(
                INPUT_FILE_NAME=_my_config, SETUPFILE_SUFFIX=_setupfile_suffix
            )

        output_file_hepmc = os.path.abspath(output_file_hepmc)
        output_file_yoda = os.path.abspath(output_file_yoda)

        os.chdir(work_dir)

        if os.path.exists(output_file_hepmc):
            # tar and compress the output HepMC files to save disk space
            if os.path.exists(output_file_yoda):
                # also add already existing YODA files if existant
                os.system(
                    "tar -cvjf {OUTPUT_FILE} {HEPMC_FILE} {YODA_FILE}".format(
                        OUTPUT_FILE=output_file,
                        HEPMC_FILE=os.path.relpath(output_file_hepmc),
                        YODA_FILE=os.path.relpath(output_file_yoda),
                    )
                )
            else:
                os.system(
                    "tar -cvjf {OUTPUT_FILE} {HEPMC_FILE}".format(
                        OUTPUT_FILE=output_file,
                        HEPMC_FILE=os.path.relpath(output_file_hepmc),
                    )
                )
        else:
            os.system("ls -l")
            raise IOError(
                "HepMC file {} doesn't exist! Abort!".format(output_file_hepmc)
            )

        output_file = os.path.abspath(output_file)

        if os.path.exists(output_file):
            # copy the compressed outputs to save them
            output.copy_from_local(output_file)
        else:
            raise IOError("Output file '{}' doesn't exist! Abort!".format(output_file))

        print("=======================================================")
