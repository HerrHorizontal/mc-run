
import luigi, law
from luigi.util import inherits
import os
import json

from subprocess import PIPE
from generation.framework.utils import run_command, rivet_env
from generation.framework.config import MCCHAIN_SCENARIO_LABELS, BINS, JETS, CAMPAIGN_MODS

from generation.framework.tasks import Task, CommonConfig

from PlotNPCorr import PlotNPCorr

@inherits(CommonConfig)
class PlotScenarioComparison(Task, law.LocalWorkflow):
    """Plot a comparison of fitted NP factors created with different scenarios"""

    input_file_name = "Comparison"

    rivet_analyses = luigi.ListParameter(
        default=["ZplusJet_3"],
        description="List of IDs of Rivet analyses to run"
    )

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

    campaigns = luigi.ListParameter(
        default=["LHC-LO-ZplusJet", "LHC-NLO-ZplusJet"],
        description="Campaigns to compare identified by the name of their Herwig input file"
    )

    match = luigi.Parameter(
        # significant=False,
        default="ZplusJet",
        description="Require presence of analysis objects which names match this regex in the YODA files."
    )
    unmatch = luigi.Parameter(
        # significant=False,
        default="MC_",
        description="Require exclusion of analysis objects which names match this regex in the YODA files."
    )
    filter_label_pad_tuples = luigi.TupleParameter(
        default=(("ZPt","RAW","p_T^Z\,/\,\mathrm{GeV}","NP corr."),),
        description="Tuple of tuples containing four or five strings:\n \
            - the filter for identification of the analysis objects to plot, match and unmatch, \n\
            - the x- and y-axis labels for the ratio pad (showing i.e. the NP-correction), \n\
            - OPTIONAL: the label for a top pad showing the original distributions used to derive the ratio \n\
            ((\"match\", \"unmatch\", \"xlabel\", \"ylabel\", [\"origin-ylabel\"]), (...), ...)"
    )
    yrange = luigi.TupleParameter(
        default=[0.8,1.3],
        significant=False,
        description="Value range for the y-axis of the ratio plot."
    )

    fits = luigi.DictParameter(
        default=None,
        description="Dictionary of keys and paths to the files containing the fit information"
    )

    def _default_fits(self):
        return {k: "{a}_{q}{j}{k}.json".format(a=ana,q="ZPt",j=jet,k=k)
            for k in BINS["all"]
            for ana in self.rivet_analyses
            for jet in JETS.keys()
        }


    def workflow_requires(self):
        req = super(PlotScenarioComparison, self).workflow_requires()
        for scen in self.campaigns:
            if self.fits:
                fits = self.fits
            else:
                fits = self._default_fits()
            req[scen] = PlotNPCorr.req(self, input_file_name=scen, fits=fits)
        return req
    

    def create_branch_map(self):
        bm = dict()
        for jobid, flp in enumerate(self.filter_label_pad_tuples):
            try:
                match, unmatch, xlabel, ylabel = flp
                bm[jobid] = dict(match=match, unmatch=unmatch, xlabel=xlabel, ylabel=ylabel)
            except ValueError as e:
                print("Acounted {}, trying with origin-y-label".format(e))
                match, unmatch, xlabel, ylabel, oylabel = flp
                bm[jobid] = dict(match=match, unmatch=unmatch, xlabel=xlabel, ylabel=ylabel, oylabel=oylabel)
        return bm
    

    def requires(self):
        req = dict()
        for scen in self.campaigns:
            if self.fits:
                fits = self.fits
            else:
                fits = self._default_fits()
            req[scen] = PlotNPCorr.req(self, input_file_name=scen, fits=fits)
        return req
    

    def output(self):
        return self.local_target(
            "m-{match}-um-{unmatch}/{full}-{partial}-Ratio-Plots/{campaigns}/".format(
                full = self.mc_setting_full,
                partial = self.mc_setting_partial,
                match=self.branch_data["match"],
                unmatch=self.branch_data["unmatch"],
                campaigns="-".join(self.campaigns)
            )
        )


    def run(self):
        # ensure that the output directory exists
        output = self.output()
        try:
            output.parent.touch()
        except IOError:
            print("Output target {} doesn't exist!".format(output.parent))
            output.makedirs()

        if len(self.yrange) != 2:
            raise ValueError("Argument --yrange takes exactly two values, but {} given!".format(len(self.yrange)))
        
        # actual payload:
        print("=======================================================")
        print("Starting comparison NP-factor plotting for campaigns {}".format(self.campaigns))
        print("=======================================================")

        plot_dir = output.parent.path
        
        if self.fits:
            fits = self.fits
        else:
            fits = self._default_fits()
        fits_dict = dict()
        print(self.input())
        for campaign in self.campaigns:
            fits_dict[campaign] = {k: os.path.join(self.input()[campaign]["single"].path, v) for k,v in fits.items()}

        # execute the script reading the fitted NP correctiuons and plotting the comparison
        executable = ["python", os.path.expandvars("$ANALYSIS_PATH/scripts/plotCampaignComparison.py")]
        for campaign, fits in fits_dict.items():
            executable += ["--campaign", "{}".format(campaign), "--fit", "{}".format(json.dumps(fits))]
        executable += ["--mods", "{}".format(json.dumps(CAMPAIGN_MODS))]
        executable += [
            "--plot-dir", "{}".format(plot_dir),
            "--yrange", "{}".format(self.yrange[0]), "{}".format(self.yrange[1]),
            "--splittings", "{}".format(json.dumps(dict(YS0=BINS["YS0"],YB0=BINS["YB0"],YSYBAll=BINS["all"]))),
            "--jets", "{}".format(json.dumps(JETS)),
            "--full-label", "{}".format(MCCHAIN_SCENARIO_LABELS.get(self.mc_setting_full, self.mc_setting_full)),
            "--partial-label", "{}".format(MCCHAIN_SCENARIO_LABELS.get(self.mc_setting_partial, self.mc_setting_partial))
        ]
        executable += ["--xlabel", "{}".format(self.branch_data["xlabel"])] if self.branch_data["xlabel"] else []
        executable += ["--ylabel", "{}".format(self.branch_data["ylabel"])] if self.branch_data["ylabel"] else []

        print("Executable: {}".format(" ".join(executable)))

        try:
            run_command(executable, env=rivet_env, cwd=os.path.expandvars("$ANALYSIS_PATH"))
        except RuntimeError as e:
            print("Summary plots creation failed!")
            output.remove()
            raise e
        
        if not os.listdir(plot_dir):
            output.remove()
            raise LookupError("Plot directory {} is empty!".format(plot_dir))

        print("-------------------------------------------------------")
