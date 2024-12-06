# -*- coding: utf-8 -*-

import os
from warnings import simplefilter

import law
import law.contrib
import luigi
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
