import glob
import os
import re

import law
import luigi
from generation.framework.hepmc import convert_hepmc
from generation.framework.htcondor import HTCondorWorkflow
from generation.framework.storage import human_size, store_verified
from generation.framework.tasks import (
    GenerationScenarioConfig,
    GenRivetTask,
    HepMCConverterJobMixin,
)
from generation.framework.utils import run_command
from law.logger import get_logger
from luigi.util import inherits

from .HerwigRun import HerwigRun
from .SherpaRun import SherpaRun

logger = get_logger(__name__)


@inherits(GenerationScenarioConfig)
class ConvertHepMC(
    HepMCConverterJobMixin, GenRivetTask, HTCondorWorkflow, law.LocalWorkflow
):
    """
    Convert `tar.bz2` outputs of HerwigRun/SherpaRun from older MC-Run versions into HepMC3 \
    ROOT files, stored where the generator task expects them with `--hepmc-format root`. The \
    `tar.bz2` file is removed once the ROOT file is stored and verified.
    """

    # allow outputs in nested directory structure
    output_collection_cls = law.NestedSiblingFileCollection

    # configuration variables
    mc_generator = luigi.Parameter(
        default="herwig",
        description="Name of the MC generator used for event generation.",
    )
    number_of_gen_jobs = luigi.IntParameter(
        description="Number of jobs of the generator workflow whose outputs are converted.",
    )
    ConfigParser = luigi.configuration.cfg_parser.LuigiConfigParser.instance()
    root_compression = luigi.IntParameter(
        default=ConfigParser.getint("HepMCOutput", "root_compression", 209),
        significant=False,
        description="ROOT compression setting (100 * algorithm + level), 209 is LZMA 9.",
    )
    remove_input = luigi.BoolParameter(
        default=True,
        significant=False,
        description="Remove the original `tar.bz2` file after the ROOT file was stored and verified.",
    )

    def generator_task(self, **kwargs):
        generators = {"herwig": HerwigRun, "sherpa": SherpaRun}
        generator = str(self.mc_generator).lower()
        if generator not in generators:
            raise ValueError("Unknown MC generator: {}".format(self.mc_generator))
        return generators[generator].req(
            self, number_of_jobs=self.number_of_gen_jobs, **kwargs
        )

    def generator_workflow(self):
        # create the generator workflow only once and share it with all branches of this workflow
        workflow = self.as_workflow()
        if getattr(workflow, "_generator_workflow", None) is None:
            workflow._generator_workflow = workflow.generator_task()
        return workflow._generator_workflow

    def create_branch_map(self):
        # inside a remote job, only its own branch is needed, so skip listing the storage
        if os.getenv("LAW_JOB_INIT_DIR"):
            return {branch: branch for branch in range(self.number_of_gen_jobs)}

        # generator jobs with an existing `tar.bz2` or `root` output, one listdir per directory
        # of 1000 jobs
        generator_workflow = self.generator_workflow()
        pattern = re.compile(
            r"^{}job(\d+)\.(tar\.bz2|root)$".format(re.escape(str(self.campaign)))
        )
        branches = set()
        for first_branch in range(0, self.number_of_gen_jobs, 1000):
            directory = generator_workflow.hepmc_output_target(first_branch, "root").parent
            if not directory.exists():
                continue
            for name in directory.listdir():
                match = pattern.match(name)
                if match and int(match.group(1)) < self.number_of_gen_jobs:
                    branches.add(int(match.group(1)))
        # branch numbers are identical to the ones of the generator workflow
        return {branch: branch for branch in sorted(branches)}

    # no requires(), so that a missing generator output never triggers an event generation
    def hepmc_input(self):
        return self.generator_workflow().hepmc_output_target(self.branch_data, "tar.bz2")

    def branch_output(self, branch):
        # branch numbers are identical to the ones of the generator workflow
        return self.generator_workflow().hepmc_output_target(branch, "root")

    def output(self):
        return self.branch_output(self.branch)

    def run(self):
        input_target = self.hepmc_input()
        output = self.output()
        if not input_target.exists():
            raise IOError("Input file {} does not exist! Abort!".format(input_target.uri()))

        # ensure that the output directory exists
        output.parent.touch()

        # actual payload:
        print("=======================================================")
        print("Converting HepMC files to compressed HepMC3 ROOT format")
        print("=======================================================")

        tmp_dir = law.LocalDirectoryTarget(is_tmp=True)
        tmp_dir.touch()
        input_size = input_target.stat().st_size

        # get and unpack the generated HepMC files
        with input_target.localize("r") as tar_file:
            run_command(
                ["tar", "-xjf", tar_file.abspath, "-C", tmp_dir.abspath],
                env=os.environ,
            )
        hepmc_files = sorted(glob.glob(os.path.join(tmp_dir.abspath, "*.hepmc")))
        if not hepmc_files:
            raise IOError("No HepMC files found in {}! Abort!".format(input_target.uri()))
        for yoda_file in glob.glob(os.path.join(tmp_dir.abspath, "*.yoda")):
            logger.warning(
                "YODA file {} is not stored in the ROOT output!".format(
                    os.path.basename(yoda_file)
                )
            )

        # convert, the converter verifies that all events of the inputs are read and written
        root_file = law.LocalFileTarget(is_tmp="root")
        convert_hepmc(
            hepmc_files,
            root_file.abspath,
            hepmc_format="root",
            compression=self.root_compression,
        )
        output_size = root_file.stat().st_size
        store_verified(root_file.abspath, output)
        if self.remove_input:
            logger.info("Removing original file {}".format(input_target.uri()))
            input_target.remove()

        # summary of the storage savings
        size_change = input_size - output_size
        print("=======================================================")
        print("Original file:  {:>12}  {}".format(human_size(input_size), input_target.basename))
        print("Converted file: {:>12}  {}".format(human_size(output_size), output.basename))
        print(
            "File size {} by {} ({:.1%}){}".format(
                "decreased" if size_change >= 0 else "increased",
                human_size(abs(size_change)),
                abs(size_change) / input_size,
                "" if self.remove_input else ", original file kept",
            )
        )
        print("=======================================================")
