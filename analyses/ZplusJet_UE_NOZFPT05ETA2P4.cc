#include "Rivet/Analysis.hh"
#include "Rivet/Projections/ChargedFinalState.hh"
#include "Rivet/Projections/DressedLeptons.hh"
#include "Rivet/Projections/FastJets.hh"
#include "Rivet/Projections/FinalState.hh"
#include "Rivet/Projections/JetAlg.hh"
#include "Rivet/Projections/PromptFinalState.hh"
#include "Rivet/Projections/VetoedFinalState.hh"

namespace Rivet {

class ZplusJet_UE_NOZFPT05ETA2P4 : public Analysis {
public:
  DEFAULT_RIVET_ANALYSIS_CTOR(ZplusJet_UE_NOZFPT05ETA2P4);

  void init() {

    const FinalState fs(Cuts::abseta < etamax && Cuts::pT > 500 * MeV);
    declare(fs, "fs");

    const ChargedFinalState cfs(Cuts::abseta < etamax && Cuts::pT > 500 * MeV);
    declare(cfs, "cfs");

    FastJets jetfsak4(fs, FastJets::ANTIKT, 0.4, JetAlg::Muons::ALL,
                      JetAlg::Invisibles::NONE);
    declare(jetfsak4, "jets");

    PromptFinalState photons(Cuts::abspid == PID::PHOTON);
    PromptFinalState bare_leps(Cuts::abspid == PID::MUON ||
                               Cuts::abspid == PID::ELECTRON);

    Cut lepton_cuts = Cuts::abseta < _maxleptoneta && Cuts::pT > _minleptonpt;
    DressedLeptons dressed_leps(photons, bare_leps, 0.1, lepton_cuts);
    declare(dressed_leps, "leptons");

    vector<double> binedges_ZPt;
    vector<double> binedges_Ystar = {0.5, 1.0, 1.5, 2.0, 2.5};
    vector<double> binedges_Yboost = {0.5, 1.0, 1.5, 2.0, 2.5};
    binedges_ZPt = {5.,  10., 15., 20., 25., 30., 35., 40., 45., 50.,
                    55., 60., 65., 70., 75., 80., 85., 90., 95., 100.};

    book(_p["NCharged_Towards_Incl"], "NCharged_Towards_Incl", binedges_ZPt);
    book(_p["NCharged_Transverse_Incl"], "NCharged_Transverse_Incl", binedges_ZPt);
    book(_p["NCharged_Away_Incl"], "NCharged_Away_Incl", binedges_ZPt);
    book(_p["pTsum_Towards_Incl"], "pTsum_Towards_Incl", binedges_ZPt);
    book(_p["pTsum_Transverse_Incl"], "pTsum_Transverse_Incl", binedges_ZPt);
    book(_p["pTsum_Away_Incl"], "pTsum_Away_Incl", binedges_ZPt);

    for (auto _ystar : binedges_Ystar) {
      for (auto _yboost : binedges_Yboost) {
        if (_ystar + _yboost > 3.0)
          continue;

        string _profile_Nch_Towards = string("NCharged_Towards") + "_Ys=" +
                                      to_string(_ystar) + "_Yb=" +
                                      to_string(_yboost);
        string _profile_Nch_Towards_name = _profile_Nch_Towards;
        string _profile_Nch_Transverse = string("NCharged_Transverse") + "_Ys=" +
                                         to_string(_ystar) + "_Yb=" +
                                         to_string(_yboost);
        string _profile_Nch_Transverse_name = _profile_Nch_Transverse;
        string _profile_Nch_Away = string("NCharged_Away") + "_Ys=" + to_string(_ystar) +
                                   "_Yb=" + to_string(_yboost);
        string _profile_Nch_Away_name = _profile_Nch_Away;

        string _profile_pTsum_Towards = string("pTsum_Towards") + "_Ys=" +
                                        to_string(_ystar) + "_Yb=" +
                                        to_string(_yboost);
        string _profile_pTsum_Towards_name = _profile_pTsum_Towards;
        string _profile_pTsum_Transverse = string("pTsum_Transverse") + "_Ys=" +
                                           to_string(_ystar) + "_Yb=" +
                                           to_string(_yboost);
        string _profile_pTsum_Transverse_name = _profile_pTsum_Transverse;
        string _profile_pTsum_Away = string("pTsum_Away") + "_Ys=" + to_string(_ystar) +
                                     "_Yb=" + to_string(_yboost);
        string _profile_pTsum_Away_name = _profile_pTsum_Away;


        book(_p[_profile_Nch_Towards], _profile_Nch_Towards_name, binedges_ZPt);
        book(_p[_profile_Nch_Transverse], _profile_Nch_Transverse_name,
             binedges_ZPt);
        book(_p[_profile_Nch_Away], _profile_Nch_Away_name, binedges_ZPt);
        book(_p[_profile_pTsum_Towards], _profile_pTsum_Towards_name,
             binedges_ZPt);
        book(_p[_profile_pTsum_Transverse], _profile_pTsum_Transverse_name,
             binedges_ZPt);
        book(_p[_profile_pTsum_Away], _profile_pTsum_Away_name, binedges_ZPt);
      }
    }


  }

  // Perform the per-event analysis
  void analyze(const Event &event) {

    // Retrieve dressed leptons, sorted by pT
    vector<DressedLepton> leptons =
        apply<DressedLeptons>(event, "leptons").dressedLeptons();

    // discard events with less than two and more than maximum number of leptons
    if (leptons.size() < 2)
      vetoEvent;
    if (leptons.size() > _maxnleptons)
      vetoEvent;
    MSG_DEBUG("Found " << leptons.size() << " leptons");
    for (auto lep : leptons) {
      MSG_DEBUG("\tlepton pt: " << lep.pT());
      MSG_DEBUG("\tlepton y: " << lep.rap());
    }

    // Retrieve clustered jets, sorted by pT, with a minimum pT cut
    Jets jets =
        apply<FastJets>(event, "jets")
            .jetsByPt(Cuts::absrap < _maxabsjetrap && Cuts::pT > _jetpt);
    if (jets.empty()) vetoEvent;
    if (jets.at(0).pt() < _minjet1pt) vetoEvent;

    bool bosoncandidateexists = false;
    double massdiff = _massdiff;
    DressedLepton muon = leptons.at(0);
    DressedLepton antimuon = leptons.at(0);

    for (unsigned int it = 1; it < leptons.size(); ++it) {
      for (unsigned int jt = 0; jt < it; ++jt) {
        double candidatemass =
            (leptons.at(it).mom() + leptons.at(jt).mom()).mass();
        if (leptons.at(it).pid() == -leptons.at(jt).pid() &&
            abs(candidatemass - 91.1876 * GeV) < massdiff) {
          bosoncandidateexists = true;
          massdiff = abs(candidatemass - 91.1876 * GeV);
          if (leptons.at(it).pid() > 0) {
            muon = leptons.at(it);
            antimuon = leptons.at(jt);
          } else {
            muon = leptons.at(jt);
            antimuon = leptons.at(it);
          }
        } else
          continue;
      }
    }

    if (!(bosoncandidateexists))
      vetoEvent;
    MSG_DEBUG("Found Z-boson candidate with mass "
              << (muon.mom() + antimuon.mom()).mass() / GeV << "GeV");

    double rap_Jet1 = jets.at(0).rap();
    const double rap_Z = (muon.mom() + antimuon.mom()).rap();
    double Zphi = (muon.mom() + antimuon.mom()).phi();
    const double pT_Z = (muon.mom() + antimuon.mom()).pT() / GeV;

    double rap_star = 0.5 * abs(rap_Z - rap_Jet1);
    double rap_boost = 0.5 * abs(rap_Z + rap_Jet1);

    if (rap_star + rap_boost > 3.0)
      vetoEvent;

    Particles particles =
        applyProjection<ChargedFinalState>(event, "cfs")
            .particlesByPt(Cuts::pT > 0.1 * GeV && Cuts::abseta < etamax);

    int nTowards = 0;
    int nTransverse = 0;
    int nAway = 0;
    double ptSumTowards = 0.;
    double ptSumTransverse = 0.;
    double ptSumAway = 0.;

    // Loop over particles
    for (const Particle &p : particles) {
      double dphi = fabs(deltaPhi(Zphi, p.phi()));
      double pT = p.pT();

      if (dphi < M_PI / 3) {
        nTowards++;
        ptSumTowards += pT;
      } else if (dphi < 2. * M_PI / 3) {
        nTransverse++;
        ptSumTransverse += pT;
      } else {
        nAway++;
        ptSumAway += pT;
      }

    }

    _p["NCharged_Towards_Incl"]->fill(pT_Z, 1. /area * nTowards);
    _p["NCharged_Transverse_Incl"]->fill(pT_Z, 1. /area * nTransverse);
    _p["NCharged_Away_Incl"]->fill(pT_Z, 1. /area * nAway);
    _p["pTsum_Towards_Incl"]->fill(pT_Z, 1. /area * ptSumTowards);
    _p["pTsum_Transverse_Incl"]->fill(pT_Z, 1. /area * ptSumTransverse);
    _p["pTsum_Away_Incl"]->fill(pT_Z, 1. /area * ptSumAway);

    bool breaking_loop_var = false;

    vector<double> binedges_Ystar = {0.5, 1.0, 1.5, 2.0, 2.5};
    vector<double> binedges_Yboost = {0.5, 1.0, 1.5, 2.0, 2.5};

    for (auto _ystar : binedges_Ystar) {
      for (auto _yboost : binedges_Yboost) {
        if (_ystar + _yboost > 3.0)
          continue;

        if ((_ystar - 0.5 < rap_star) && (rap_star <= _ystar) &&
            (_yboost - 0.5 < rap_boost) && (rap_boost <= _yboost)) {
          breaking_loop_var = true;

          double _ystar_label = _ystar;
          double _yboost_label = _yboost;

          string _profile_Nch_Towards = string("NCharged_Towards") + ("_Ys=") +
                                        to_string(_ystar_label) + "_Yb=" +
                                        to_string(_yboost_label);
          string _profile_Nch_Transverse = string("NCharged_Transverse") + "_Ys=" +
                                           to_string(_ystar_label) + "_Yb=" +
                                           to_string(_yboost_label);
          string _profile_Nch_Away = string("NCharged_Away") + "_Ys=" +
                                     to_string(_ystar_label) + "_Yb=" +
                                     to_string(_yboost_label);

          string _profile_pTsum_Towards = string("pTsum_Towards") + "_Ys=" +
                                          to_string(_ystar_label) + "_Yb=" +
                                          to_string(_yboost_label);
          string _profile_pTsum_Transverse = string("pTsum_Transverse") + "_Ys=" +
                                             to_string(_ystar_label) + "_Yb=" +
                                             to_string(_yboost_label);
          string _profile_pTsum_Away = string("pTsum_Away") + "_Ys=" +
                                       to_string(_ystar_label) + "_Yb=" +
                                       to_string(_yboost_label);

          // Fill the histograms
          _p[_profile_Nch_Towards]->fill(pT_Z, 1. /area * nTowards);
          _p[_profile_Nch_Transverse]->fill(pT_Z, 1. /area * nTransverse);
          _p[_profile_Nch_Away]->fill(pT_Z, 1. /area * nAway);
          _p[_profile_pTsum_Towards]->fill(pT_Z, 1. /area * ptSumTowards);
          _p[_profile_pTsum_Transverse]->fill(pT_Z, 1. /area * ptSumTransverse);
          _p[_profile_pTsum_Away]->fill(pT_Z, 1. /area * ptSumAway);
        }
      }
      if (breaking_loop_var)
        break;
    }
  }

  void finalize() {

  }

  map<string, Profile1DPtr> _p;
  
  //Jet cuts
  const double _maxabsjetrap = 2.4; // maximum absolute jet y
  const double _jetpt = 10 * GeV;   // minimum jet pT
  const double _minjet1pt =
      20 * GeV; // minimum pT of hardest jet. SHOULDN'T THE VALUE BE 25 GEV
                // BECAUSE OF MOMENTUM CONSERVATION?
  
  //lepton cuts
  const double _maxleptoneta = 2.4; // maximum absolute lepton eta
  const double _minleptonpt =
      25 * GeV; // Because of momentum conservation the Pt of Z-boson(lepton
                // pair) and that of the jet must be the same!
  const size_t _maxnleptons =
      numeric_limits<size_t>::max(); // maximium number of leptons, which is how
                                     // much ?
  // Z boson cuts
  const double _minptZ = 25 * GeV;   // minimum pT of the Z-Boson
  const double _massdiff = 20 * GeV; // mass window around Z-boson PDG mass

  // Particle cuts
  const double etamax=2.4; //maximal pseudorap value taken into consideration.

  //Normalization
  const double area = ((2. * etamax) * (2. * M_PI)) / 3.;


};

DECLARE_RIVET_PLUGIN(ZplusJet_UE_NOZFPT05ETA2P4);

} // namespace Rivet