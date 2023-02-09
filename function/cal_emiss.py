# -*- coding: utf-8 -*-
"""
Created on Fri Jul  2 14:29:07 2021

@author: DELL
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# C=1000000; H=4775; UC=265; UB=500; Sum_j_xij=2354185.9744656; Sum_j_DBxij=51678097.7206588; Dccs=295; CY=1995; RY=2030
# # Emiss_PP(C, H)
# Emiss_BE(C, H, UB, Sum_j_xij, Sum_j_DBxij)
# Emiss_BE1(C, H, UB, Sum_j_xij, Sum_j_DBxij)
# # Emiss_CCS(C, H)
# Emiss_BECCS(C, H, UB, Sum_j_xij, Sum_j_DBxij)
# Emiss_BECCS_origin(C,H,UB,Sum_j_xij,Sum_j_DBxij)
# Emiss_BECCS(C, H, UB, Sum_j_xij, Sum_j_DBxij)
# Emiss_BE(C, H, UB, Sum_j_xij, Sum_j_DBxij)
# Emiss_BE_origin(C, H, UB, Sum_j_xij, Sum_j_DBxij)

scale_Bio = pow(10,9)

def Emiss_PP(C, H, OY, RY, unitCoal):
    # emiss = 0.0010916 * C * H
    # emiss = (275.1 + 14.8 + 801.7) * C * H * 0.1 / pow(10,6)
    emiss = (275.1 + 14.8) * C * H / pow(10,6) + unitCoal* 2.7725 * C * H /pow(10,6) # unit: tonne
    if RY - OY > 40:
        emiss = 0
    return emiss

def Emiss_BE(C, H, Sum_j_xij_kwh, Sum_j_DBxij, OY, RY, unitCoal):
    cofiringRatio = Sum_j_xij_kwh * scale_Bio / (C*H)
    # coalEmiss = (275.1 + 14.8 + 801.7) * C * H * (1-cofiringRatio) / pow(10,6)
    coalEmiss = (275.1 + 14.8) * C * H * (1-cofiringRatio) / pow(10,6) + unitCoal* 2.7725 * C * H * (1-cofiringRatio) / pow(10,6)
    bioEmiss = (2.36 + 1.1 + 0.295 + 2.457) * Sum_j_xij_kwh / pow(10,6) * scale_Bio  + 0.009 * Sum_j_DBxij / pow(10,6) * scale_Bio
    emiss = coalEmiss + bioEmiss
    if RY - OY > 40:
        emiss = 0
    return emiss

def Emiss_CCS(C, H, OY, RY, unitCoal):    
    # emiss = (275.1 + 14.8 + 801.7) * C * H * 0.1 / pow(10,6)
    emiss = (275.1 + 14.8) * C * H * 0.1 / pow(10,6) + unitCoal* 2.7725 * C * H * 0.1 / pow(10,6)
    if RY - OY > 40:
        emiss = 0
    return emiss

def Emiss_BECCS(C,H,Sum_j_xij_kwh,Sum_j_DBxij, OY, RY, unitCoal):

    cofiringRatio = Sum_j_xij_kwh * scale_Bio / (C*H)
    # coalEmiss = (275.1 + 14.8 + 0.1 * 801.7) * C * H * (1-cofiringRatio) / pow(10,6) 
    coalEmiss = (275.1 + 14.8) * C * H * (1-cofiringRatio) / pow(10,6) + (0.1 * unitCoal* 2.7725) * C * H * (1-cofiringRatio) / pow(10,6) 
    # coal_CCS = 801.7 * 0.9 * C * H / pow(10,6) # capture 90% emission
    bio_processEmiss = (2.36 + 1.1 + 0.295 + 2.457) * Sum_j_xij_kwh / pow(10,6) * scale_Bio + 0.009 * Sum_j_DBxij / pow(10,6) * scale_Bio
    bio_absorb = 375.72 * Sum_j_xij_kwh * 0.9 / pow(10,6)  * scale_Bio # capture 90% emission
    # bio_absorb = 0
    # emiss = coalEmiss - coal_CCS + bio_processEmiss - bio_absorb
    emiss = coalEmiss + bio_processEmiss - bio_absorb
    if RY - OY > 40:
        emiss = 0
    return emiss

def Emiss_Retire():
    emiss = 0
    return emiss


