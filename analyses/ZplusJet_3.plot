# BEGIN PLOT /ZplusJet_3/*
LegendXPos=0.3
GofLegend=1
LogX=1
#RatioPlotMode=deviation
#RatioPlotYLabel=$\frac{\text{data2}-\text{data1}}{\text{uncertainty}}$
RatioPlotMode=default
RatioPlotYMin=0.8
RatioPlotYMax=1.2
RatioPlotYLabel=Ratio
NormalizeToIntegral=0
# END PLOT

# BEGIN HISTOGRAM /ZplusJet_3/*
ErrorBars=1
LineOpacity=0.8
ErrorBandOpacity=0.8
ConnectBins=0
PolyMarker=*
# END HISTOGRAM

# BEGIN HISTOGRAM /ZplusJet_3/PhiStarEta*
XLabel=$\phi^*_{\eta}$
YLabel=$\frac{1}{N}\frac{dN}{d\phi^*_{\eta} dy^* dy_b}$
# END HISTOGRAM

# BEGIN HISTOGRAM /ZplusJet_3/ZPt*
XLabel=$p_{T_Z}$/GeV
YLabel=$\frac{1}{N}\frac{dN}{dp_{T_Z} dy^* dy_b}$/$\frac{1}{\text{GeV}}$
# END HISTOGRAM

# BEGIN PLOT /ZplusJet_3/NJet*
LogX=0
XLabel=$N_{\text{jets}}$
YLabel=$\frac{1}{N}\frac{dN}{dN_{\text{jets}} dy^* dy_b}$
# END PLOT

# ... add more histograms as you need them ...
