import luigi
import law
from luigi.util import inherits
import os
import json

from generation.framework.utils import (
    run_command,
    set_environment_variables,
    check_outdir,
    localize_input,
)
from generation.framework.config import MCCHAIN_SCENARIO_LABELS, BINS, JETS

from generation.framework.tasks import PostprocessingTask, GenerationScenarioConfig

from .RivetMerge import RivetMerge

from law.logger import get_logger


logger = get_logger(__name__)


@inherits(GenerationScenarioConfig)
class PlotSplittedQuantity(PostprocessingTask, law.LocalWorkflow):
    """
    Plotting class for NP-correction factor plots using the YODA API
    """

    # configuration variables
    campaign = luigi.Parameter(
        description="Name of the Herwig input file or Sherpa run directory used for event generation without file extension `.in`. \
                Per default saved in the `inputfiles` directory."
    )
    mc_setting = luigi.Parameter(
        default="withNP",
        description="Scenario identifier for MC production, typically `withNP` for full chain. \
                Used to identify the corresponding input Rivet analysis objects.",
    )
    mc_generator = luigi.Parameter(
        default="herwig",
        description="Name of the MC generator used for event generation.",
    )

    filter_label_pad_tuples = luigi.TupleParameter(
        default=((".*", "", "Observable", "NP corr."),),
        description='Tuple of tuples containing four strings each:\n \
            - the filters for identification of the analysis objects to plot, match and unmatch, \n\
            - the x- and y-axis labels, \n\
            (("match", "unmatch", "xlabel", "ylabel"), (...), ...)',
    )
    yrange = luigi.TupleParameter(
        default=[0.0, 10],
        significant=False,
        description="Value range for the y-axis of the plot.",
    )

    splittings_conf_summary = luigi.DictParameter(
        # default="zjet",
        description="BINS identifier (predefined binning configuration in generation/framework/config.py) for all splittings. \
             Will set parameter 'splittings'. Overwritten by --splittings-all."
    )
    splittings_summary = luigi.DictParameter(
        default=None,
        description="Splittings plot settings for all bins. Set via --splittings-conf-all from config, if None.",
    )

    exclude_params_req = {
        "source_script",
    }
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

    def workflow_requires(self):
        req = super(PlotSplittedQuantity, self).workflow_requires()
        req["Rivet"] = RivetMerge.req(self)
        return req

    def create_branch_map(self):
        bm = dict()
        for jobid, flp in enumerate(self.filter_label_pad_tuples):
            match, unmatch, xlabel, ylabel = flp
            bm[jobid] = dict(match=match, unmatch=unmatch, xlabel=xlabel, ylabel=ylabel)
        return bm

    def requires(self):
        return self.workflow_requires()

    def local_path(self, *path):
        parts = (
            (os.getenv("ANALYSIS_DATA_PATH"),)
            + (
                self.__class__.__name__,
                str(self.mc_generator).lower(),
                self.campaign,
                self.mc_setting,
            )
            + path
        )
        return os.path.join(*parts)

    def output(self):
        out = dict()
        out["summary"] = self.local_target(
            "m-{match}-um-{unmatch}/".format(
                match=self.branch_data["match"],
                unmatch=self.branch_data["unmatch"],
            )
        )
        return out

    def run(self):
        check_outdir(self.output())
        print("=======================================================")
        print("Starting summary plotting for quantity {} with YODA".format(self.branch_data["match"]))
        print("=======================================================")

        inputs = dict()
        logger.debug("\n\nInput:\n{}\n\n".format(self.input()))
        inputs["Rivet"] = localize_input(self.input()["Rivet"])

        # assign paths for output YODA file and plots
        plot_dir = self.output()["summary"].parent.path

        # check whether explicit defnition for splittings exists
        if self.splittings_summary:
            splittings_summary = self.splittings_summary
        else:
            if self.splittings_conf_summary:
                splittings_summary = {
                    k: BINS[v] for k, v in self.splittings_conf_summary.items()
                }
            else:
                raise TypeError(
                    "Splittings undefined (None), configuration for "
                    + "--splittings-summary or --splittings-conf-summary needed!"
                )

        # plot also summary plots
        executable = [
            "python",
            os.path.expandvars("$ANALYSIS_PATH/scripts/yodaPlotSplittedQuantity.py"),
            "--in",
            "{}".format(inputs["Rivet"]),
            "--plot-dir",
            "{}".format(plot_dir),
            "--yrange",
            "{}".format(self.yrange[0]),
            "{}".format(self.yrange[1]),
            "--splittings",
            "{}".format(json.dumps(splittings_summary)),
            "--jets",
            "{}".format(json.dumps(JETS)),
            "--generator",
            "{}".format(str(self.mc_generator).lower()),
            "--match",
            "{}".format(self.branch_data["match"]),
            "--unmatch",
            "{}".format(self.branch_data["unmatch"]),
            "--xlabel",
            "{}".format(self.branch_data["xlabel"]),
            "--ylabel",
            "{}".format(self.branch_data["ylabel"]),
        ]

        logger.info("Executable: {}".format(" ".join(executable)))

        rivet_env = set_environment_variables(
            os.path.expandvars("$ANALYSIS_PATH/setup/setup_rivet.sh")
        )
        try:
            run_command(
                executable,
                env=rivet_env,
                cwd=os.path.expandvars("$ANALYSIS_PATH"),
            )
        except RuntimeError as e:
            logger.error("Summary plots creation failed!")
            self.output()["summary"].remove()
            raise e

        if not os.listdir(plot_dir):
            self.output()["summary"].remove()
            raise LookupError("Plot directory {} is empty!".format(plot_dir))

        print("-------------------------------------------------------")
