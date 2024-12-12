import os
import random

import law
import luigi
from generation.framework.htcondor import HTCondorWorkflow
from generation.framework.tasks import GenerationScenarioConfig, GenRivetTask
from generation.framework.utils import run_command, set_environment_variables
from law.logger import get_logger
from luigi.util import inherits

from .SherpaIntegrate import SherpaIntegrate

logger = get_logger(__name__)


@inherits(GenerationScenarioConfig)
class SherpaRun(GenRivetTask, HTCondorWorkflow, law.LocalWorkflow):
    """
    Use the prepared grids in Herwig-cache to generate HEP particle collision \
    events
    """

    # allow outputs in nested directory structure
    output_collection_cls = law.NestedSiblingFileCollection

    # configuration variables
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

    exclude_params_req = HTCondorWorkflow.exclude_params_req | {
        "setupfile",
        # "number_of_jobs",
        "events_per_job",
        "start_seed",
    }

    def workflow_requires(self):
        # Each job requires the sherpa setup to be present
        return {
            "SherpaIntegrate": SherpaIntegrate.req(self, _exclude={"branch"}),
        }

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

    def remote_path(self, *path):
        parts = (self.__class__.__name__, self.campaign, self.mc_setting) + path
        return os.path.join(*parts)

    def output(self):
        dir_number = int(self.branch) / 1000
        return self.remote_target(
            "{DIR_NUMBER}/{INPUT_FILE_NAME}job{JOB_NUMBER}.tar.bz2".format(
                DIR_NUMBER=int(dir_number),
                INPUT_FILE_NAME=str(self.campaign),
                JOB_NUMBER=str(self.branch),
            )
        )

    def run(self):
        _my_config = str(self.campaign)
        _num_events = str(self.events_per_job)
        seed = int(self.branch_data)

        # ensure that the output directory exists
        output = self.output()
        output.parent.touch()

        # actual payload:
        print("=======================================================")
        print("Producing events with Sherpa")
        print("=======================================================")

        # set environment variables
        sherpa_env = set_environment_variables(
            os.path.expandvars("$ANALYSIS_PATH/setup/setup_sherpa.sh")
        )
        work_dir = os.getcwd()
        # get the prepared Sherpack and runfiles and unpack them
        with self.workflow_input()["SherpaIntegrate"].localize("r") as _file:
            os.system("tar -xzf {}".format(_file.path))

        # run Sherpa event generation
        out_name = "{}-{}-{}.hepmc".format(self.campaign, self.mc_setting, seed)
        _sherpa_exec = ["Sherpa"]
        _sherpa_args = [
            "-R {SEED}".format(SEED=seed),
            "-e {NEVENTS}".format(NEVENTS=_num_events),
            "EVENT_OUTPUT=HepMC3_GenEvent[{}]".format(out_name),
        ]

        if self.mc_setting == "withNP":
            _gen_opts = []
        elif self.mc_setting == "NPoff":
            _gen_opts = ["FRAGMENTATION=Off", "MI_HANDLER=None"]
        elif self.mc_setting == "Hadoff":
            _gen_opts = ["FRAGMENTATION=Off"]
        elif self.mc_setting == "MPIoff":
            _gen_opts = ["MI_HANDLER=None"]
        else:
            raise ValueError("Unknown mc_setting: {}".format(self.mc_setting))

        try:
            run_command(
                _sherpa_exec + _sherpa_args + _gen_opts, env=sherpa_env, cwd=work_dir
            )
            logger.info("Seed: {}".format(seed))
        except RuntimeError as e:
            output.remove()
            raise e

        os.chdir(work_dir)
        output_file_hepmc = os.path.abspath(
            os.path.join(work_dir, "{}".format(out_name))
        )
        output_file = "{INPUT_FILE_NAME}.tar.bz2".format(INPUT_FILE_NAME=_my_config)

        if os.path.exists(output_file_hepmc):
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
            os.system("ls -l")
            raise IOError("Output file '{}' doesn't exist! Abort!".format(output_file))

        print("=======================================================")
