# BEGIN PLOT /ZplusJet/*
LogX=1
RatioPlotYMin=0.8
RatioPlotYMax=1.2
RatioPlotYLabel=NP corr.
NormalizeToIntegral=1
# END PLOT

# BEGIN HISTOGRAM /ZplusJet/*
ErrorBars=1
# END HISTOGRAM

# BEGIN HISTOGRAM /ZplusJet/Phi*
XLabel=$\phi^*_{\eta}$
YLabel=$\frac{1}{N}\frac{dN}{d\phi^*_{\eta} dy^* dy_b}$
# END HISTOGRAM

# BEGIN HISTOGRAM /ZplusJet/ZPt*
XLabel=$p_{T_Z}$/GeV
YLabel=$\frac{1}{N}\frac{dN}{dp_{T_Z} dy^* dy_b}$/$\frac{1}{\text{GeV}}$
# END HISTOGRAM

# BEGIN PLOT /ZplusJet/NJet*
LogX=0
XLabel=$N_{\text{jets}}$
YLabel=$\frac{1}{N}\frac{dN}{dN_{\text{jets}} dy^* dy_b}$
# END PLOT

# ... add more histograms as you need them ...
