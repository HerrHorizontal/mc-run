import matplotlib as mpl
import matplotlib.pyplot as plt
import ROOT
import numpy as np
from plot_tools import plot_as_step, LogFormatterSciNotationForceSublabels

import matplotlib.ticker

# global plot settings
mpl.rcParams.update({'font.size': 11})
if int(mpl.__version__.split('.')[0]) >= 2:
    mpl.rc('xtick', direction='in', bottom=True, top=True)
    mpl.rc('ytick', direction='in', left=True, right=True)
else:
    mpl.rc('xtick', direction='in')
    mpl.rc('ytick', direction='in')
mpl.rc('axes', labelsize=16)
mpl.rc('legend', labelspacing=.1, fontsize=8)


files = {
   'lo': ROOT.TFile("LO_NP_full_AK4_mass.root", "READ"),
   'nlo': ROOT.TFile("NLO_NP_full_AK4_mass.root", "READ"),
}

YBYS_BINS = [
    "y1",
    "y2",
    "y3",
    "y4",
    "y5",
]
YBYS_LABELS = [
    r"$|y|_{max} < 0.5$",
    r"$0.5 \leq |y|_{max} < 1.0$",
    r"$1.0 \leq |y|_{max} < 1.5$",
    r"$1.5 \leq |y|_{max} < 2.0$",
    r"$2.0 \leq |y|_{max} < 2.5$"
]

fig = plt.figure(figsize=(10, 10))

axes = []
for i_ybys, ybys in enumerate(YBYS_BINS):
    hists = {
        'lo': files['lo'].Get("ak4_{}".format(ybys)),
        'nlo': files['nlo'].Get("ak4_{}".format(ybys)),
    }

    ax = plt.subplot(5, 1, i_ybys + 1)
    axes.append(ax)
    if i_ybys != len(YBYS_BINS) - 1:
        ax.set_xticklabels([])
        
    ## optional, should enable minor tick labels
    #minor_formatter = LogFormatterSciNotationForceSublabels(base=10.0, labelOnlyBase=False, sci_min_exp=5, sublabels_max_exp=3)
    #major_formatter = LogFormatterSciNotationForceSublabels(base=10.0, labelOnlyBase=True, sci_min_exp=5)
    #minor_formatter.set_locs(locs=[1., 2., 5., 10.])
    #ax.xaxis.set_minor_formatter(minor_formatter)
    #ax.xaxis.set_major_formatter(major_formatter)

    h = hists['lo']
    y = [h.GetBinContent(i) for i in range(1, h.GetNbinsX() + 1)]
    x = [h.GetBinCenter(i) for i in range(1, h.GetNbinsX() + 1)]
    xerr = [h.GetBinWidth(i)/2 for i in range(1, h.GetNbinsX() + 1)]
    plot_as_step(ax, x, y, xerr=(xerr, xerr), color='r', linewidth=2,
                 label="LO")

    h = hists['nlo']
    y = [h.GetBinContent(i) for i in range(1, h.GetNbinsX() + 1)]
    x = [h.GetBinCenter(i) for i in range(1, h.GetNbinsX() + 1)]
    xerr = [h.GetBinWidth(i)/2 for i in range(1, h.GetNbinsX() + 1)]
    plot_as_step(ax, x, y, xerr=(xerr, xerr), color='k', linestyle='dashed',
                 label="NLO")

    ax.annotate(YBYS_LABELS[i_ybys], xy=(0, 1), xycoords='axes fraction',
                xytext=(10, -10), textcoords='offset points',
                ha='left', va='top')
    
ax.annotate('R = 0.4, 2D', xy=(0, 1), xycoords='axes fraction',
             xytext=(10, -25), textcoords='offset points',
             ha='left', va='top',fontsize=14)

    
# final settings
fig.subplots_adjust(hspace=0)
axes[0].get_shared_y_axes().join(*axes)
axes[0].get_shared_x_axes().join(*axes)
axes[0].set_xscale('log')
axes[-1].legend(loc='center left', fontsize=12, frameon=False)
axes[0].set_ylabel('NP correction', y=1.0, ha='right', fontsize=12)
axes[-1].set_xlabel("m(GeV)", x=1.0, ha='right', fontsize=12)
plt.axis('equal')

def show_only_some(x, pos):
    s = str(int(x))
    if s[0] in ('2','5'):
        return s
    return ''
ax.xaxis.set_minor_formatter(plt.FuncFormatter(show_only_some))

'''
## optional, should enable minor tick labels
minor_formatter = LogFormatterSciNotationForceSublabels(base=10.0, labelOnlyBase=False, sci_min_exp=5, sublabels_max_exp=3)
major_formatter = LogFormatterSciNotationForceSublabels(base=10.0, labelOnlyBase=True, sci_min_exp=5)
minor_formatter.set_locs(locs=[1., 2., 5., 10.])
ax.xaxis.set_minor_formatter(minor_formatter)
ax.xaxis.set_major_formatter(major_formatter)
'''
plt.savefig('NP_full_AK4_mass_new.pdf')
plt.show()
