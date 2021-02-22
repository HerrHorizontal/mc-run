// -*- C++ -*-
#include "Rivet/Analysis.hh"
#include "Rivet/Projections/FinalState.hh"
#include "Rivet/Projections/ChargedFinalState.hh"
#include "Rivet/Projections/PromptFinalState.hh"
#include "Rivet/Projections/VetoedFinalState.hh"
#include "Rivet/Projections/DressedLeptons.hh"
#include "Rivet/Projections/FastJets.hh"
#include "Rivet/Projections/JetAlg.hh"
#include "Rivet/Projections/MissingMomentum.hh"

namespace Rivet {


  /// @brief Add a short analysis description here
  class ZplusJet_2 : public Analysis {
  public:

    /// Constructor
    DEFAULT_RIVET_ANALYSIS_CTOR(ZplusJet_2);


    /// @name Analysis methods
    //@{

    /// Book histograms and initialise projections before the run
    void init() {

      /// Initialise and register projections
      const FinalState ffs(Cuts::abseta < 5 && Cuts::pT > 100*MeV);
      const ChargedFinalState cfs(ffs);
      declare(ffs, "FS");
      declare(cfs, "CFS");
      /// leptons
      PromptFinalState bare_leps(Cuts::abspid == PID::MUON || Cuts::abspid == PID::ELECTRON);
      declare(bare_leps, "bare_leptons");
      PromptFinalState photons(Cuts::abspid == PID::PHOTON);
      DressedLeptons dressed_leps(photons, bare_leps, 0.1, Cuts::abseta < 2.4 && Cuts::pT > 25*GeV);
      declare(dressed_leps, "dressed_leptons");
      /// jet collection
      FastJets jets(ffs, FastJets::ANTIKT, 0.4);
      declare(jets, "Jets");
      /// out of acceptance particles treat as invisible
      VetoedFinalState fs_onlyinacc(ffs, (Cuts::abspid == PID::MUON && Cuts::abseta > 2.4) || 
                                    (Cuts::abspid == PID::PHOTON && Cuts::abseta > 3.0) || 
                                    (Cuts::abspid == PID::ELECTRON && Cuts::abseta > 3.0));
      declare(MissingMomentum(fs_onlyinacc), "invisibles");

      /// Book histograms

      //// Book histograms with variable bin size
      vector<double> binedges_Ystar = {0.0, 0.5, 1.0, 1.5, 2.0, 2.5};
      vector<double> binedges_Yboost = {0.0, 0.5, 1.0, 1.5, 2.0, 2.5};
      vector<double> binedges_ZPtC = {25., 30., 35., 40., 50., 60., 70., 80., 90., 100., 110., 130., 150., 170., 190., 220., 250., 400., 1000.};
      vector<double> binedges_ZPtE = {25., 30., 35., 40., 45., 50., 60., 70., 80., 90., 100., 110., 130., 150., 170., 190., 250., 1000.};
      vector<double> binedges_ZPtX = {25., 30., 40., 50., 70., 90., 110., 150., 250.};
      vector<double> binedges_PhiStarEtaC = {0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2, 1.5, 2., 3., 4., 5., 7., 10., 15., 20., 30., 50.};
      vector<double> binedges_PhiStarEtaE = {0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2, 1.5, 2., 3., 5., 10., 15., 50.};
      vector<double> binedges_PhiStarEtaX = {0.4, 0.6, 0.8, 1.0, 5.};

      _hist_NJets = bookHisto1D("NJets", 10, 0.5, 10.5);

      _hist_Ys0Yb0_ZPt = bookHisto1D("ZPtY*0Yb0",binedges_ZPtC); 
      _hist_Ys0Yb05_ZPt = bookHisto1D("ZPtY*0Yb05",binedges_ZPtC); 
      _hist_Ys0Yb1_ZPt = bookHisto1D("ZPtY*0Yb1",binedges_ZPtC); 
      _hist_Ys0Yb15_ZPt = bookHisto1D("ZPtY*0Yb15",binedges_ZPtC); 
      _hist_Ys0Yb2_ZPt = bookHisto1D("ZPtY*0Yb2",binedges_ZPtE);
      _hist_Ys05Yb0_ZPt = bookHisto1D("ZPtY*05Yb0",binedges_ZPtC); 
      _hist_Ys05Yb05_ZPt = bookHisto1D("ZPtY*05Yb05",binedges_ZPtC); 
      _hist_Ys05Yb1_ZPt = bookHisto1D("ZPtY*05Yb1",binedges_ZPtC); 
      _hist_Ys05Yb15_ZPt = bookHisto1D("ZPtY*05Yb15",binedges_ZPtE);
      _hist_Ys1Yb0_ZPt = bookHisto1D("ZPtY*1Yb0",binedges_ZPtC); 
      _hist_Ys1Yb05_ZPt = bookHisto1D("ZPtY*1Yb05",binedges_ZPtC); 
      _hist_Ys1Yb1_ZPt = bookHisto1D("ZPtY*1Yb15",binedges_ZPtE);
      _hist_Ys15Yb0_ZPt  = bookHisto1D("ZPtY*15Yb0",binedges_ZPtE); 
      _hist_Ys15Yb05_ZPt = bookHisto1D("ZPtY*15Yb05",binedges_ZPtE);
      _hist_Ys2Yb0_ZPt = bookHisto1D("ZPtY*2Yb0",binedges_ZPtX);

      _hist_Ys0Yb0_PhiStarEta = bookHisto1D("Phi*_etaY*0Yb0",binedges_PhiStarEtaC); 
      _hist_Ys0Yb05_PhiStarEta = bookHisto1D("Phi*_etaY*0Yb05",binedges_PhiStarEtaC); 
      _hist_Ys0Yb1_PhiStarEta = bookHisto1D("Phi*_etaY*0Yb1",binedges_PhiStarEtaC); 
      _hist_Ys0Yb15_PhiStarEta = bookHisto1D("Phi*_etaY*0Yb15",binedges_PhiStarEtaC); 
      _hist_Ys0Yb2_PhiStarEta = bookHisto1D("Phi*_etaY*0Yb2",binedges_PhiStarEtaE);
      _hist_Ys05Yb0_PhiStarEta = bookHisto1D("Phi*_etaY*05Yb0",binedges_PhiStarEtaC); 
      _hist_Ys05Yb05_PhiStarEta = bookHisto1D("Phi*_etaY*05Yb05",binedges_PhiStarEtaC); 
      _hist_Ys05Yb1_PhiStarEta = bookHisto1D("Phi*_etaY*05Yb1",binedges_PhiStarEtaC); 
      _hist_Ys05Yb15_PhiStarEta = bookHisto1D("Phi*_etaY*05Yb15",binedges_PhiStarEtaE);
      _hist_Ys1Yb0_PhiStarEta = bookHisto1D("Phi*_etaY*1Yb0",binedges_PhiStarEtaC); 
      _hist_Ys1Yb05_PhiStarEta = bookHisto1D("Phi*_etaY*1Yb05",binedges_PhiStarEtaC); 
      _hist_Ys1Yb1_PhiStarEta = bookHisto1D("Phi*_etaY*1Yb15",binedges_PhiStarEtaE);
      _hist_Ys15Yb0_PhiStarEta  = bookHisto1D("Phi*_etaY*15Yb0",binedges_PhiStarEtaE); 
      _hist_Ys15Yb05_PhiStarEta = bookHisto1D("Phi*_etaY*15Yb05",binedges_PhiStarEtaE);
      _hist_Ys2Yb0_PhiStarEta = bookHisto1D("Phi*_etaY*2Yb0",binedges_PhiStarEtaX);
      
    }


    /// Perform the per-event analysis
    void analyze(const Event& event) {

      /// Find muons and jets
      //vector<DressedLepton> muons = apply<DressedLeptons>(event, "dressed_leptons").dressedLeptons(Cuts::abspid == PID::MUON && Cuts::abseta < 2.4 && Cuts::pT > 25*GeV);
      vector<DressedLepton> muons = apply<DressedLeptons>(event, "dressed_leptons").dressedLeptons();
      MSG_DEBUG("Muon multiplicity = " << muons.size());

      //// discard events with less than two muons
      if (muons.size() < 2) vetoEvent;

      Jets jets = apply<JetAlg>(event, "Jets").jetsByPt(Cuts::absrap < 2.4 && Cuts::pT > 10.0*GeV);
      MSG_DEBUG("Jet multiplicity before overlap removal = " << jets.size());

      //// Remove jet-muon overlap
      idiscardIfAnyDeltaRLess(jets, muons, 0.3);
      MSG_DEBUG("Jet multiplicity = " << jets.size());

      //// Require at least one hard jet
      if (jets.size() < 1) vetoEvent;      
      if (jets.at(0).pT() <= 20*GeV) vetoEvent;

      /// Require at least two opposite sign muons compatible with Z-boson mass and keep the pair closest to Zboson mass
      bool _bosoncandidateexists = false;
      double _massdiff = 20*GeV;
      DressedLepton _muon = muons.at(0);
      DressedLepton _antimuon = muons.at(0);

      for (unsigned int it = 1; it < muons.size(); ++it) {
        for (unsigned int jt = 0; jt < it; ++jt) {
          double _candidatemass = (muons.at(it).mom() + muons.at(jt).mom()).mass();
          if (muons.at(it).pid() == -muons.at(jt).pid() && abs(_candidatemass - 91.1876*GeV) < _massdiff) {
            _bosoncandidateexists = true;
            _massdiff = abs(_candidatemass - 91.1876*GeV);
            if (muons.at(it).pid() > 0) {
              _muon = muons.at(it);
              _antimuon = muons.at(jt);
            }
            else {
              _muon = muons.at(jt);
              _antimuon = muons.at(it);
            }
          }
          else continue;
        }
      }

      if (!(_bosoncandidateexists)) vetoEvent;

      /// Fill jet related histograms
      _hist_NJets -> fill(jets.size());

      /// Fill triple differential histograms
      const double rap_Z = (_muon.mom() + _antimuon.mom()).rap();

      const double pT_Z = (_muon.mom() + _antimuon.mom()).pT()/GeV;

      //const double pi = 3.14159265358979323846;
      const double thetastar = acos(tanh((_antimuon.mom().eta() - _muon.mom().eta())/2));
      const double phistareta = tan(HALFPI - (_antimuon.mom().phi() - _muon.mom().phi())/2)*sin(thetastar);

      const double rap_Jet1 = jets.at(0).rap();  

      const double rap_star = 0.5 * abs(rap_Z - rap_Jet1);
      const double rap_boost = 0.5 * abs(rap_Z + rap_Jet1);
      if (rap_star <= .5) {
        if (rap_boost < .5) {
          _hist_Ys0Yb0_ZPt -> fill(pT_Z);
          _hist_Ys0Yb0_PhiStarEta -> fill(phistareta);
        }
        else if (rap_boost < 1.) {
          _hist_Ys0Yb05_ZPt -> fill(pT_Z);
          _hist_Ys0Yb05_PhiStarEta -> fill(phistareta);
        }
        else if (rap_boost < 1.5) {
          _hist_Ys0Yb1_ZPt -> fill(pT_Z);
          _hist_Ys0Yb1_PhiStarEta -> fill(phistareta);
        }
        else if (rap_boost < 2.) {
          _hist_Ys0Yb15_ZPt -> fill(pT_Z);
          _hist_Ys0Yb15_PhiStarEta -> fill(phistareta);
        }
        else {
          _hist_Ys0Yb2_ZPt -> fill(pT_Z);
          _hist_Ys0Yb2_PhiStarEta -> fill(phistareta);
        }

      }
      else if (rap_star <= 1.) {
        if (rap_boost < .5) {
          _hist_Ys05Yb0_ZPt -> fill(pT_Z);
          _hist_Ys05Yb0_PhiStarEta -> fill(phistareta);
        }
        else if (rap_boost < 1.) {
          _hist_Ys05Yb05_ZPt -> fill(pT_Z);
          _hist_Ys05Yb05_PhiStarEta -> fill(phistareta);
        }
        else if (rap_boost < 1.5) {
          _hist_Ys05Yb1_ZPt -> fill(pT_Z);
          _hist_Ys05Yb1_PhiStarEta -> fill(phistareta);
        }
        else {
          _hist_Ys05Yb15_ZPt -> fill(pT_Z);
          _hist_Ys05Yb15_PhiStarEta -> fill(phistareta);
        }

      }
      else if (rap_star <= 1.5) {
        if (rap_boost < .5) {
          _hist_Ys1Yb0_ZPt -> fill(pT_Z);
          _hist_Ys1Yb0_PhiStarEta -> fill(phistareta);
        }
        else if (rap_boost < 1.) {
          _hist_Ys1Yb05_ZPt -> fill(pT_Z);
          _hist_Ys1Yb05_PhiStarEta -> fill(phistareta);
        }
        else {
          _hist_Ys1Yb1_ZPt -> fill(pT_Z);
          _hist_Ys1Yb1_PhiStarEta -> fill(phistareta);
        }
      }
      else if (rap_star <= 2.) {
        if (rap_boost < .5) {
          _hist_Ys15Yb0_ZPt -> fill(pT_Z);
          _hist_Ys15Yb0_PhiStarEta -> fill(phistareta);
        }
        else {
          _hist_Ys15Yb05_ZPt -> fill(pT_Z);
          _hist_Ys15Yb05_PhiStarEta -> fill(phistareta);
        }
      }
      else {
        _hist_Ys2Yb0_ZPt -> fill(pT_Z);
        _hist_Ys2Yb0_PhiStarEta -> fill(phistareta);
      }

    }


    /// Normalise histograms etc., after the run
    void finalize() {

      // normalize(_h_YYYY); // normalize to unity
      // const double sf = crossSection() / picobarn / sumOfWeights();
      const double sf = 1.0;

      scale(_hist_NJets, sf);

      scale(_hist_Ys0Yb0_ZPt, sf);
      scale(_hist_Ys0Yb05_ZPt, sf);
      scale(_hist_Ys0Yb1_ZPt, sf);
      scale(_hist_Ys0Yb15_ZPt, sf);
      scale(_hist_Ys0Yb2_ZPt, sf);
      scale(_hist_Ys05Yb0_ZPt, sf);
      scale(_hist_Ys05Yb05_ZPt, sf);
      scale(_hist_Ys05Yb1_ZPt, sf);
      scale(_hist_Ys05Yb15_ZPt, sf);
      scale(_hist_Ys1Yb0_ZPt, sf);
      scale(_hist_Ys1Yb05_ZPt, sf);
      scale(_hist_Ys1Yb1_ZPt, sf);
      scale(_hist_Ys15Yb0_ZPt, sf);
      scale(_hist_Ys15Yb05_ZPt, sf);
      scale(_hist_Ys2Yb0_ZPt, sf);

      scale(_hist_Ys0Yb0_PhiStarEta, sf);
      scale(_hist_Ys0Yb05_PhiStarEta, sf);
      scale(_hist_Ys0Yb1_PhiStarEta, sf);
      scale(_hist_Ys0Yb15_PhiStarEta, sf);
      scale(_hist_Ys0Yb2_PhiStarEta, sf);
      scale(_hist_Ys05Yb0_PhiStarEta, sf);
      scale(_hist_Ys05Yb05_PhiStarEta, sf);
      scale(_hist_Ys05Yb1_PhiStarEta, sf);
      scale(_hist_Ys05Yb15_PhiStarEta, sf);
      scale(_hist_Ys1Yb0_PhiStarEta, sf);
      scale(_hist_Ys1Yb05_PhiStarEta, sf);
      scale(_hist_Ys1Yb1_PhiStarEta, sf);
      scale(_hist_Ys15Yb0_PhiStarEta, sf);
      scale(_hist_Ys15Yb05_PhiStarEta, sf);
      scale(_hist_Ys2Yb0_PhiStarEta, sf);

    }

    //@}


    /// @name Histograms
    //@{

    /// Control Histograms
    Histo1DPtr _hist_NJets;

    Histo1DPtr _hist_Ys0Yb0_ZPt, _hist_Ys0Yb05_ZPt, _hist_Ys0Yb1_ZPt, _hist_Ys0Yb15_ZPt, _hist_Ys0Yb2_ZPt;
    Histo1DPtr _hist_Ys05Yb0_ZPt, _hist_Ys05Yb05_ZPt, _hist_Ys05Yb1_ZPt, _hist_Ys05Yb15_ZPt;
    Histo1DPtr _hist_Ys1Yb0_ZPt, _hist_Ys1Yb05_ZPt, _hist_Ys1Yb1_ZPt;
    Histo1DPtr _hist_Ys15Yb0_ZPt, _hist_Ys15Yb05_ZPt;
    Histo1DPtr _hist_Ys2Yb0_ZPt;

    Histo1DPtr _hist_Ys0Yb0_PhiStarEta, _hist_Ys0Yb05_PhiStarEta, _hist_Ys0Yb1_PhiStarEta, _hist_Ys0Yb15_PhiStarEta, _hist_Ys0Yb2_PhiStarEta;
    Histo1DPtr _hist_Ys05Yb0_PhiStarEta, _hist_Ys05Yb05_PhiStarEta, _hist_Ys05Yb1_PhiStarEta, _hist_Ys05Yb15_PhiStarEta;
    Histo1DPtr _hist_Ys1Yb0_PhiStarEta, _hist_Ys1Yb05_PhiStarEta, _hist_Ys1Yb1_PhiStarEta;
    Histo1DPtr _hist_Ys15Yb0_PhiStarEta, _hist_Ys15Yb05_PhiStarEta;
    Histo1DPtr _hist_Ys2Yb0_PhiStarEta;
  
    //@}


  };


  // The hook for the plugin system
  DECLARE_RIVET_PLUGIN(ZplusJet_2);


}
