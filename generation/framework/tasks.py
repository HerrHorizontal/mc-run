# -*- coding: utf-8 -*-

import os
from warnings import simplefilter

import law
import law.contrib
import luigi
from generation.framework.hepmc import HEPMC_FORMATS, hepmc_converter_job_input
from law.logger import get_logger
from luigi.parameter import UnconsumedParameterWarning
from luigi.util import inherits

# Ignore warnings about unused parameters that are set in the default config but not used by all tasks
simplefilter("ignore", UnconsumedParameterWarning)


law.contrib.load("wlcg")
logger = get_logger(__name__)


class CommonConfig(luigi.Config):
    from ast import literal_eval
    from luigi.configuration import add_config_path
    Config = luigi.configuration.cfg_parser.LuigiConfigParser.instance()
    for add_config in literal_eval(Config.get("AddConfigFiles", "add_configs")):
        add_config_path(os.path.expandvars(add_config))


@inherits(CommonConfig)
class GenerationScenarioConfig(luigi.Config):
    campaign = luigi.Parameter(
        description="Name of the Herwig input file or Sherpa run directory used for event generation without file extension `.in`. \
                Per default saved in the `inputfiles` directory."
    )
    mc_setting = luigi.Parameter(
        description="Scenario of the MC production. Typically one of the following: `withNP`, `PSoff`, `NPoff`, `MPIoff` or `Hadoff`. \
                Used to differentiate between output-paths for different generation scenarios."
    )


class HepMCOutputMixin:
    """
    Parameters steering the file format of the generated HepMC events. Defaults are read from
    the [HepMCOutput] section of luigi.cfg, so that generator and analysis tasks agree on them.
    """

    ConfigParser = luigi.configuration.cfg_parser.LuigiConfigParser.instance()
    hepmc_format = luigi.ChoiceParameter(
        default=ConfigParser.get("HepMCOutput", "hepmc_format", "root"),
        choices=list(HEPMC_FORMATS) + ["tar.bz2"],
        var_type=str,
        description="File format of the generated events: `root` (HepMC3 ROOT TTree), \
                `hepmc3` (HepMC3 ascii), `hepmc3.gz` (gzip-compressed HepMC3 ascii) or \
                `tar.bz2` (legacy MC-Run format).",
    )
    root_compression = luigi.IntParameter(
        default=ConfigParser.getint("HepMCOutput", "root_compression", 209),
        significant=False,
        description="ROOT compression setting (100 * algorithm + level) of `root` output, \
                209 is LZMA 9.",
    )

    def hepmc_output_target(self, branch=None, hepmc_format=None):
        """
        Remote target of the generated events of a generator job, in sub-directories of 1000
        jobs each. Defaults to the branch and file format of this task.
        """
        branch = self.branch if branch is None else branch
        return self.remote_target(
            str(int(branch) // 1000),
            "{INPUT_FILE_NAME}job{JOB_NUMBER}.{EXTENSION}".format(
                INPUT_FILE_NAME=str(self.campaign),
                JOB_NUMBER=str(branch),
                EXTENSION=hepmc_format or self.hepmc_format,
            ),
        )


class HepMCConverterJobMixin:
    """
    Ship the HepMC converter, built once at submission, with the HTCondor jobs of tasks that
    convert HepMC files. Not needed for the `tar.bz2` format.
    """

    def htcondor_job_config(self, config, job_num, branches):
        config = super().htcondor_job_config(config, job_num, branches)
        if getattr(self, "hepmc_format", "root") in HEPMC_FORMATS:
            config.input_files["hepmc_converter"] = hepmc_converter_job_input()
        return config


@inherits(CommonConfig)
class BaseTask(law.Task):
    def local_path():
        try:
            raise NotImplementedError(
                "Local path method not implemented for this base class object! Use derived class instead!"
            )
        except NotImplementedError as e:
            print(repr(e))

    def local_target(self, *path):
        return law.LocalFileTarget(self.local_path(*path))

    def remote_path():
        try:
            raise NotImplementedError(
                "Remote path method not implemented for this base class object! Use derived class instead!"
            )
        except NotImplementedError as e:
            print(repr(e))

    def remote_target(self, *path):
        return law.wlcg.WLCGFileTarget(
            self.remote_path(*path),
            fs="wlcg_fs",
        )


@inherits(GenerationScenarioConfig)
class GenRivetTask(BaseTask):

    def local_path(self, *path):
        parts = (
            (os.getenv("ANALYSIS_DATA_PATH"),)
            + (
                self.__class__.__name__,
                self.campaign,
            )
            + path
        )
        return os.path.join(*parts)

    def remote_path(self, *path):
        parts = (
            self.__class__.__name__,
            self.campaign,
        ) + path
        return os.path.join(*parts)


class PostprocessingTask(BaseTask):

    def local_path(self, *path):
        parts = (os.getenv("ANALYSIS_DATA_PATH"),) + (self.__class__.__name__,) + path
        return os.path.join(*parts)

    def remote_path(self, *path):
        parts = (self.__class__.__name__,) + path
        return os.path.join(*parts)
