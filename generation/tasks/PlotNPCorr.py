import json
import os

import law
import luigi
from generation.framework.config import BINS, JETS, MCCHAIN_SCENARIO_LABELS
from generation.framework.tasks import GenerationScenarioConfig, PostprocessingTask
from generation.framework.utils import (
    check_outdir,
    run_command,
    set_environment_variables,
)
from law.decorator import localize
from law.logger import get_logger
from luigi.util import inherits

from .DeriveNPCorr import DeriveNPCorr
from .RivetMerge import RivetMergeExtensions

logger = get_logger(__name__)


@inherits(GenerationScenarioConfig)
class PlotNPCorr(PostprocessingTask, law.LocalWorkflow):
    """
    Plotting class for NP-correction factor plots using the YODA API
    """

    # attribute not needed
    mc_setting = None

    # configuration variables
    campaign = luigi.Parameter(
        description="Name of the Herwig input file or Sherpa run directory used for event generation without file extension `.in`. \
                Per default saved in the `inputfiles` directory."
    )
    mc_setting_full = luigi.Parameter(
        default="withNP",
        description="Scenario identifier for the full MC production, typically `withNP`. \
                Used to identify the output-paths for the full generation scenario.",
    )
    mc_setting_partial = luigi.Parameter(
        default="NPoff",
        description="Scenario identifier for the partial MC production, typically `PSoff`, `NPoff`, `MPIoff` or `Hadoff`. \
                Used to identify the output-paths for the partial generation scenario, \
                where parts of the generation chain are turned off.",
    )
    mc_generator = luigi.Parameter(
        default="herwig",
        description="Name of the MC generator used for event generation.",
    )
    match = luigi.ListParameter(
        # significant=False,
        default=None,
        description="Require presence of analysis objects which names match these regexes in the YODA files.",
    )
    unmatch = luigi.ListParameter(
        # significant=False,
        default=None,
        description="Require exclusion of analysis objects which names match these regexes in the YODA files.",
    )
    filter_label_pad_tuples = luigi.TupleParameter(
        default=((".*", "", "Observable", "NP corr.", "arb. units"),),
        description='Tuple of tuples containing four or five strings:\n \
            - the filters for identification of the analysis objects to plot, match and unmatch, \n\
            - the x- and y-axis labels for the ratio pad (showing i.e. the NP-correction), \n\
            - OPTIONAL: the label for a top pad showing the original distributions used to derive the ratio \n\
            (("match", "unmatch", "xlabel", "ylabel", ["origin-ylabel"]), (...), ...)',
    )
    yrange = luigi.TupleParameter(
        default=[0.8, 1.3],
        significant=False,
        description="Value range for the y-axis of the ratio plot.",
    )

    fits = luigi.DictParameter(
        default=None,
        description="Dictionary of keys and paths to the files containing the fit information",
    )

    fit_method = luigi.Parameter(
        default="Nelder-Mead",
        description="Optimizer method for performing the smoothing fit. Choose between 'Nelder-Mead', 'trust-exact', 'BFGS'.",
    )

    splittings_conf_all = luigi.Parameter(
        # default="zjet",
        description="BINS identifier (predefined binning configuration in generation/framework/config.py) for all splittings. \
             Will set parameter 'splittings'. Overwritten by --splittings-all."
    )

    splittings_all = luigi.DictParameter(
        default=None,
        description="Splittings plot settings for all bins. Set via --splittings-conf-all from config, if None.",
    )
    threads = luigi.IntParameter(
        default=15, description="Number of threads to use for the fits."
    )
    max_chi2ndf = luigi.FloatParameter(
        default=10, description="Maximum chi2/ndf value for the fits."
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
        req = super(PlotNPCorr, self).workflow_requires()
        req["full"] = RivetMergeExtensions.req(self, mc_setting=self.mc_setting_full)
        req["partial"] = RivetMergeExtensions.req(
            self, mc_setting=self.mc_setting_partial
        )
        req["ratio"] = DeriveNPCorr.req(
            self,
            mc_setting_full=self.mc_setting_full,
            mc_setting_partial=self.mc_setting_partial,
            match=list(self.match),
            unmatch=list(self.unmatch),
        )
        return req

    def create_branch_map(self):
        bm = dict()
        for jobid, flp in enumerate(self.filter_label_pad_tuples):
            try:
                match, unmatch, xlabel, ylabel = flp
                bm[jobid] = dict(
                    match=match, unmatch=unmatch, xlabel=xlabel, ylabel=ylabel
                )
            except ValueError as e:
                logger.info("Acounted {}, trying with origin-y-label".format(e))
                match, unmatch, xlabel, ylabel, oylabel = flp
                bm[jobid] = dict(
                    match=match,
                    unmatch=unmatch,
                    xlabel=xlabel,
                    ylabel=ylabel,
                    oylabel=oylabel,
                )
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
            )
            + path
        )
        return os.path.join(*parts)

    def output(self):
        out = dict()
        out["single"] = self.local_target(
            "{full}-{partial}-Ratio-Plots/m-{match}-um-{unmatch}/".format(
                full=self.mc_setting_full,
                partial=self.mc_setting_partial,
                match=self.branch_data["match"],
                unmatch=self.branch_data["unmatch"],
            )
        )
        return out

    @localize(input=True, output=False)
    def run(self):
        check_outdir(self.output())

        if len(self.yrange) != 2:
            raise ValueError(
                "Argument --yrange takes exactly two values, but {} given!".format(
                    len(self.yrange)
                )
            )

        # actual payload:
        print("=======================================================")
        print("Starting NP-factor plotting with YODA")
        print("=======================================================")

        # assign paths for output YODA file and plots
        plot_dir_single = self.output()["single"].parent.path

        # check whether explicit defnition for splittings exists
        if self.splittings_all:
            splittings_all = luigi.DictParameter().serialize(self.splittings_all)
        else:
            if self.splittings_conf_all:
                splittings_all = json.dumps(BINS[self.splittings_conf_all])
            else:
                raise TypeError(
                    "Splittings undefined (None), configuration for --splittings-all or --splittings-conf-all needed!"
                )

        # execute the script deriving the NP correction plots and files
        executable = [
            "python",
            os.path.expandvars("$ANALYSIS_PATH/scripts/yodaPlotNPCorr.py"),
            "--full",
            "{}".format(self.input()["full"].abspath),
            "--partial",
            "{}".format(self.input()["partial"].abspath),
            "--ratio",
            "{}".format(self.input()["ratio"].abspath),
            "--plot-dir",
            "{}".format(plot_dir_single),
            "--yrange",
            "{}".format(self.yrange[0]),
            "{}".format(self.yrange[1]),
            "--splittings",
            "{}".format(splittings_all),
            "--jets",
            "{}".format(json.dumps(JETS)),
            "--full-label",
            "{}".format(
                MCCHAIN_SCENARIO_LABELS.get(self.mc_setting_full, self.mc_setting_full)
            ),
            "--partial-label",
            "{}".format(
                MCCHAIN_SCENARIO_LABELS.get(
                    self.mc_setting_partial, self.mc_setting_partial
                )
            ),
            "--fit-method",
            "{}".format(self.fit_method),
            "--threads",
            "{}".format(self.threads),
            "--max-chi2ndf",
            "{}".format(self.max_chi2ndf),
        ]
        executable += (
            [
                "--fit",
                "{}".format(
                    json.dumps(
                        dict(
                            {
                                os.path.join(plot_dir_single, k): v
                                for k, v in self.fits.items()
                            }
                        )
                    )
                ),
            ]
            if self.fits
            else []
        )
        executable += (
            ["--match", "{}".format(self.branch_data["match"])]
            if self.branch_data["match"]
            else []
        )
        executable += (
            ["--unmatch", "{}".format(self.branch_data["unmatch"])]
            if self.branch_data["unmatch"]
            else []
        )
        executable += (
            ["--xlabel", "{}".format(self.branch_data["xlabel"])]
            if self.branch_data["xlabel"]
            else []
        )
        executable += (
            ["--ylabel", "{}".format(self.branch_data["ylabel"])]
            if self.branch_data["ylabel"]
            else []
        )
        executable += (
            ["--origin", "--origin-ylabel", "{}".format(self.branch_data["oylabel"])]
            if self.branch_data.get("oylabel", None)
            else []
        )

        logger.info("Executable: {}".format(" ".join(executable)))

        rivet_env = set_environment_variables(
            os.path.expandvars("$ANALYSIS_PATH/setup/setup_rivet.sh")
        )
        try:
            run_command(
                executable, env=rivet_env, cwd=os.path.expandvars("$ANALYSIS_PATH")
            )
        except RuntimeError as e:
            logger.error("Individual bins' plots creation failed!")
            self.output()["single"].remove()
            raise e

        if not os.listdir(plot_dir_single):
            self.output()["single"].remove()
            raise LookupError("Plot directory {} is empty!".format(plot_dir_single))

        print("=======================================================")


class PlotNPCorrSummary(PlotNPCorr):
    """
    Plotting class for NP-correction factor summary plots using the YODA API
    """

    splittings_conf_all = None

    splittings_conf_summary = luigi.DictParameter(
        # default=dict(YS0="YS0", YB0="YB0", YSYBAll="zjet"),
        description="Dictionary of identifier and BINS identifier (predefined binning configuration in generation/framework/config.py) for summary splittings. \
             Will set parameter 'splittings'. Overwritten by --splittings-summary."
    )

    splittings_summary = luigi.DictParameter(
        default=None,
        description="Dictionary of identifier and splittings plot settings for all bins. Set via --splittings-conf-summary from config, if None.",
    )

    splittings_conf_all = luigi.Parameter(
        # default=splittings_conf_summary.values()[-1],
        description="BINS identifier (predefined binning configuration in generation/framework/config.py) covering all splittings. \
             Will set parameter 'splittings'. Overwritten by --splittings-all."
    )

    splittings_all = luigi.DictParameter(
        default=None,
        description="Splittings plot settings for all bins. Set via --splittings-conf-all from config, if None.",
    )

    def workflow_requires(self):
        reqs = super(PlotNPCorrSummary, self).workflow_requires()
        reqs["Fits"] = PlotNPCorr.req(self)
        return reqs

    def requires(self):
        return self.workflow_requires()

    def output(self):
        out = dict()
        out["summary"] = self.local_target(
            "{full}-{partial}-Ratio-Plots/m-{match}-um-{unmatch}/".format(
                full=self.mc_setting_full,
                partial=self.mc_setting_partial,
                match=self.branch_data["match"],
                unmatch=self.branch_data["unmatch"],
            )
        )
        return out

    @localize(input=True, output=False)
    def run(self):
        check_outdir(self.output())
        print("=======================================================")
        print("Starting NP-factor summary plotting with YODA")
        print("=======================================================")

        # assign paths for output YODA file and plots
        plot_dir_summary = self.output()["summary"].parent.path

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
                    "Splittings undefined (None), configuration for --splittings-summary or --splittings-conf-summary needed!"
                )

        # plot also summary plots
        executable_summary = [
            "python",
            os.path.expandvars("$ANALYSIS_PATH/scripts/yodaPlotNPCorrSummary.py"),
            "--ratio",
            self.input()["ratio"].abspath,
            "--plot-dir",
            "{}".format(plot_dir_summary),
            "--yrange",
            "{}".format(self.yrange[0]),
            "{}".format(self.yrange[1]),
            "--splittings",
            "{}".format(json.dumps(splittings_summary)),
            "--jets",
            "{}".format(json.dumps(JETS)),
            "--full-label",
            "{}".format(
                MCCHAIN_SCENARIO_LABELS.get(self.mc_setting_full, self.mc_setting_full)
            ),
            "--partial-label",
            "{}".format(
                MCCHAIN_SCENARIO_LABELS.get(
                    self.mc_setting_partial, self.mc_setting_partial
                )
            ),
            "--generator",
            "{}".format(str(self.mc_generator).lower()),
        ]
        executable_summary += (
            [
                "--fit",
                "{}".format(
                    json.dumps(
                        dict(
                            {
                                os.path.join(self.input()["Fits"].abspath, k): v
                                for k, v in self.fits.items()
                            }
                        )
                    )
                ),
            ]
            if self.fits
            else []
        )
        executable_summary += (
            ["--match", "{}".format(self.branch_data["match"])]
            if self.branch_data["match"]
            else []
        )
        executable_summary += (
            ["--unmatch", "{}".format(self.branch_data["unmatch"])]
            if self.branch_data["unmatch"]
            else []
        )
        executable_summary += (
            ["--xlabel", "{}".format(self.branch_data["xlabel"])]
            if self.branch_data["xlabel"]
            else []
        )
        executable_summary += (
            ["--ylabel", "{}".format(self.branch_data["ylabel"])]
            if self.branch_data["ylabel"]
            else []
        )

        logger.info("Executable: {}".format(" ".join(executable_summary)))

        rivet_env = set_environment_variables(
            os.path.expandvars("$ANALYSIS_PATH/setup/setup_rivet.sh")
        )
        try:
            run_command(
                executable_summary,
                env=rivet_env,
                cwd=os.path.expandvars("$ANALYSIS_PATH"),
            )
        except RuntimeError as e:
            logger.error("Summary plots creation failed!")
            self.output()["summary"].remove()
            raise e

        if not os.listdir(plot_dir_summary):
            self.output()["summary"].remove()
            raise LookupError("Plot directory {} is empty!".format(plot_dir_summary))

        print("-------------------------------------------------------")
