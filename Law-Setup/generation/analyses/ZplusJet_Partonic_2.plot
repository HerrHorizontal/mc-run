# BEGIN PLOT /ZplusJet_Partonic/*
LogX=1
RatioPlotYMin=0.8
RatioPlotYMax=1.2
RatioPlotYLabel=NP corr.
NormalizeToIntegral=1
# END PLOT

# BEGIN HISTOGRAM /ZplusJet_Partonic/*
ErrorBars=1
# END HISTOGRAM

# BEGIN HISTOGRAM /ZplusJet_Partonic/Phi*
XLabel=$\phi^*_{\eta}$
YLabel=$\frac{1}{N}\frac{dN}{d\phi^*_{\eta} dy^* dy_b}$
# END HISTOGRAM

# BEGIN HISTOGRAM /ZplusJet_Partonic/ZPt*
XLabel=$p_{T_Z}$/GeV
YLabel=$\frac{1}{N}\frac{dN}{dp_{T_Z} dy^* dy_b}$/$\frac{1}{\text{GeV}}$
# END HISTOGRAM

# ... add more histograms as you need them ...
