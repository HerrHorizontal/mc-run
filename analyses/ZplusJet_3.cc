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
  class ZplusJet_3 : public Analysis {
  public:

    /// Constructor
    DEFAULT_RIVET_ANALYSIS_CTOR(ZplusJet_3);


    /// @name Analysis methods
    ///@{

    /// Book histograms and initialise projections before the run
    void init() {

      MSG_INFO(
        "Analysis cuts: \n" 
        << "\tminimum jet pt for jet definition: " << _jetpt << "\n"
        << "\tminimum jet1 pt: " << _minjet1pt << "\n"
        << "\tjet rapidity cut: " << _maxabsjetrap << "\n"
        << "\tmaximum number of leptons: " << _maxnleptons << "\n"
        << "\tminimum lepton pt: " << _minleptonpt << "\n"
        << "\tlepton eta cut: " << _maxleptoneta << "\n"
        << "\tZ-mass window +/-: " << _massdiff << "\n"
        << "\tminimum Z pt: " << _minptZ << "\n"
      );

      // Initialise and register projections

      // The basic final-state projection:
      // all final-state particles within
      // the given eta acceptance
      const FinalState fs(Cuts::abseta < 5. && Cuts::pT > 100*MeV);
      //const ChargedFinalState cfs(fs);


      // The final-state particles declared above are clustered using FastJet with
      // the anti-kT algorithm and a jet-radius parameter 0.4
      // neutrinos are excluded from the clustering
      FastJets jetfsak4(fs, FastJets::ANTIKT, 0.4, JetAlg::Muons::ALL, JetAlg::Invisibles::NONE);
      declare(jetfsak4, "jetsAK4");
      FastJets jetfsak8(fs, FastJets::ANTIKT, 0.8, JetAlg::Muons::ALL, JetAlg::Invisibles::NONE);
      declare(jetfsak8, "jetsAK8");

      // FinalState of prompt photons and bare muons and electrons in the event
      PromptFinalState photons(Cuts::abspid == PID::PHOTON);
      PromptFinalState bare_leps(Cuts::abspid == PID::MUON || Cuts::abspid == PID::ELECTRON);

      // Dress the prompt bare leptons with prompt photons within dR < 0.1,
      // and apply some fiducial cuts on the dressed leptons
      Cut lepton_cuts = Cuts::abseta < _maxleptoneta && Cuts::pT > _minleptonpt;
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

      vector<double> binedges_Ystar = {0.0, 0.5, 1.0, 1.5, 2.0};
      vector<double> binedges_Yboost = {0.0, 0.5, 1.0, 1.5, 2.0};
      
      vector<double> binedges_ZPt;
      vector<double> binedges_PhiStarEta;

      for(string _jettype: {"AK4","AK8"}){
        book(_h["NJets"+_jettype], "NJets"+_jettype, 11, -0.5, 10.5);
        for(auto _ystar: binedges_Ystar){
          for(auto _yboost: binedges_Yboost){
            if(_ystar + _yboost > 2.) continue;
            // extreme bin
            if(_ystar>=2.0 && _yboost<0.5){
              binedges_ZPt = {25., 30., 40., 50., 70., 90., 110., 150., 250.};
              binedges_PhiStarEta = {0.2, 0.4, 0.6, 0.8, 1.0, 5.};
            }
            // central bins
            else if((_ystar<0.5 && _yboost<2.) || (_ystar<1. && _yboost<1.5) || (_ystar<1.5 && _yboost<1.)){
              binedges_ZPt = {25., 30., 35., 40., 50., 60., 70., 80., 90., 100., 110., 130., 150., 170., 190., 220., 250., 400., 1000.};
              binedges_PhiStarEta = {0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2, 1.5, 2., 3., 4., 5., 7., 10., 15., 20., 30., 50.};
            }
            // edge bins
            else {
              binedges_ZPt = {25., 30., 35., 40., 45., 50., 60., 70., 80., 90., 100., 110., 130., 150., 170., 190., 250., 1000.};
              binedges_PhiStarEta = {0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2, 1.5, 2., 3., 5., 10., 15., 50.};
            }

            string _hist_ZPt_ident = "ZPt"+_jettype+"Ys"+to_string(_ystar)+"Yb"+to_string(_yboost);
            string _hist_ZPt_name = _hist_ZPt_ident;
            string _hist_PhiStarEta_ident = "PhiStarEta"+_jettype+"Ys"+to_string(_ystar)+"Yb"+to_string(_yboost);
            string _hist_PhiStarEta_name = _hist_PhiStarEta_ident;
            
            book(_h[_hist_ZPt_ident], _hist_ZPt_name, binedges_ZPt);
            book(_h[_hist_PhiStarEta_ident], _hist_PhiStarEta_name, binedges_PhiStarEta);

          }
        }
      }

      MSG_INFO(
        "Booked " << _h.size() << " histograms"
      );
      if (getLog().isActive(Log::DEBUG)) {
        MSG_DEBUG("Histograms:");
        for (auto h: _h) {
          MSG_DEBUG("\t" << h.first);
        }
      }
    }


    /// Perform the per-event analysis
    void analyze(const Event& event) {

      // Retrieve dressed leptons, sorted by pT
      vector<DressedLepton> leptons = apply<DressedLeptons>(event, "leptons").dressedLeptons();

      // discard events with less than two and more than maximum number of leptons
      if (leptons.size() < 2) vetoEvent;
      if (leptons.size() > _maxnleptons) vetoEvent;
      MSG_DEBUG("Found " << leptons.size() << " leptons");
      for (auto lep: leptons) {
        MSG_DEBUG("\tlepton pt: " << lep.pT());
        MSG_DEBUG("\tlepton y: " << lep.rap());
      }

      // Retrieve clustered jets, sorted by pT, with a minimum pT cut
      map<string,Jets> _jetcollections;
      _jetcollections["AK4"] = apply<FastJets>(event, "jetsAK4").jetsByPt(Cuts::absrap < _maxabsjetrap && Cuts::pT > _jetpt);
      _jetcollections["AK8"] = apply<FastJets>(event, "jetsAK8").jetsByPt(Cuts::absrap < _maxabsjetrap && Cuts::pT > _jetpt);

      // Require at least one jet in any jet collection with a minimum pT 
      bool jet1pass = false;

      set<string> _jetcollectionstoerase;

      for (auto& jets: _jetcollections) {
        // Remove all jets within dR < 0.3 of a dressed lepton
        idiscardIfAnyDeltaRLess(jets.second, leptons, _lepCleaningDeltaR);
        MSG_DEBUG("After lepton cleaning jet multiplicity " << jets.first << "= " << jets.second.size());
        for (auto jet: jets.second) {
          MSG_DEBUG("\tjet pt: " << jet.pT()/GeV);
          MSG_DEBUG("\tjet y: " << jet.rap());
        }

        // Require at least one hard jet
        if (!jets.second.empty()) {
          if (jets.second.at(0).pT() > _minjet1pt) {
            MSG_DEBUG("Hardest " << jets.first << " jet pt: " << jets.second.at(0).pT());
            jet1pass = true;
          } else {
            _jetcollectionstoerase.insert(jets.first);
          }
        }
        else {
            _jetcollectionstoerase.insert(jets.first);
        }
      }

      if (!(jet1pass)) vetoEvent;

      for (string c: _jetcollectionstoerase) {
        _jetcollections.erase(c);
      }
      MSG_DEBUG("Remaining jet collections:");
      if (getLog().isActive(Log::DEBUG)) {
        for (auto jc: _jetcollections) {
          MSG_DEBUG("\t" << jc.first);
        }
      }

      // Require at least two opposite sign leptons compatible with Z-boson mass and keep the pair closest to Zboson mass
      bool bosoncandidateexists = false;
      double massdiff = _massdiff;
      DressedLepton muon = leptons.at(0);
      DressedLepton antimuon = leptons.at(0);

      for (unsigned int it = 1; it < leptons.size(); ++it) {
        for (unsigned int jt = 0; jt < it; ++jt) {
          double candidatemass = (leptons.at(it).mom() + leptons.at(jt).mom()).mass();
          if (leptons.at(it).pid() == -leptons.at(jt).pid() && abs(candidatemass - 91.1876*GeV) < massdiff) {
            bosoncandidateexists = true;
            massdiff = abs(candidatemass - 91.1876*GeV);
            if (leptons.at(it).pid() > 0) {
              muon = leptons.at(it);
              antimuon = leptons.at(jt);
            }
            else {
              muon = leptons.at(jt);
              antimuon = leptons.at(it);
            }
          }
          else continue;
        }
      }

      if (!(bosoncandidateexists)) vetoEvent;
      MSG_DEBUG("Found Z-boson candidate with mass " << (muon.mom() + antimuon.mom()).mass()/GeV << "GeV");

      // Fill histograms with selected events
      const double rap_Z = (muon.mom() + antimuon.mom()).rap();
      const double pT_Z = (muon.mom() + antimuon.mom()).pT()/GeV;
      if (pT_Z <= _minptZ) vetoEvent;
      MSG_DEBUG("\tZ-boson pt: " << pT_Z);
      MSG_DEBUG("\tZ-boson y: " << rap_Z);

      const double thetastar = acos(tanh((antimuon.mom().eta() - muon.mom().eta())/2));
      const double phistareta = tan(HALFPI - (antimuon.mom().phi() - muon.mom().phi())/2)*sin(thetastar);
      MSG_DEBUG("\tphi*eta: " << phistareta);

      /// Fill signal histograms
      vector<double> binedges_Ystar = {0.5, 1.0, 1.5, 2.0, 2.5};
      vector<double> binedges_Yboost = {0.5, 1.0, 1.5, 2.0, 2.5};

      for (auto jets: _jetcollections) {
        // Fill jet related histograms
        _h["NJets"+jets.first] -> fill(jets.second.size());
        
        double rap_Jet1 = jets.second.at(0).rap();

        double rap_star = 0.5 * abs(rap_Z - rap_Jet1);
        double rap_boost = 0.5 * abs(rap_Z + rap_Jet1);

        for(auto _ystar: binedges_Ystar){
          for(auto _yboost: binedges_Yboost){
            if(_ystar + _yboost > 3.) continue;
            if((rap_star < _ystar) && (rap_boost < _yboost)){

              // The histograms are named with the left bin border
              double _ystar_label = _ystar - 0.5;
              double _yboost_label = _yboost - 0.5;

              MSG_DEBUG("Selected y*-yb bin: Ys" << _ystar_label << "Yb" << _yboost_label);
              string _hist_ZPt_ident = "ZPt"+jets.first+"Ys"+to_string(_ystar_label)+"Yb"+to_string(_yboost_label);
              string _hist_PhiStarEta_ident = "PhiStarEta"+jets.first+"Ys"+to_string(_ystar_label)+"Yb"+to_string(_yboost_label);

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
      }
    }


    /// Normalise histograms etc., after the run
    void finalize() {

      /// Normalise histograms
      const double sf = crossSection()/picobarn/sumOfWeights();
      // const double sf = 1.0;
      
      for(auto const& _hist : _h){
        scale(_hist.second, sf);
      }

    }

    ///@}


    /// @name Histograms
    ///@{
    map<string,Histo1DPtr> _h;
    ///@}

    /// @name Selections
    ///@{
    const double _massdiff = 20*GeV; // mass window around Z-boson PDG mass
    const double _minptZ = 25*GeV;
    const double _minjet1pt = 20*GeV; // minimum pT of hardest jet
    const double _jetpt = 10*GeV; // minimum jet pT
    const double _maxabsjetrap = 2.4; // maximum absolute jet y
    const size_t _maxnleptons = numeric_limits<size_t>::max(); // maximium number of leptons
    const double _maxleptoneta = 2.4; // maximum absolute lepton eta
    const double _minleptonpt = 25*GeV; // minimum lepton pT
    const double _lepCleaningDeltaR = 0.3; // DeltaR between leptons and jets to clean former from latter
    ///@}

    const double UndefinedDouble = -9999.9999;


  };


  DECLARE_RIVET_PLUGIN(ZplusJet_3);

}
