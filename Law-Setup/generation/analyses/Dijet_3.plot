BEGIN PLOT /.*
LogX=1
LogY=1
PlotYMin=1e-9
PlotYMax=1e-1
RatioPlot=0
RatioPlotSameStyle=1
RatioPlotMode=datamc
RatioPlotYMin=0.4
RatioPlotYMax=1.6
LegendXPos = 0.5
END PLOT

# -- color curves depending on jet size

# BEGIN HISTOGRAM /Dijet_3/.*AK4
LineColor=blue
LineStyle=solid
Title=XS
# END HISTOGRAM

# BEGIN HISTOGRAM /Dijet_3/.*AK8
LineColor=red
LineStyle=solid
Title=XS
# END HISTOGRAM

# -- label axes depending on observable

# BEGIN HISTOGRAM /Dijet_3/.*_Mass_.*
XLabel=$m_{1,2}$ (GeV)
YLabel=$d^3\sigma / dm_{1,2}\,dy_b\,dy^*$ (pb/GeV)
#XCustomMajorTicks=1000 1000 10000 10000
#XCustomMinorTicks=300 300 500 500 2000 2000 3000 3000 5000 5000
XCustomMajorTicks=300 300 500 500 1000 1000 2000 2000 3000 3000 5000 5000 10000 10000
# END HISTOGRAM

# BEGIN HISTOGRAM /Dijet_3/.*_PtAve_.*
XLabel=$\langle p_{\mathrm{T}}\rangle_{1,2}$ (GeV)
YLabel=$d^3\sigma / d\langle p_{\mathrm{T}}\rangle_{1,2}\,dy_b\,dy^*$ (pb/GeV)
#XCustomMajorTicks=100 100 1000 1000
#XCustomMinorTicks=200 200 300 300 500 500 2000 2000 3000 3000 5000 5000
XCustomMajorTicks=200 200 300 300 500 500 1000 1000 2000 2000 3000 3000 5000 5000
Title=PtAve
# END HISTOGRAM

# -- identify (yb, ys) region in bottom-left corner

# BEGIN SPECIAL /Dijet_3/.*YB_00_05_YS_00_05.*
    \psclip{\psframe[linewidth=0, linestyle=none](0,0)(1,1)}
    \uput{4pt}[0]{0}(0.05,0.1){$0.0 \leq y^{*} < 0.5$, $0.0 \leq y_{\mathrm{b}} < 0.5$}
    \endpsclip
# END SPECIAL

# BEGIN SPECIAL /Dijet_3/.*YB_00_05_YS_05_10.*
    \psclip{\psframe[linewidth=0, linestyle=none](0,0)(1,1)}
    \uput{4pt}[0]{0}(0.05,0.1){$0.5 \leq y^{*} < 1.0$, $0.0 \leq y_{\mathrm{b}} < 0.5$}
    \endpsclip
# END SPECIAL

# BEGIN SPECIAL /Dijet_3/.*YB_00_05_YS_10_15.*
    \psclip{\psframe[linewidth=0, linestyle=none](0,0)(1,1)}
    \uput{4pt}[0]{0}(0.05,0.1){$1.0 \leq y^{*} < 1.5$, $0.0 \leq y_{\mathrm{b}} < 0.5$}
    \endpsclip
# END SPECIAL

# BEGIN SPECIAL /Dijet_3/.*YB_00_05_YS_15_20.*
    \psclip{\psframe[linewidth=0, linestyle=none](0,0)(1,1)}
    \uput{4pt}[0]{0}(0.05,0.1){$1.5 \leq y^{*} < 2.0$, $0.0 \leq y_{\mathrm{b}} < 0.5$}
    \endpsclip
# END SPECIAL

# BEGIN SPECIAL /Dijet_3/.*YB_00_05_YS_20_25.*
    \psclip{\psframe[linewidth=0, linestyle=none](0,0)(1,1)}
    \uput{4pt}[0]{0}(0.05,0.1){$2.0 \leq y^{*} < 2.5$, $0.0 \leq y_{\mathrm{b}} < 0.5$}
    \endpsclip
# END SPECIAL

# BEGIN SPECIAL /Dijet_3/.*YB_05_10_YS_00_05.*
    \psclip{\psframe[linewidth=0, linestyle=none](0,0)(1,1)}
    \uput{4pt}[0]{0}(0.05,0.1){$0.0 \leq y^{*} < 0.5$, $0.5 \leq y_{\mathrm{b}} < 1.0$}
    \endpsclip
# END SPECIAL

# BEGIN SPECIAL /Dijet_3/.*YB_05_10_YS_05_10.*
    \psclip{\psframe[linewidth=0, linestyle=none](0,0)(1,1)}
    \uput{4pt}[0]{0}(0.05,0.1){$0.5 \leq y^{*} < 1.0$, $0.5 \leq y_{\mathrm{b}} < 1.0$}
    \endpsclip
# END SPECIAL

# BEGIN SPECIAL /Dijet_3/.*YB_05_10_YS_10_15.*
    \psclip{\psframe[linewidth=0, linestyle=none](0,0)(1,1)}
    \uput{4pt}[0]{0}(0.05,0.1){$1.0 \leq y^{*} < 1.5$, $0.5 \leq y_{\mathrm{b}} < 1.0$}
    \endpsclip
# END SPECIAL

# BEGIN SPECIAL /Dijet_3/.*YB_05_10_YS_15_20.*
    \psclip{\psframe[linewidth=0, linestyle=none](0,0)(1,1)}
    \uput{4pt}[0]{0}(0.05,0.1){$1.5 \leq y^{*} < 2.0$, $0.5 \leq y_{\mathrm{b}} < 1.0$}
    \endpsclip
# END SPECIAL

# BEGIN SPECIAL /Dijet_3/.*YB_10_15_YS_00_05.*
    \psclip{\psframe[linewidth=0, linestyle=none](0,0)(1,1)}
    \uput{4pt}[0]{0}(0.05,0.1){$0.0 \leq y^{*} < 0.5$, $1.0 \leq y_{\mathrm{b}} < 1.5$}
    \endpsclip
# END SPECIAL

# BEGIN SPECIAL /Dijet_3/.*YB_10_15_YS_05_10.*
    \psclip{\psframe[linewidth=0, linestyle=none](0,0)(1,1)}
    \uput{4pt}[0]{0}(0.05,0.1){$0.5 \leq y^{*} < 1.0$, $1.0 \leq y_{\mathrm{b}} < 1.5$}
    \endpsclip
# END SPECIAL

# BEGIN SPECIAL /Dijet_3/.*YB_10_15_YS_10_15.*
    \psclip{\psframe[linewidth=0, linestyle=none](0,0)(1,1)}
    \uput{4pt}[0]{0}(0.05,0.1){$1.0 \leq y^{*} < 1.5$, $1.0 \leq y_{\mathrm{b}} < 1.5$}
    \endpsclip
# END SPECIAL

# BEGIN SPECIAL /Dijet_3/.*YB_15_20_YS_00_05.*
    \psclip{\psframe[linewidth=0, linestyle=none](0,0)(1,1)}
    \uput{4pt}[0]{0}(0.05,0.1){$0.0 \leq y^{*} < 0.5$, $1.5 \leq y_{\mathrm{b}} < 2.0$}
    \endpsclip
# END SPECIAL

# BEGIN SPECIAL /Dijet_3/.*YB_15_20_YS_05_10.*
    \psclip{\psframe[linewidth=0, linestyle=none](0,0)(1,1)}
    \uput{4pt}[0]{0}(0.05,0.1){$0.5 \leq y^{*} < 1.0$, $1.5 \leq y_{\mathrm{b}} < 2.0$}
    \endpsclip
# END SPECIAL

# BEGIN SPECIAL /Dijet_3/.*YB_20_25_YS_00_05.*
    \psclip{\psframe[linewidth=0, linestyle=none](0,0)(1,1)}
    \uput{4pt}[0]{0}(0.05,0.1){$0.0 \leq y^{*} < 0.5$, $2.0 \leq y_{\mathrm{b}} < 2.5$}
    \endpsclip
# END SPECIAL
