# BEGIN PLOT /ZplusJet_UE/*
LegendXPos=0.3
GofLegend=1
LogX=0
#RatioPlotMode=deviation
#RatioPlotYLabel=$\frac{\text{data2}-\text{data1}}{\text{uncertainty}}$
RatioPlotMode=default
RatioPlotYMin=0.8
RatioPlotYMax=1.2
RatioPlotYLabel=Ratio
NormalizeToIntegral=0
# END PLOT

# BEGIN HISTOGRAM /ZplusJet_UE/*
ErrorBars=1
LineOpacity=0.8
ErrorBandOpacity=0.8
ConnectBins=0
PolyMarker=*
# END HISTOGRAM

# BEGIN HISTOGRAM /ZplusJet_UE/NCharged*
XLabel=$p_T^Z$/GeV
YLabel=$N_{ch}$
LogY=0
ShowZero=1
# END HISTOGRAM

# BEGIN HISTOGRAM /ZplusJet_UE/pTsum*
XLabel=$p_{T_Z}$/GeV
YLabel=$p_T^{sum}$/GeV
# END HISTOGRAM

# END PLOT

# ... add more histograms as you need them ...
