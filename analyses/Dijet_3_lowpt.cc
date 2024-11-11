// -*- C++ -*-
#include "Rivet/Analysis.hh"
#include "Rivet/Projections/FinalState.hh"
#include "Rivet/Projections/FastJets.hh"


namespace Rivet {

  /// @brief Add a short analysis description here
  class Dijet_3 : public Analysis {
  public:

    /// Constructor
    DEFAULT_RIVET_ANALYSIS_CTOR(Dijet_3);

    /// @name Analysis methods
    //@{

    /// Book histograms and initialize projections before the run
    void init() {

      // Initialize and register projections
      const FinalState fs;
      declare(fs, "FinalState");

      // declare jets (both AK4 and AK8)
      FastJets fj_ak04(fs, FastJets::ANTIKT, 0.4);
      FastJets fj_ak08(fs, FastJets::ANTIKT, 0.8);
      declare(fj_ak04, "JetsAK4");
      declare(fj_ak08, "JetsAK8");

      // mjj bin edges for each of the 15 (yb, ys) rapidity regions
      std::vector<std::vector<double>> binEdgesMass = {
        // YB_00_05_YS_00_05
        {306, 372, 449, 539, 641, 756, 887, 1029, 1187, 1361, 1556, 1769, 2008, 2273, 2572, 2915, 3306, 3754, 4244, 4805, 5374, 6094},
        // YB_05_10_YS_00_05
        {306, 372, 449, 539, 641, 756, 887, 1029, 1187, 1361, 1556, 1769, 2008, 2273, 2572, 2915, 3306, 3754, 4244, 4805},
        // YB_10_15_YS_00_05
        {306, 372, 449, 539, 641, 756, 887, 1029, 1187, 1361, 1556, 1769, 2008, 2273, 2572, 2915, 3306, 3754},
        // YB_15_20_YS_00_05
        {372, 539, 756, 1029, 1361, 1769, 2273},
        // YB_20_25_YS_00_05
        {372, 539, 756, 1029, 1361},
        // YB_00_05_YS_05_10
        {449, 539, 641, 756, 887, 1029, 1187, 1361, 1556, 1769, 2008, 2273, 2572, 2915, 3306, 3754, 4244, 4805, 5374, 6094},
        // YB_05_10_YS_05_10
        {449, 539, 641, 756, 887, 1029, 1187, 1361, 1556, 1769, 2008, 2273, 2572, 2915, 3306, 3754, 4244, 4805},
        // YB_10_15_YS_05_10
        {539, 756, 1029, 1361, 1769, 2273, 2915, 3754},
        // YB_15_20_YS_05_10
        {539, 756, 1029, 1361, 1769, 2273},
        // YB_00_05_YS_10_15
        {641, 756, 887, 1029, 1187, 1361, 1556, 1769, 2008, 2273, 2572, 2915, 3306, 3754, 4244, 4805, 5374, 6094},
        // YB_05_10_YS_10_15
        {756, 1029, 1361, 1769, 2273, 2915, 3754, 4805},
        // YB_10_15_YS_10_15
        {756, 1029, 1361, 1769, 2273, 2915, 3574},
        // YB_00_05_YS_15_20
        {1029, 1361, 1769, 2273, 2915, 3754, 4805, 6094},
        // YB_05_10_YS_15_20
        {1029, 1361, 1769, 2273, 2915, 3754, 4805},
        // YB_00_05_YS_20_25
        {1361, 1769, 2273, 2915, 3754, 4805, 6094},
      };

      // ptave bin edges for each of the 15 (yb, ys) rapidity regions
      std::vector<std::vector<double>> binEdgesPtAve = {
        // YB_00_05_YS_00_05
        {147, 175, 207, 243, 284, 329, 380, 437, 499, 569, 646, 732, 827, 931, 1046, 1171, 1307, 1458, 1621, 1806, 2003, 2217, 2453, 2702},
        // YB_05_10_YS_00_05
        {147, 175, 207, 243, 284, 329, 380, 437, 499, 569, 646, 732, 827, 931, 1046, 1171, 1307, 1458, 1621, 1806, 2003, 2217},
        // YB_10_15_YS_00_05
        {147, 175, 207, 243, 284, 329, 380, 437, 499, 569, 646, 732, 827, 931, 1046, 1171, 1307, 1458, 1621},
        // YB_15_20_YS_00_05
        {147, 207, 284, 380, 499, 646, 827, 1046},
        // YB_20_25_YS_00_05
        {147, 207, 284, 380, 499, 646},
        // YB_00_05_YS_05_10
        {147, 175, 207, 243, 284, 329, 380, 437, 499, 569, 646, 732, 827, 931, 1046, 1171, 1307, 1458, 1621, 1806, 2003, 2217, 2453},
        // YB_05_10_YS_05_10
        {147, 175, 207, 243, 284, 329, 380, 437, 499, 569, 646, 732, 827, 931, 1046, 1171, 1307, 1458, 1621, 1806},
        // YB_10_15_YS_05_10
        {147, 207, 284, 380, 499, 646, 827, 1046, 1307},
        // YB_15_20_YS_05_10
        {147, 207, 284, 380, 499, 646, 827, 1046},
        // YB_00_05_YS_10_15
        {147, 175, 207, 243, 284, 329, 380, 437, 499, 569, 646, 732, 827, 931, 1046, 1171, 1307, 1458, 1621, 1806},
        // YB_05_10_YS_10_15
        {147, 207, 284, 380, 499, 646, 827, 1046, 1307},
        // YB_10_15_YS_10_15
        {147, 207, 284, 380, 499, 646, 827, 1046},
        // YB_00_05_YS_15_20
        {147, 207, 284, 380, 499, 646, 827, 1046, 1307},
        // YB_05_10_YS_15_20
        {147, 207, 284, 380, 499, 646, 827, 1046},
        // YB_00_05_YS_20_25
        {147, 207, 284, 380, 499, 646, 827},
      };

#if 1
    std::vector<double> binExtension = {47, 57, 67, 77, 87, 97, 107, 127};
    for (std::vector<double> & binEdges: binEdgesPtAve) {
      binEdges.insert(binEdges.begin(), binExtension.begin(), binExtension.end());
    }
#endif

      // Book histograms
      m_hist_ybys_ptave_ak04.resize(15);
      m_hist_ybys_ptave_ak08.resize(15);
      m_hist_ybys_mass_ak04.resize(15);
      m_hist_ybys_mass_ak08.resize(15);
      for (size_t idx_yboost = 0; idx_yboost < 5; idx_yboost++) {
        for (size_t idx_ystar = 0; idx_ystar < 5 - idx_yboost; idx_ystar++) {
          size_t idx_ybys = getYBYSIndex(idx_yboost, idx_ystar);

          char ybysName[20];
          std::snprintf(ybysName, sizeof(ybysName),
                        "YB_%02d_%02d_YS_%02d_%02d",
                        idx_yboost * 5, (idx_yboost + 1) * 5,
                        idx_ystar * 5, (idx_ystar + 1) * 5
          );

          book(m_hist_ybys_ptave_ak04[idx_ybys], std::string(ybysName) + "_PtAve_AK4", binEdgesPtAve[idx_ybys]);
          book(m_hist_ybys_ptave_ak08[idx_ybys], std::string(ybysName) + "_PtAve_AK8", binEdgesPtAve[idx_ybys]);
          book(m_hist_ybys_mass_ak04[idx_ybys], std::string(ybysName) + "_Mass_AK4", binEdgesMass[idx_ybys]);
          book(m_hist_ybys_mass_ak08[idx_ybys], std::string(ybysName) + "_Mass_AK8", binEdgesMass[idx_ybys]);

        }
      }
    }

    /// Perform the per-event analysis
    void analyze(const Event& event) {

      /// @todo Do the event by event analysis here

      const FastJets& fj_ak04 = apply<FastJets>(event, "JetsAK4");
      const FastJets& fj_ak08 = apply<FastJets>(event, "JetsAK8");

      // select all jets above minimum pt threshold within rapidity acceptance
      const Jets& jets_ak04 = fj_ak04.jetsByPt(Cuts::pt >= _subleadingjetpt && Cuts::absrap < 5);
      const Jets& jets_ak08 = fj_ak08.jetsByPt(Cuts::pt >= _subleadingjetpt && Cuts::absrap < 5);

      // fill histograms for both jet sizes
      fillHistograms(jets_ak04, m_hist_ybys_ptave_ak04, m_hist_ybys_mass_ak04);
      fillHistograms(jets_ak08, m_hist_ybys_ptave_ak08, m_hist_ybys_mass_ak08);
    }

    void fillHistograms(const Jets& jets, std::vector<Histo1DPtr>& histograms_ybys_ptave, std::vector<Histo1DPtr>& histograms_ybys_mass) {
      // if fewer than two jets, return
      if (jets.size() < 2) return;

      // check dijet phase space: want events where the leading and subleading jets
      // pass the required pt thresholds, respectively, //
      // and both satisfy |y| < 3.0
      if ( (jets[0].pt() >= _leadingjetpt) && (jets[0].absrap() < 3) &&
           (jets[1].pt() >= _subleadingjetpt)  && (jets[1].absrap() < 3) ) {

        // calculate observables
        double ystar = 0.5 * std::abs(jets[0].rap() - jets[1].rap());
        double yboost = 0.5 * std::abs(jets[0].rap() + jets[1].rap());
        double ptavg = 0.5 * (jets[0].pT() + jets[1].pT());
	      if (ptavg > 147) return;
        double mass = FourMomentum(jets[0].momentum() + jets[1].momentum()).mass();

        // compute index of histogram to be filled from (yb, ys): yb0ys0 --> 0, yb1ys0 --> 1 ...
        size_t idx_ystar  = (size_t)(ystar * 2);
        size_t idx_yboost = (size_t)(yboost * 2);

        // if outside (yb, ys) phase space, return
        int idx_ybys = getYBYSIndex(idx_yboost, idx_ystar);
        if (idx_ybys < 0) return;

        // fill corresponding ptave/mjj histograms
        histograms_ybys_ptave[idx_ybys]->fill(ptavg/GeV);
        histograms_ybys_mass[idx_ybys]->fill(mass/GeV);
      }
    }

    /// Normalize histograms etc., after the run
    void finalize() {

      // normalize histograms to cross section
      scale(m_hist_ybys_ptave_ak04, crossSection()/picobarn/sumOfWeights());
      scale(m_hist_ybys_mass_ak04,  crossSection()/picobarn/sumOfWeights());
      scale(m_hist_ybys_ptave_ak08, crossSection()/picobarn/sumOfWeights());
      scale(m_hist_ybys_mass_ak08,  crossSection()/picobarn/sumOfWeights());

    }

    //@}

    /// @name Histograms
    //@{
    std::vector<Histo1DPtr> m_hist_ybys_ptave_ak04;
    std::vector<Histo1DPtr> m_hist_ybys_mass_ak04;
    std::vector<Histo1DPtr> m_hist_ybys_ptave_ak08;
    std::vector<Histo1DPtr> m_hist_ybys_mass_ak08;
    //@}

  private:

    /** index of (ystar, yboost) region (integer between 0 and 15: YB_00_05_YS_00_05 --> 0, YB_05_10_YS_00_05 --> 1 ...)
      * or -1 if out of bounds.
      * `idx_yboost` and `idx_ystar` should be one of {0, 1, 2, 3, 4}
      */
    static int getYBYSIndex(size_t idx_yboost, size_t idx_ystar) {
      int idx_ybys = idx_yboost + 5 * idx_ystar - idx_ystar * (idx_ystar - 1) / 2;
      if ((0 <= idx_ybys) && (idx_ybys < 15))
          return idx_ybys;
      else
          return -1;
    }

  /// @name Selections
    ///@{
  const double _leadingjetpt = 30*GeV; // minimum jet pT
  const double _subleadingjetpt = 25*GeV; // minimum jet pT
  ///@}

  };

  // The hook for the plugin system
  DECLARE_RIVET_PLUGIN(Dijet_3);

}
