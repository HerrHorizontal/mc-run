import os

import yoda

import law
import luigi
from generation.framework.tasks import GenerationScenarioConfig, GenRivetTask
from generation.framework.utils import run_command
from generation.tasks.RivetBuild import RivetBuild, rivet_env
from generation.tasks.RunRivet import RunRivet
from law.contrib.tasks import ForestMerge
from law.logger import get_logger
from luigi.util import inherits

logger = get_logger(__name__)


@inherits(GenerationScenarioConfig)
class RivetMerge(GenRivetTask, ForestMerge):
    # configuration variables
    rivet_analyses = luigi.ListParameter(
        default=["MC_XS", "MC_WEIGHTS"],
        description="List of IDs of Rivet analyses to run.",
    )
    mc_generator = luigi.Parameter(
        default="herwig",
        description="Name of the MC generator used for event generation.",
    )
    skip_max_uncertainty = luigi.FloatParameter(
        default=0.25,
        description="Skip files when the uncertainty on the sum of weights is above this value. Default 0.25",
    )
    equiv = luigi.BoolParameter(
        default=True,
        description="Use the -e flag in rivet merge. This should be used if the extensions covers the same final state, phase space and cross section as the main campaign.",
    )
    # dummy parameter for run step
    number_of_gen_jobs = luigi.IntParameter()
    merge_factor = 100

    def workflow_requires(self):
        return {
            "analyses": RivetBuild.req(
                self,
                _exclude={"branch"},
            )
        }

    def merge_workflow_requires(self):
        return RunRivet.req(self, _exclude={"branch"})

    def merge_requires(self, start_leaf, end_leaf):
        return RunRivet.req(
            self, branches=((start_leaf, end_leaf),), _exclude={"branch"}
        )

    def remote_path(self, *path):
        parts = (
            self.__class__.__name__,
            str(self.mc_generator).lower(),
            self.campaign,
            self.mc_setting,
        ) + path
        return os.path.join(*parts)

    def merge_output(self):
        return self.remote_target(
            "_".join(sorted(self.rivet_analyses)) + ".yoda",
        )

    def trace_merge_inputs(self, inputs):
        return super().trace_merge_inputs(inputs["collection"].targets.values())

    def merge(self, inputs, output):
        tmp_dir = law.LocalDirectoryTarget(is_tmp=True)
        tmp_dir.touch()
        # copy Rivet Analyses
        for so_file in self.workflow_input()["analyses"]["collection"].iter_existing():
            so_file.copy_to_local(tmp_dir.child(so_file.basename, type="f"))
        # localize input files
        file_list = set()
        logger.debug(f"Merging inputs:\n{inputs}")
        for inp in inputs:
            inp.copy_to_local(tmp_dir.child(inp.unique_basename, type="f"))
            file_list.add(inp.unique_basename)
        # Skip files with excessive weight uncertainty
        skip_files = set()
        for _yoda_file in file_list:
            histos = yoda.read(
                f"{tmp_dir.abspath}/{_yoda_file}",
                asdict=True,
                patterns=["/RAW/_EVTCOUNT"],
            )
            evt_count = histos.get("/RAW/_EVTCOUNT", None)
            if evt_count.relErr() > self.skip_max_uncertainty:
                logger.warning(
                    f"Excessive weight uncertainty {evt_count.relErr()*100:.2f}%! Skipping: {_yoda_file}"
                )
                skip_files.add(_yoda_file)
        file_list -= skip_files
        logger.debug(f"Final files:\n{file_list}")
        # merge
        # append the current directory (pwd) to the analysis/data search paths
        command = ["rivet-merge", "--pwd"]
        if self.equiv:
            # assume that the yoda files are equivalent but statistically independent
            command.append("--equiv")
        # add output file and input files
        command += ["-o", "merged.yoda"] + list(file_list)
        run_command(command, env=rivet_env, cwd=tmp_dir.abspath)
        output.copy_from_local(tmp_dir.child("merged.yoda"))


@inherits(GenerationScenarioConfig)
class RivetMergeExtensions(RivetMerge):
    extensions = luigi.DictParameter(
        default=dict(),
        description="Campaign extensions (e.g. dedicated MC campaigns enhancing statistics in parts of phase space) identified by a list of suffices to the campaign name with a corresponding number of generation jobs to be expected.",
    )
    map_analyses = luigi.DictParameter(
        default={"Dijet_3": {"default": "Dijet_3_highpt", "_lowpt": "Dijet_3_lowpt"}},
        description="Map Rivet analyses to different names for the default run and the extensions. A default value is required.",
    )

    def merge_output(self):
        return self.remote_target(
            str(self.campaign) + "".join(self.extensions.keys()),
            "_".join(sorted(self.rivet_analyses)) + ".yoda",
        )

    def merge_workflow_requires(self):
        _mapping = [
            self.map_analyses.get(analysis, {"default": analysis})
            for analysis in self.rivet_analyses
        ]
        extensions = {k: v for k, v in self.extensions.items()}
        extensions["default"] = self.number_of_gen_jobs
        reqs = []
        for extension, nJobs in extensions.items():
            _mapped_analyses = [
                _map.get(extension, _map["default"]) for _map in _mapping
            ]
            if extension == "default":
                extension = ""
            kwargs = dict(
                campaign=(f"{self.campaign}{extension}"),
                rivet_analyses=_mapped_analyses,
            )
            if nJobs and nJobs > 0:
                kwargs["number_of_gen_jobs"] = nJobs
            reqs += [
                RivetMerge.req(
                    self,
                    _exclude={"branch", "equiv"},
                    **kwargs,
                )
            ]
        return reqs

    def merge_requires(self, start_leaf, end_leaf):
        return self.merge_workflow_requires()[int(start_leaf) : int(end_leaf)]

    def trace_merge_inputs(self, inputs):
        _target_list = []
        for input in inputs:
            _target_list += [target for target in input["collection"].targets.values()]
        return _target_list
