
MCCHAIN_SCENARIO_LABELS = {
    "withNP": "ME+PS+Had+MPI",
    "MPIoff": "ME+PS+Had",
    "Hadoff": "ME+PS+MPI",
    "NPoff": "ME+PS"
}

BINS = {
    "all": {
        'YB_00_05_YS_00_05' : dict(
            ident="Ys0.000000Yb0.000000",
            label="$0.0<y^*\\leq 0.5$,\n$0.0<y_b\\leq 0.5$",
            ylim=[0.75,1.3],
        ),
        'YB_00_05_YS_05_10' : dict(
            ident="Ys0.500000Yb0.000000",
            label="$0.5<y^*\\leq 1.0$,\n$0.0<y_b\\leq 0.5$",
            ylim=[0.75,1.3],
        ),
        'YB_00_05_YS_10_15' : dict(
            ident="Ys1.000000Yb0.000000",
            label="$1.0<y^*\\leq 1.5$,\n$0.0<y_b\\leq 0.5$",
            ylim=[0.75,1.3],
        ),
        'YB_00_05_YS_15_20' : dict(
            ident="Ys1.500000Yb0.000000",
            label="$1.5<y^*\\leq 2.0$,\n$0.0<y_b\\leq 0.5$",
            ylim=[0.75,1.3],
        ),
        'YB_00_05_YS_20_25' : dict(
            ident="Ys2.000000Yb0.000000",
            label="$2.0<y^*\\leq 2.5$,\n$0.0<y_b\\leq 0.5$",
            ylim=[0.75,1.3],
        ),
        'YB_05_10_YS_00_05' : dict(
            ident="Ys0.000000Yb0.500000",
            label="$0.0<y^*\\leq 0.5$,\n$0.5<y_b\\leq 1.0$",
            ylim=[0.75,1.3],
        ),
        'YB_05_10_YS_05_10' : dict(
            ident="Ys0.500000Yb0.500000",
            label="$0.5<y^*\\leq 1.0$,\n$0.5<y_b\\leq 1.0$",
            ylim=[0.75,1.3],
        ),
        'YB_05_10_YS_10_15' : dict(
            ident="Ys1.000000Yb0.500000",
            label="$1.0<y^*\\leq 1.5$,\n$0.5<y_b\\leq 1.0$",
            ylim=[0.75,1.3],
        ),
        'YB_05_10_YS_15_20' : dict(
            ident="Ys1.500000Yb0.500000",
            label="$1.5y^*\\leq 2.0$,\n$0.5<y_b\\leq 1.0$",
            ylim=[0.75,1.3],
        ),
        'YB_10_15_YS_00_05' : dict(
            ident="Ys0.000000Yb1.000000",
            label="$0.0<y^*\\leq 0.5$,\n$1.0<y_b\\leq 1.5$",
            ylim=[0.75,1.3],
        ),
        'YB_10_15_YS_05_10' : dict(
            ident="Ys0.500000Yb1.000000",
            label="$0.5<y^*\\leq 1.0$,\n$1.0<y_b\\leq 1.5$",
            ylim=[0.75,1.3],
        ),
        'YB_10_15_YS_10_15' : dict(
            ident="Ys1.000000Yb1.000000",
            label="$1.0<y^*\\leq 1.5$,\n$1.0<y_b\\leq 1.5$",
            ylim=[0.75,1.3],
        ),
        'YB_15_20_YS_00_05' : dict(
            ident="Ys0.000000Yb1.500000",
            label="$0.0<y^*\\leq 0.5$,\n$1.5<y_b\\leq 2.0$",
            ylim=[0.75,1.3],
        ),
        'YB_15_20_YS_05_10' : dict(
            ident="Ys0.500000Yb1.500000",
            label="$0.5<y^*\\leq 1.0$,\n$1.5<y_b\\leq 2.0$",
            ylim=[0.75,1.3],
        ),
        'YB_20_25_YS_00_05' : dict(
            ident="Ys0.000000Yb2.000000",
            label="$0.0<y^*\\leq 0.5$,\n$2.0<y_b\\leq 2.5$",
            ylim=[0.75,1.3],
        ),
    },
}
BINS["YB0"] = {k: v for k,v in BINS["all"].items() if "YB_00_05" in k}
BINS["YS0"] = {k: v for k,v in BINS["all"].items() if "YS_00_05" in k}
