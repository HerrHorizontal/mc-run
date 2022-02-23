
//this program plots all NP Correction factors on single canvas
#include <iostream>
#include "cmath"

using namespace std;
void NP_full_AK4_mass()

int main () {
    
    gStyle->SetOptStat(0); 
    gStyle->SetOptFit(0); 

    TFile *f1 = TFile::Open("Dijets_cms.root");      // Root file with Hadronization On
    TFile *f2 = TFile::Open("Dijets_cms_nohad.root");    // Root file with Hadronization Off
    TFile *NP = new TFile("NP_full_AK4_mass.root","RECREATE");

    TF1* f3 = new TF1("f3","(([0]/TMath::Exp(x^[1]))+[2])", 160.,10050.); 

    ROOT::Math::MinimizerOptions::SetDefaultMaxFunctionCalls(20000);
    f3->SetParameter(0,9);
    f3->SetParameter(1,-0.5);
    f3->SetParameter(2,-0.1);
    f3->SetLineColor(1);
    f3->SetLineStyle(3);

    TH1D *h[5], *k[5], *hNP[5];
    int N[5] = {28, 28, 28, 14, 14};

    const char *titleIN[5] = {"/CMS_2D_Dijet_Mass_AK4_AK8_Rivet3/ak4_y1", "/CMS_2D_Dijet_Mass_AK4_AK8_Rivet3/ak4_y2", "/CMS_2D_Dijet_Mass_AK4_AK8_Rivet3/ak4_y3","/CMS_2D_Dijet_Mass_AK4_AK8_Rivet3/ak4_y4","/CMS_2D_Dijet_Mass_AK4_AK8_Rivet3/ak4_y5"};

    const char *titleO[5] = {"ak4_y1","ak4_y2","ak4_y3","ak4_y4","ak4_y5"};

    const double new_bins[5][29] = {{
        160,  200,  249,  306,  372,  449,  539,  641,
        756,  887,  1029, 1187, 1361, 1556, 1769, 2008,
        2273, 2572, 2915, 3306, 3754, 4244, 4805, 5374,
        6094, 6908, 7861, 8929, 10050},{
        160,  200,  249,  306,  372,  449,  539,  641,
        756,  887,  1029, 1187, 1361, 1556, 1769, 2008,
        2273, 2572, 2915, 3306, 3754, 4244, 4805, 5374,
        6094, 6908, 7861, 8929, 10050},{
        160,  200,  249,  306,  372,  449,  539,  641,
        756,  887,  1029, 1187, 1361, 1556, 1769, 2008,
        2273, 2572, 2915, 3306, 3754, 4244, 4805, 5374,
        6094, 6908, 7861, 8929, 10050},{
        160,  249,  372,  539,  756,  1029, 1361, 1769,
        2273, 2915, 3754, 4805, 6094, 7861, 10050},{
        160,  249,  372,  539,  756,  1029, 1361, 1769,
        2273, 2915, 3754, 4805, 6094, 7861, 10050}
    };

    const char *hist_title[5] = {"|y|_{max} < 0.5","0.5 #leq |y|_{max} < 1.0","1.0 #leq |y|_{max} < 1.5","1.5 #leq |y|_{max} < 2.0","2.0 #leq |y|_{max} < 2.5"};

    for (int i = 0 ; i <5; i++) {
        if ( i == 3) {
            f3->SetParameter(0,2);
            f3->SetParameter(1,-0.02);
            f3->SetParameter(2,0.01);
        }
        else if (i == 4) {
            f3->SetParameter(0,4);
            f3->SetParameter(1,-0.002);
            f3->SetParameter(2,-0.01);
        }

        f1->GetObject(titleIN[i],h[i]);
        f2->GetObject(titleIN[i],k[i]);
        hNP[i] = new TH1D(titleO[i],hist_title[i],N[i],new_bins[i]);

        h[i]->Divide(k[i]);
        h[i]->Fit("f3","M"); 
        hNP[i]->Sumw2();
        hNP[i]->SetTitleFont(42);
        hNP[i]->GetYaxis()->SetRangeUser(0.86, 1.19);
        hNP[i]->GetXaxis()->SetTitleOffset(1);
        hNP[i]->GetYaxis()->SetTitleOffset(1);
        hNP[i]->GetYaxis()->SetTitle("NP correction");
        hNP[i]->GetXaxis()->SetTitle("m(GeV)");

        Double_t x1[N[i]], z1[N[i]];
        for (int j = 0.; j < N[i]; j++) {
            x1[j] = hNP[i]->GetBinCenter(j+1);
            z1[j] =  f3->Eval(x1[j]); 
            hNP[i]->SetBinContent(j+1,z1[j]);
        } 

        hNP[i]->Draw("hist");
        hNP[i]->Write();
    }

    //############################################
    //      CANVAS				     #
    //############################################
    TCanvas *c1 = new TCanvas("c1","NP Correction Factor");
    c1->SetCanvasSize(2000, 2000);
    c1->SetWindowSize(1000, 1000);
    c1->Divide(1,5,1e-17,1e-17);

    //canvas loop starts
    for (int k = 0.; k<5; k++) {
        c1->cd(k+1);
        hNP[k]->SetTitle("");
        hNP[k]->GetXaxis()->SetTitle("");
        hNP[k]->GetYaxis()->SetTitle("");
        //hNP[k]->GetXaxis()->SetMoreLogLabels();
        //hNP[k]->GetXaxis()->SetRangeUser(306, 10000);
        hNP[k]->GetYaxis()->SetLabelSize(0.07); 
        hNP[k]->GetXaxis()->SetLabelSize(0.07);  
        if (k == 0)
        {
        hNP[k]->GetYaxis()->SetTitleSize(0.10);
        hNP[k]->GetYaxis()->SetTitleOffset(0.3);
        hNP[k]->GetYaxis()->SetTitle("NP correction");
        }
        if (k == 4)
        {
        hNP[k]->GetXaxis()->SetTitleSize(0.07); 
        hNP[k]->GetXaxis()->SetTitleOffset(1);
        hNP[k]->GetXaxis()->SetTitle("    m(GeV)");
        gPad->SetBottomMargin(0.18);
        }

        hNP[k]->Draw("hist][");

        h[k]->SetLineColor(1);
        h[k]->SetMarkerStyle(8);
        h[k]->SetMarkerSize(2);
        h[k]->SetMarkerColor(1);
        h[k]->Draw("same");

        gPad->SetTickx(1);
        gPad->SetTicky(1);
        gPad->SetRightMargin(0.02);
        //gPad->SetLogx(1);
        TPaveText *pt1 = new TPaveText(0.1865,0.75,0.4145,0.865,"blNDC"); 
        pt1->SetBorderSize(0);
        pt1->SetFillColor(0);
        pt1->SetFillStyle(0);
        pt1->SetTextFont(42);
        TText *pt_LaTex1 = pt1->AddText(hist_title[k]);
        pt1->Draw();   
            pt1 = new TPaveText(0.16,0.66,0.414,0.7625,"blNDC");
        pt1->SetBorderSize(0);
        pt1->SetFillColor(0);
        pt1->SetFillStyle(0);
        pt1->SetTextFont(42);
        pt_LaTex1 = pt1->AddText("R = 0.4, 2D, LO");
        pt1->Draw();
    } //canvas loop ends

    c1->Draw();
    c1->Update();
    c1->SaveAs("NP_full_AK4_mass_fit.pdf");


    NP->Write();
    NP->Close();

}
