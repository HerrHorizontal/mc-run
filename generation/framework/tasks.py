# -*- coding: utf-8 -*-

import os
import law.contrib
import luigi
import law
from luigi.util import inherits
from law.logger import get_logger


law.contrib.load("wlcg")
logger = get_logger(__name__)


class CommonConfig(luigi.Config):
    pass


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
            raise NotImplementedError("Local path method not implemented for this base class object! Use derived class instead!")
        except NotImplementedError as e:
            print(repr(e))

    def local_target(self, *path):
        return law.LocalFileTarget(self.local_path(*path))

    def remote_path():
        try:
            raise NotImplementedError("Remote path method not implemented for this base class object! Use derived class instead!")
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
        parts = (os.getenv("ANALYSIS_DATA_PATH"),) + (self.__class__.__name__,  self.campaign,) + path
        return os.path.join(*parts)

    def remote_path(self, *path):
        parts = (self.__class__.__name__, self.campaign,) + path
        return os.path.join(*parts)


class PostprocessingTask(BaseTask):

    def local_path(self, *path):
        parts = (os.getenv("ANALYSIS_DATA_PATH"),) + (self.__class__.__name__,) + path
        return os.path.join(*parts)

    def remote_path(self, *path):
        parts = (self.__class__.__name__,) + path
        return os.path.join(*parts)
