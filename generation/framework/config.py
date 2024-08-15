
from collections import OrderedDict


MCCHAIN_SCENARIO_LABELS = {
    "withNP": "ME+PS+Had+MPI",
    "MPIoff": "ME+PS+Had",
    "Hadoff": "ME+PS+MPI",
    "NPoff": "ME+PS",
    "PSoff": "ME"
}

CAMPAIGN_MODS = {
    "herwigLHC-LO-ZplusJet": dict(
        order="LO",
        label=r"Herwig7 LO",
        lightencolor=1.0,
        linestyle="solid"
    ),
    "herwigLHC-NLO-ZplusJet": dict(
        order="NLO",
        label=r"Herwig7 NLO",
        lightencolor=0.7,
        linestyle="solid"
    ),
    "sherpaLHC-LO-ZplusJet": dict(
        order="LO",
        label=r"Sherpa LO",
        lightencolor=0.5,
        linestyle="dashdot"
    ),
    "sherpaLHC-NLO-ZplusJet": dict(
        order="NLO",
        label=r"Sherpa NLO",
        lightencolor=0.7,
        linestyle="dashed"
    ),
    "sherpaLHC-ZJetMerging": dict(
        order="NLO",
        label=r"Sherpa Merged",
        lightencolor=1.0,
        linestyle="solid"
    ),
    "herwigDijets_LO": dict(
        order="LO",
        label=r"MG@LO $\oplus$ Herwig7",
        lightencolor=1.0,
        linestyle="dotted"
    ),
    "herwigDijets_NLO": dict(
        order="NLO",
        label=r"MG@NLO $\oplus$ Herwig7",
        lightencolor=0.7,
        linestyle="solid"
    ),
    "sherpaDijets_LO": dict(
        order="LO",
        label=r"Sherpa LO",
        lightencolor=0.5,
        linestyle="dashed"
    ),
    "sherpaDijets_NLO": dict(
        order="NLO",
        label=r"Sherpa NLO",
        lightencolor=0.3,
        linestyle="dashdot"
    ),
}

JETS = {
    "AK4": dict(ident="AK4", label="Anti-kt\n$R=0.4$", linestyle="solid"),
    "AK8": dict(ident="AK8", label="Anti-kt\n$R=0.8$", linestyle="dashed"),
}

BINS = {
    # general 3D z+jet bins config 
    "zjet": OrderedDict({
        'YB_00_05_YS_00_05' : dict(
            ident="Ys0.000000Yb0.000000",
            label="$0.0<y^*\\leq 0.5$,\n$0.0<y_b\\leq 0.5$",
            ylim=[0.75,1.3],
            color="#5c15b6",
            marker="D",
            marker_style="full",
        ),
        'YB_00_05_YS_05_10' : dict(
            ident="Ys0.500000Yb0.000000",
            label="$0.5<y^*\\leq 1.0$,\n$0.0<y_b\\leq 0.5$",
            ylim=[0.75,1.3],
            color="#2659a2",
            marker="D",
            marker_style="full",
        ),
        'YB_00_05_YS_10_15' : dict(
            ident="Ys1.000000Yb0.000000",
            label="$1.0<y^*\\leq 1.5$,\n$0.0<y_b\\leq 0.5$",
            ylim=[0.75,1.3],
            color="#139913",
            marker="v",
            marker_style="full",
        ),
        'YB_00_05_YS_15_20' : dict(
            ident="Ys1.500000Yb0.000000",
            label="$1.5<y^*\\leq 2.0$,\n$0.0<y_b\\leq 0.5$",
            ylim=[0.75,1.3],
            color="#c55200",
            marker="v",
            marker_style="full",
        ),
        'YB_00_05_YS_20_25' : dict(
            ident="Ys2.000000Yb0.000000",
            label="$2.0<y^*\\leq 2.5$,\n$0.0<y_b\\leq 0.5$",
            ylim=[0.75,1.3],
            color="#a11313",
            marker="^",
            marker_style="full",
        ),
        'YB_05_10_YS_00_05' : dict(
            ident="Ys0.000000Yb0.500000",
            label="$0.0<y^*\\leq 0.5$,\n$0.5<y_b\\leq 1.0$",
            ylim=[0.75,1.3],
            color="#7959c4",
            marker="D",
            marker_style="full",
        ),
        'YB_05_10_YS_05_10' : dict(
            ident="Ys0.500000Yb0.500000",
            label="$0.5<y^*\\leq 1.0$,\n$0.5<y_b\\leq 1.0$",
            ylim=[0.75,1.3],
            color="#3e98b2",
            marker="D",
            marker_style="full",
        ),
        'YB_05_10_YS_10_15' : dict(
            ident="Ys1.000000Yb0.500000",
            label="$1.0<y^*\\leq 1.5$,\n$0.5<y_b\\leq 1.0$",
            ylim=[0.75,1.3],
            color="#51c230",
            marker="v",
            marker_style="full",
        ),
        'YB_05_10_YS_15_20' : dict(
            ident="Ys1.500000Yb0.500000",
            label="$1.5y^*\\leq 2.0$,\n$0.5<y_b\\leq 1.0$",
            ylim=[0.75,1.3],
            color="#ffa500",
            marker="v",
            marker_style="full",
        ),
        'YB_10_15_YS_00_05' : dict(
            ident="Ys0.000000Yb1.000000",
            label="$0.0<y^*\\leq 0.5$,\n$1.0<y_b\\leq 1.5$",
            ylim=[0.75,1.3],
            color="#9983cf",
            marker="s",
            marker_style="full",
        ),
        'YB_10_15_YS_05_10' : dict(
            ident="Ys0.500000Yb1.000000",
            label="$0.5<y^*\\leq 1.0$,\n$1.0<y_b\\leq 1.5$",
            ylim=[0.75,1.3],
            color="#67b4cb",
            marker="s",
            marker_style="full",
        ),
        'YB_10_15_YS_10_15' : dict(
            ident="Ys1.000000Yb1.000000",
            label="$1.0<y^*\\leq 1.5$,\n$1.0<y_b\\leq 1.5$",
            ylim=[0.75,1.3],
            color="#8def56",
            marker=">",
            marker_style="full",
        ),
        'YB_15_20_YS_00_05' : dict(
            ident="Ys0.000000Yb1.500000",
            label="$0.0<y^*\\leq 0.5$,\n$1.5<y_b\\leq 2.0$",
            ylim=[0.75,1.3],
            color="#c6b2e2",
            marker="s",
            marker_style="full",
        ),
        'YB_15_20_YS_05_10' : dict(
            ident="Ys0.500000Yb1.500000",
            label="$0.5<y^*\\leq 1.0$,\n$1.5<y_b\\leq 2.0$",
            ylim=[0.75,1.3],
            color="#a0eaff",
            marker="s",
            marker_style="full",
        ),
        'YB_20_25_YS_00_05' : dict(
            ident="Ys0.000000Yb2.000000",
            label="$0.0<y^*\\leq 0.5$,\n$2.0<y_b\\leq 2.5$",
            ylim=[0.75,1.3],
            color="#fab0ff",
            marker="o",
            marker_style="full",
        ),
    }),
}
# according 3D dijet config
BINS["dijets"] = {k: dict(v, ident=k) for k,v in BINS["zjet"].items()}

# add bin configs for 3D underlying event analyses
BINS["zjet_RFUE_all"] = {
    "_".join((region,k)): dict(
        v,
        ident="_".join([
            region,
            v["ident"][:2]+"="+"{:.6f}".format(float(v["ident"][2:10])+0.5),
            v["ident"][10:12]+"="+"{:.6f}".format(float(v["ident"][12:])+0.5)
        ]),
        label=v["label"]
    )
    for k,v in BINS["zjet"].items()
    for region in ["Towards", "Transverse", "Away"]
}
for region in ["Towards", "Transverse", "Away"]:
    BINS[f"zjet_RFUE_{region}"] = {
        "_".join((region,k)): dict(
            v,
            ident="_".join([
                region,
                v["ident"][:2]+"="+"{:.6f}".format(float(v["ident"][2:10])+0.5),
                v["ident"][10:12]+"="+"{:.6f}".format(float(v["ident"][12:])+0.5)
            ]),
            label=v["label"]
        )
        for k,v in BINS["zjet"].items()
    }
# filtered yb=0 and ys=0 bins only
    BINS[f"YB0_zjet_RFUE_{region}"] = {k: v for k,v in BINS[f"zjet_RFUE_{region}"].items() if "YB_00_05" in k}
    BINS[f"YS0_zjet_RFUE_{region}"] = {k: v for k,v in BINS[f"zjet_RFUE_{region}"].items() if "YS_00_05" in k}

BINS["YB0_zjet"] = {k: v for k,v in BINS["zjet"].items() if "YB_00_05" in k}
BINS["YS0_zjet"] = {k: v for k,v in BINS["zjet"].items() if "YS_00_05" in k}

BINS["YB0_dijets"] = {k: v for k,v in BINS["dijets"].items() if "YB_00_05" in k}
BINS["YS0_dijets"] = {k: v for k,v in BINS["dijets"].items() if "YS_00_05" in k}

BINS["test"] = {k: v for k,v in BINS["zjet"].items() if "YB_05_10_YS_10_15" in k}
