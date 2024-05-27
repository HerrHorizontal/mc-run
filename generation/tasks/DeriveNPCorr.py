
import luigi
from luigi.util import inherits
import os

from generation.framework.utils import run_command, set_environment_variables
from generation.framework.tasks import PostprocessingTask, GenerationScenarioConfig

from .RivetMerge import RivetMerge

from law.logger import get_logger


logger = get_logger(__name__)


@inherits(GenerationScenarioConfig)
class DeriveNPCorr(PostprocessingTask):
    """
    Plotting class for NP-correction factor plots using the YODA API
    """

    # attribute not needed
    mc_setting = None

    # configuration variables
    mc_setting_full = luigi.Parameter(
        default="withNP",
        description="Scenario identifier for the full MC production, typically `withNP`. \
                Used to identify the output-paths for the full generation scenario."
    )
    mc_setting_partial = luigi.Parameter(
        default="NPoff",
        description="Scenario identifier for the partial MC production, typically `NPoff`, `MPIoff` or `Hadoff`. \
                Used to identify the output-paths for the partial generation scenario, \
                where parts of the generation chain are turned off."
    )
    mc_generator = luigi.Parameter(
        default="herwig",
        description="Name of the MC generator used for event generation."
    )
    match = luigi.ListParameter(
        # significant=False,
        default=None,
        description="Include analysis objects which name matches these regexes."
    )
    unmatch = luigi.ListParameter(
        # significant=False,
        default=None,
        description="Exclude analysis objects which name matches these regexes."
    )

    exclude_params_req = {
        "source_script",
        "mc_setting_full",
        "mc_setting_partial",
        "match",
        "unmatch"
    }


    def requires(self):
        req = dict()
        req["full"] = RivetMerge.req(
            self, 
            mc_setting = self.mc_setting_full
        )
        req["partial"] = RivetMerge.req(
            self,
            mc_setting = self.mc_setting_partial
        )
        return req


    def remote_path(self, *path):
        parts = (self.__class__.__name__,str(self.mc_generator).lower(),self.campaign,) + path
        return os.path.join(*parts)


    def output(self):
        output = self.remote_target(
            "w-{match}-wo-{unmatch}/{full}-{partial}-Ratio.yoda".format(
                match = "-".join(list(self.match)),
                unmatch = "-".join(list(self.unmatch)),
                full = self.mc_setting_full,
                partial = self.mc_setting_partial,
            )
        )
        return output

    def run(self):
        # ensure that the output directory exists
        output = self.output()
        try:
            output.parent.touch()
        except IOError:
            logger.error("Output target doesn't exist!")

        # actual payload:
        print("=======================================================")
        print("Starting NP-factor calculation with YODA")
        print("=======================================================")

        # localize the separate YODA files on grid storage
        logger.info("Inputs:")
        with self.input()["full"].localize('r') as _file:
            logger.info("\tfull: {} cached at {}".format(self.input()["full"], _file.path))
            input_yoda_file_full = _file.path
        with self.input()["partial"].localize('r') as _file:
            logger.info("\tpartial: {} cached at {}".format(self.input()["partial"], _file.path))
            input_yoda_file_partial = _file.path

        # assign paths for output YODA file and plots
        output_yoda = "{full}-{partial}-Ratio.yoda".format(
            full = self.mc_setting_full,
            partial = self.mc_setting_partial
        )
        # execute the script deriving the NP correction plots and files
        executable = [
            "python", os.path.expandvars("$ANALYSIS_PATH/scripts/yodaDeriveNPCorr.py"),
            "--full", "{}".format(input_yoda_file_full),
            "--partial", "{}".format(input_yoda_file_partial),
            "--output-file", "{}".format(output_yoda)
        ]
        if self.match:
            executable += ["--match"] + [matchstr for matchstr in list(self.match)]
        if self.unmatch:
            executable += ["--unmatch"] + [matchstr for matchstr in list(self.unmatch)]

        logger.info("Executable: {}".format(" ".join(executable)))

        rivet_env = set_environment_variables(
            os.path.expandvars("$ANALYSIS_PATH/setup/setup_rivet.sh")
        )
        try:
            run_command(executable, env=rivet_env, cwd=os.path.expandvars("$ANALYSIS_PATH"))
            output_yoda = os.path.abspath(output_yoda)
            if not os.path.exists(output_yoda):
                raise IOError("Could not find output file {}!".format(output_yoda))
            output.copy_from_local(output_yoda)
            os.remove(output_yoda)
        except RuntimeError as e:
            output.remove()
            raise e

        print("-------------------------------------------------------")
