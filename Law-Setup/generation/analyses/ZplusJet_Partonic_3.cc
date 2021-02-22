// -*- C++ -*-
#include "Rivet/Analysis.hh"
#include "Rivet/Projections/FinalState.hh"
#include "Rivet/Projections/FinalPartons.hh"
#include "Rivet/Projections/ChargedFinalState.hh"
#include "Rivet/Projections/PromptFinalState.hh"
#include "Rivet/Projections/VetoedFinalState.hh"
#include "Rivet/Projections/DressedLeptons.hh"
#include "Rivet/Projections/FastJets.hh"
#include "Rivet/Projections/JetAlg.hh"
#include "Rivet/Projections/MissingMomentum.hh"

namespace Rivet {


  /// @brief Add a short analysis description here
  class ZplusJet_Partonic_3 : public Analysis {
  public:

    /// Constructor
    DEFAULT_RIVET_ANALYSIS_CTOR(ZplusJet_Partonic_3);


    /// @name Analysis methods
    ///@{

    /// Book histograms and initialise projections before the run
    void init() {

      cout << "Starting initializing ..." << endl;

      // Initialise and register projections

      // The basic final-state projection:
      // all final-state particles within
      // the given eta acceptance
      const FinalPartons fs(Cuts::abseta < 5. && Cuts::pT > 100*MeV);


      // The final-state particles declared above are clustered using FastJet with
      // the anti-kT algorithm and a jet-radius parameter 0.4
      // neutrinos are excluded from the clustering
      FastJets jetfs(fs, FastJets::ANTIKT, 0.4, JetAlg::Muons::ALL, JetAlg::Invisibles::NONE);
      declare(jetfs, "jets");

      // FinalState of prompt photons and bare muons and electrons in the event
      PromptFinalState photons(Cuts::abspid == PID::PHOTON);
      PromptFinalState bare_leps(Cuts::abspid == PID::MUON || Cuts::abspid == PID::ELECTRON);

      // Dress the prompt bare leptons with prompt photons within dR < 0.1,
      // and apply some fiducial cuts on the dressed leptons
      Cut lepton_cuts = Cuts::abseta < 2.4 && Cuts::pT > 25*GeV;
      DressedLeptons dressed_leps(photons, bare_leps, 0.1, lepton_cuts);
      declare(dressed_leps, "leptons");

      // Missing momentum
      /// Out of acceptance particles treat as invisible
      VetoedFinalState fs_onlyinacc(fs, (Cuts::abspid == PID::MUON && Cuts::abseta > 2.4) || 
                                    (Cuts::abspid == PID::PHOTON && Cuts::abseta > 3.0) || 
                                    (Cuts::abspid == PID::ELECTRON && Cuts::abseta > 3.0));
      declare(MissingMomentum(fs_onlyinacc), "MET");

      // Book histograms
      // specify custom binning
      /// Book histograms with variable bin size
      book(_h["NJets"], "NJets", 10, 0.5, 10.5);

      vector<double> binedges_Ystar = {0.0, 0.5, 1.0, 1.5, 2.0};
      vector<double> binedges_Yboost = {0.0, 0.5, 1.0, 1.5, 2.0};
      
      vector<double> binedges_ZPt;
      vector<double> binedges_PhiStarEta;

      for(auto _ystar: binedges_Ystar){
        for(auto _yboost: binedges_Yboost){
          if(_ystar + _yboost > 2.) continue;
          // extreme bin
          if(_ystar>=2.0 && _yboost<0.5){
            binedges_ZPt = {25., 30., 40., 50., 70., 90., 110., 150., 250.};
            binedges_PhiStarEta = {0.4, 0.6, 0.8, 1.0, 5.};
          }
          // central bins
          else if((_ystar<0.5 && _yboost<2.) || (_ystar<1. && _yboost<1.5) || (_ystar<1.5 && _yboost<1.)){
            binedges_ZPt = {25., 30., 35., 40., 50., 60., 70., 80., 90., 100., 110., 130., 150., 170., 190., 220., 250., 400., 1000.};
            binedges_PhiStarEta = {0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2, 1.5, 2., 3., 4., 5., 7., 10., 15., 20., 30., 50.};
          }
          // edge bins
          else {
            binedges_ZPt = {25., 30., 35., 40., 45., 50., 60., 70., 80., 90., 100., 110., 130., 150., 170., 190., 250., 1000.};
            binedges_PhiStarEta = {0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2, 1.5, 2., 3., 5., 10., 15., 50.};
          }

          string _hist_ZPt_ident = "ZPtYs"+to_string(_ystar)+"Yb"+to_string(_yboost);
          string _hist_ZPt_name = _hist_ZPt_ident;
          string _hist_PhiStarEta_ident = "PhiStarEtaYs"+to_string(_ystar)+"Yb"+to_string(_yboost);
          string _hist_PhiStarEta_name = _hist_PhiStarEta_ident;
          
          book(_h[_hist_ZPt_ident], _hist_ZPt_name, binedges_ZPt);
          book(_h[_hist_PhiStarEta_ident], _hist_PhiStarEta_name, binedges_PhiStarEta);

          cout << "Finished initialization" << endl;

        }
      }

    }


    /// Perform the per-event analysis
    void analyze(const Event& event) {

      // Retrieve dressed leptons, sorted by pT
      vector<DressedLepton> leptons = apply<DressedLeptons>(event, "leptons").dressedLeptons();
      MSG_DEBUG("Lepton multiplicity = " << leptons.size());

      // discard events with less than two muons
      if (leptons.size() < 2) vetoEvent;

      // Retrieve clustered jets, sorted by pT, with a minimum pT cut
      Jets jets = apply<FastJets>(event, "jets").jetsByPt(Cuts::absrap < 2.4 && Cuts::pT > 10*GeV);

      // Remove all jets within dR < 0.3 of a dressed lepton
      idiscardIfAnyDeltaRLess(jets, leptons, 0.3);
      MSG_DEBUG("Jet multiplicity = " << jets.size());

      // Require at least one hard jetcout << "Finished initialization" << endl;
      if (jets.empty()) vetoEvent;      
      if (jets.at(0).pT() <= 20*GeV) vetoEvent;

      // Require at least two opposite sign leptons compatible with Z-boson mass and keep the pair closest to Zboson mass
      bool _bosoncandidateexists = false;
      double _massdiff = 20*GeV;
      DressedLepton _muon = leptons.at(0);
      DressedLepton _antimuon = leptons.at(0);

      for (unsigned int it = 1; it < leptons.size(); ++it) {
        for (unsigned int jt = 0; jt < it; ++jt) {
          double _candidatemass = (leptons.at(it).mom() + leptons.at(jt).mom()).mass();
          if (leptons.at(it).pid() == -leptons.at(jt).pid() && abs(_candidatemass - 91.1876*GeV) < _massdiff) {
            _bosoncandidateexists = true;
            _massdiff = abs(_candidatemass - 91.1876*GeV);
            if (leptons.at(it).pid() > 0) {
              _muon = leptons.at(it);
              _antimuon = leptons.at(jt);
            }
            else {
              _muon = leptons.at(jt);
              _antimuon = leptons.at(it);
            }
          }
          else continue;
        }
      }

      if (!(_bosoncandidateexists)) vetoEvent;


      // Fill jet related histograms
      _h["NJets"] -> fill(jets.size());

      // Fill triple differential histograms
      const double rap_Z = (_muon.mom() + _antimuon.mom()).rap();
      const double pT_Z = (_muon.mom() + _antimuon.mom()).pT()/GeV;

      const double thetastar = acos(tanh((_antimuon.mom().eta() - _muon.mom().eta())/2));
      const double phistareta = tan(HALFPI - (_antimuon.mom().phi() - _muon.mom().phi())/2)*sin(thetastar);

      const double rap_Jet1 = jets.at(0).rap();  

      const double rap_star = 0.5 * abs(rap_Z - rap_Jet1);
      const double rap_boost = 0.5 * abs(rap_Z + rap_Jet1);

      /// Fill signal histograms
      vector<double> binedges_Ystar = {0.5, 1.0, 1.5, 2.0, 2.5};
      vector<double> binedges_Yboost = {0.5, 1.0, 1.5, 2.0, 2.5};

      for(auto _ystar: binedges_Ystar){
        for(auto _yboost: binedges_Yboost){
          if(_ystar + _yboost > 3.) continue;
          if((rap_star < _ystar) && (rap_boost < _yboost)){

            // The histograms are named with the left bin border
            _ystar -= 0.5;
            _yboost -= 0.5;

            string _hist_ZPt_ident = "ZPtYs"+to_string(_ystar)+"Yb"+to_string(_yboost);
            string _hist_PhiStarEta_ident = "PhiStarEtaYs"+to_string(_ystar)+"Yb"+to_string(_yboost);

            // Fill the histograms
            _h[_hist_ZPt_ident]->fill(pT_Z);
            _h[_hist_PhiStarEta_ident]->fill(phistareta); 

            // End the loop, when a matching bin has been found
            goto theEnd;
          }
          else continue;
        }
      }
      theEnd:;

      cout << "Finished analyzing event!" << endl;

    }


    /// Normalise histograms etc., after the run
    void finalize() {

      cout << "Starting finalizing ..." << endl;

      /// Normalise histograms
      //const double sf = crossSection()/picobarn/sumW();
      const double sf = 1.0;
      
      for(auto const& _hist : _h){
        normalize(_hist.second, sf);
      }

      cout << "Finished finalizing!" << endl;

    }

    ///@}


    /// @name Histograms
    ///@{
    map<string,Histo1DPtr> _h;
    ///@}


  };


  DECLARE_RIVET_PLUGIN(ZplusJet_Partonic_3);

}
