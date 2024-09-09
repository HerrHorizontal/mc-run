import os
import shutil
from subprocess import PIPE

import law
import luigi
from generation.framework.tasks import GenerationScenarioConfig, GenRivetTask
from generation.framework.utils import (
    identify_inputfile,
    identify_setupfile,
    run_command,
    set_environment_variables,
)
from law.logger import get_logger
from luigi.util import inherits

logger = get_logger(__name__)


@inherits(GenerationScenarioConfig)
class HerwigConfig(law.ExternalTask):
    """
    Check for config file
    """

    mc_generator = "herwig"

    config_path = luigi.Parameter(
        significant=True,
        default="default",
        description="Directory where the Herwig config file resides. Default transaltes to `inputfiles/herwig/`.",
    )

    def output(self):
        return law.LocalFileTarget(
            identify_inputfile(self.campaign, self.config_path, self.mc_generator)
        )


class HerwigBuild(GenRivetTask):
    """
    Gather and compile all necessary libraries and prepare the integration \
    lists for the chosen Matchbox defined in the '[campaign].in' file \
    by running 'Herwig build', which will create the Herwig-cache directory \
    and the '[campaign].run' file
    """

    mc_generator = "herwig"

    # configuration variables
    integration_maxjobs = luigi.Parameter(
        description="Number of individual integration jobs to prepare. \
                Should not be greater than the number of subprocesses."
    )

    setupfile = luigi.Parameter(default=None)
    mc_setting = luigi.Parameter(default=None)

    exclude_params_req_get = {
        "htcondor_remote_job",
        "htcondor_accounting_group",
        "htcondor_request_cpus",
        "htcondor_universe",
        "htcondor_docker_image",
        "transfer_logs",
        "local_scheduler",
        "tolerance",
        "acceptance",
        "only_missing",
    }

    def requires(self):
        return {
            "HerwigConfig": HerwigConfig.req(self),
        }

    def remote_path(self, *path):
        if self.mc_setting == "PSoff":
            parts = (
                self.__class__.__name__,
                self.campaign,
                self.mc_setting,
            ) + path
            return os.path.join(*parts)
        else:
            parts = (
                self.__class__.__name__,
                self.campaign,
            ) + path
            return os.path.join(*parts)

    def output(self):
        return self.remote_target("Herwig-build.tar.gz")

    def run(self):
        # data
        campaign = str(self.campaign)
        _max_integration_jobs = str(self.integration_maxjobs)

        # ensure that the output directory exists
        output = self.output()
        output.parent.touch()

        # actual payload:
        print("=========================================================")
        print("Starting build step to generate Herwig-cache and run file")
        print("=========================================================")

        herwig_env = set_environment_variables(
            os.path.expandvars(
                os.path.join("$ANALYSIS_PATH", "setup", "setup_herwig.sh")
            )
        )
        # run Herwig build step
        _herwig_exec = ["Herwig", "build"]
        _herwig_args = [
            "--maxjobs={MAXJOBS}".format(MAXJOBS=_max_integration_jobs),
            "{INPUT_FILE}".format(INPUT_FILE=self.input()["HerwigConfig"].path),
        ]
        if self.mc_setting == "PSoff":
            _setupfile_path = identify_setupfile(
                self.setupfile, self.mc_generator, self.mc_setting, os.getcwd()
            )
            _herwig_args = [
                "--setupfile={SETUPFILE}".format(SETUPFILE=_setupfile_path)
            ] + _herwig_args

        logger.info("Executable: {}".format(" ".join(_herwig_exec + _herwig_args)))

        try:
            run_command(
                _herwig_exec + _herwig_args,
                env=herwig_env,
                cwd=os.path.expandvars("$ANALYSIS_PATH"),
            )
        except RuntimeError as e:
            output.remove()
            raise e

        cache_dir = os.path.abspath(os.path.expandvars("$ANALYSIS_PATH/Herwig-cache"))
        output_file = os.path.abspath(
            os.path.expandvars("$ANALYSIS_PATH/Herwig-build.tar.gz")
        )
        run_file = os.path.abspath(
            os.path.expandvars("$ANALYSIS_PATH/{}.run".format(campaign))
        )

        if os.path.exists(cache_dir) and os.path.isfile(run_file):
            logger.debug("Checking {} ...".format(cache_dir))
            if not os.listdir(cache_dir):
                raise LookupError(
                    "Herwig cache directory {} is empty!".format(cache_dir)
                )
            logger.debug(
                "Tarring {0} and {1} into {2} ...".format(
                    cache_dir, run_file, output_file
                )
            )
            os.system(
                "tar -czf {OUTPUT_FILE} {HERWIGCACHE} {INPUT_FILE_NAME}.run".format(
                    OUTPUT_FILE=output_file,
                    HERWIGCACHE=os.path.relpath(cache_dir),
                    INPUT_FILE_NAME=campaign,
                )
            )
        else:
            raise IOError(
                "Something went wrong, Herwig-cache or run-file doesn't exist! Abort!"
            )

        if os.path.exists(output_file):
            output.copy_from_local(output_file)
            os.remove(output_file)
            os.remove(run_file)
            shutil.rmtree(cache_dir)
        else:
            raise IOError("Could not find output file {}!".format(output_file))

        print("=======================================================")
