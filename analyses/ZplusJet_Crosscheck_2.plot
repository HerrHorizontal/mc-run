BEGIN PLOT /ZplusJet_Crosscheck/*
NormalizeToIntegral=1
END PLOT

# BEGIN HISTOGRAM /ZplusJet_Crosscheck/*
ErrorBars=1
# END HISTOGRAM

# BEGIN HISTOGRAM /ZplusJet_Crosscheck/Phi*
LogX=1
XLabel=$\phi^*_{\eta}$
YLabel=$\frac{1}{N}\frac{dN}{d\phi^*_{\eta} dy^* dy_b}$
# END HISTOGRAM

# BEGIN HISTOGRAM /ZplusJet_Crosscheck/ZPt*
LogX=1
XLabel=$p_{T_Z}$/GeV
YLabel=$\frac{1}{N}\frac{dN}{dp_{T_Z} dy^* dy_b}$/$\frac{1}{\text{GeV}}$
# END HISTOGRAM

# ... add more histograms as you need them ...
