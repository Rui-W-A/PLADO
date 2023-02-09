# -*- coding: utf-8 -*-
"""
Created on Tue Jun  7 11:15:06 2022

@author: vicke
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os


scale_Bio = pow(10,9)
# Parameters
# para = pd.read_csv('./function/params.csv', encoding = 'gbk')
dirPath = os.path.dirname(os.path.abspath(__file__))
paraPath = dirPath + "\\params.csv"
para = pd.read_csv(paraPath, encoding = 'gbk')
para = para.set_index('Parameter')
para_pp_capital = para.loc['PP-capital','Value']
para_pp_fixOM = para.loc['PP-fixOM','Value']
para_pp_variOM = para.loc['PP-variableOM', 'Value']
para_pp_coalCost = para.loc['PP-coalCost', 'Value']
para_be_capital = para.loc['BE-capital', 'Value']
para_be_fixOM = para.loc['BE-fixOM', 'Value']
para_be_variOM = para.loc['BE-variableOM', 'Value'] 
para_be_purchaseCost = para.loc['BE-purchaseCost', 'Value'] 
para_be_pretreatCost = para.loc['BE-pretreatCost', 'Value'] 
para_be_trans1 = para.loc['BE-transportCost1', 'Value']
para_be_trans2 = para.loc['BE-transportCost2', 'Value']
para_CCS_capital = para.loc['CCS-capital', 'Value'] 
para_CCS_captureCost = para.loc['CCS-captureCost', 'Value'] 
para_CCS_transCost = para.loc['CCS-transportCost', 'Value'] 
para_CCS_storageCost = para.loc['CCS-storageCost', 'Value'] 

def updateParas(columnName):
    # Parameters
    para = pd.read_csv(paraPath, encoding = 'gbk')
    para = para.set_index('Parameter')
    para_be_capital = para.loc['BE-capital', columnName] 
    para_be_purchaseCost = para.loc['BE-purchaseCost', columnName] 
    para_be_pretreatCost = para.loc['BE-pretreatCost', columnName] 
    para_CCS_capital = para.loc['CCS-capital', columnName] 
    para_CCS_captureCost = para.loc['CCS-captureCost', columnName] 
    para_CCS_transCost = para.loc['CCS-transportCost', columnName]  
    para_CCS_storageCost = para.loc['CCS-storageCost', columnName] 
    return [para_be_capital, para_be_purchaseCost, para_be_pretreatCost, para_CCS_capital, 
            para_CCS_captureCost, para_CCS_transCost, para_CCS_storageCost]


def LCOE_PP(C, H, operateYear, retrofitYear,columnName):
    
    para_be_capital, para_be_purchaseCost, para_be_pretreatCost, para_CCS_capital, para_CCS_captureCost, para_CCS_transCost, para_CCS_storageCost = updateParas(columnName)

    lcoe = 0.0
    
    if retrofitYear - operateYear + 1 >= 40: 
        lcoe = 0.0
        
    else: 
        r = 1 + 0.05  # rate
        lifespan = 40        
        
        Cap_PP = para_pp_capital * C # CAPEX = 3274 $/kw
        OM_PP = (para_pp_fixOM + para_pp_variOM) * C   # O & M = 41.66 + 31.35 $/kw
        Fuel_PP = C * H * para_pp_coalCost / pow(10,6)  # coal price = 11.45/MWh
        Debt_PP = Cap_PP * 0.0 # debt rate = 10% 
        D_PP = 0.05 * Cap_PP # depricition rate = 5%
        
        Elec = C * H
        r = 1 + 0.05
        lifespan = 40
        
        LF_0 = 0
        LF_1 = 0
        # lcoeFrame = np.zeros(shape = (lifespan, 2))
        for i in range(lifespan):
            cost_i = 0
            if i == 0:
                cost_i = (Cap_PP + OM_PP + Fuel_PP + Debt_PP) / pow(r, i+1)
            if i < 10 and i > 0:
                cost_i = (OM_PP + Fuel_PP + Debt_PP) / pow(r, i+1)
            if i >= 10 and i < lifespan-1:
                cost_i = (OM_PP + Fuel_PP) / pow(r, i+1)
            if i == lifespan - 1:
                cost_i = (OM_PP + Fuel_PP - D_PP) / pow(r, i+1)
                
            LF_0 += cost_i
            LF_1 += Elec / pow(r, i+1)

        lcoe = LF_0/LF_1 
        # print('PP:LF_O:%.2f, LF_1: %.2f' % (LF_0,LF_1))

    return lcoe

def LCOE_BE(C, H, Sum_j_xij_kwh, Sum_j_DBxij, operateYear, retrofitYear, lcoeFrame, columnName):
    
    para_be_capital, para_be_purchaseCost, para_be_pretreatCost, para_CCS_capital, para_CCS_captureCost, para_CCS_transCost, para_CCS_storageCost = updateParas(columnName)
    
    lcoe = 0.0
    
    if retrofitYear - operateYear + 1 >= 40:
        lcoe = 0.0
        
    else:
        # Cap_PP = 3274 * C # CAPEX = 3274 $/kw
        # OM_PP = (41.66 + 31.35) * C   # O & M = 41.66 + 31.35 $/kw
        Fuel_PP = C * H * para_pp_coalCost / pow(10,3)  # coal price = 11.45/MWh
        # Debt_PP = Cap_PP * 0.0 # debt rate = 10% 
        # D_PP = 0.05 * Cap_PP # depricition rate = 5%
        
        Cap_BE = para_be_capital * C
        OM_BE = (para_be_fixOM + para_be_variOM) * C
        Fuel_BE = (para_be_purchaseCost + para_be_pretreatCost + para_be_trans2) * C * H/pow(10,3) + Sum_j_DBxij * para_be_trans1 /pow(10,3) * scale_Bio  # xij = kwh/pow(10,6)
        Debt_BE = Cap_BE * 0.0
        D_BE = Cap_BE * 0.05
        
        add_Cap = Cap_BE
        add_OM = OM_BE
        Fuel_BE_PPpart = C * H * para_pp_coalCost / pow(10,3) - Sum_j_xij_kwh * para_pp_coalCost / pow(10,3) * scale_Bio # xij = kwh/pow(10,6)
        add_Fuel =  Fuel_BE_PPpart + Fuel_BE - Fuel_PP # coal reduction cost and biomass cost        
        add_Debt = Debt_BE
        add_D = D_BE
        
        Elec = C * H
        r = 1 + 0.05
        lifespan = 40
        
        n = retrofitYear - operateYear + 1
        # if n == 0: # [0:0] = no value
        #     n = n+1
        LF_0 = np.sum(lcoeFrame[:n, 0:5])
        LF_1 = np.sum(lcoeFrame[:, 5])
        # print('BE:LF_O:%.2f, LF_1: %.2f' % (LF_0,LF_1))
        
        # print(lcoeFrame[n:,0:5].shape)
        ori_cost_i = np.sum(lcoeFrame[n:,0:5], axis=1)
        # lcoeFrame = np.zeros(shape = (lifespan, 2))
        
        cost_i = 0.
        if n < lifespan:
            for i in range(n, lifespan):
                cost_i = ori_cost_i[0]
                if i == n:
                    # print('%.f, %.1f,%.1f, %.1f, %.1f'%(i,cost_i/pow(10,8), add_Cap,add_OM,add_Fuel))
                    cost_i = cost_i + (add_Cap + add_OM + add_Fuel) / pow(r, i+1)
                if i > n and i < (n+10):
                    # print('%.f, %.1f, %.1f, %.1f, %.1f'%(i,cost_i/pow(10,8),add_OM,add_Fuel,add_Debt))
                    cost_i = cost_i + (add_OM + add_Fuel + add_Debt) / pow(r, i+1)
                if i >= (n+10) and i < lifespan - 1:
                    # print('%.f, %.1f, %.1f, %.1f'%(i,cost_i/pow(10,8),add_OM,add_Fuel))
                    cost_i = cost_i + (add_OM + add_Fuel) / pow(r, i+1)
                if i == lifespan - 1:
                    # print('%.f, %.1f, %.1f, %.1f, %.1f'%(i,cost_i/pow(10,8),add_OM,add_Fuel,add_D))
                    cost_i = cost_i + (add_OM + add_Fuel - add_D) / pow(r, i+1)
                LF_0 += cost_i
            # print('cost in year: %.f, %.2f'%(i,cost_i))
         
        lcoe = LF_0/LF_1   
        
    return lcoe
            
def LCOE_CCS(C, H, Dccs, operateYear, retrofitYear, lcoeFrame, columnName):
    
    para_be_capital, para_be_purchaseCost, para_be_pretreatCost, para_CCS_capital, para_CCS_captureCost, para_CCS_transCost, para_CCS_storageCost = updateParas(columnName)
    
    lcoe = 0.0
    
    if retrofitYear - operateYear + 1 >= 40:
        lcoe = 0.0
    
    else:
        # Cap_PP = 3274 * C # CAPEX = 3274 $/kw
        # OM_PP = (41.66 + 31.35) * C   # O & M = 41.66 + 31.35 $/kw
        Fuel_PP = C * H * para_pp_coalCost / pow(10,3)  # coal price = 11.45/MWh
        # Debt_PP = Cap_PP * 0.0 # debt rate = 10% 
        # D_PP = 0.05 * Cap_PP # depricition rate = 5%
        
        Cap_CCS = para_CCS_capital * C
        Emiss_CO2 = C * H * 0.801 / pow(10,3)  # 0.801 t/MWh
        OM_CCS = Emiss_CO2 * (para_CCS_captureCost + para_CCS_storageCost) + Emiss_CO2 * Dccs * para_CCS_transCost
        Debt_CCS = 0.0 * Cap_CCS
        D_CCS = 0.05 * Cap_CCS
        
        add_Cap = Cap_CCS
        add_OM = OM_CCS
        add_Fuel = 0
        add_Debt = Debt_CCS
        add_D = D_CCS
    
        Elec = C * H
        r = 1 + 0.05
        lifespan = 40
        
        n = retrofitYear - operateYear + 1 # 发生改造的i 
        # if n == 0: # [0:0] = no value
        #     n = n+1
        LF_0 = np.sum(lcoeFrame[:n, 0:5])
        LF_1 = np.sum(lcoeFrame[:,5])
        # print('CCS:LF_O:%.2f, LF_1: %.2f' % (LF_0,LF_1))
        
        ori_cost_i = np.sum(lcoeFrame[n:,0:5], axis=1)
        cost_i = 0.
        if n < lifespan:
            for i in range(n, lifespan):
                cost_i = ori_cost_i[0]              
                if i == n:  # 改造第一年
                    cost_i = cost_i + (add_Cap + add_OM + add_Fuel) / pow(r, i+1)
                if i > n and i < (n+10) :
                    cost_i = cost_i + (add_OM + add_Fuel + add_Debt) / pow(r, i+1)
                if i >= (n + 10) and i < lifespan - 1:
                    cost_i = cost_i + (add_OM + add_Fuel) / pow(r, i+1)
                if i == lifespan - 1:
                    cost_i = cost_i + (add_OM + add_Fuel - add_D) / pow(r, i+1)
        
                LF_0 += cost_i            
    
        lcoe = LF_0/LF_1
    
    return lcoe

def LCOE_BECCS(C, H, Sum_j_xij_kwh, Sum_j_DBxij, Dccs, operateYear, retrofitYear, lcoeFrame, columnName):
    
    para_be_capital, para_be_purchaseCost, para_be_pretreatCost, para_CCS_capital, para_CCS_captureCost, para_CCS_transCost, para_CCS_storageCost = updateParas(columnName)
    
    lcoe = 0.0
    
    if retrofitYear - operateYear + 1 >= 40:
        lcoe = 0.0
    
    else:
        # Cap_PP = 3274 * C # CAPEX = 3274 $/kw
        # OM_PP = (41.66 + 31.35) * C   # O & M = 41.66 + 31.35 $/kw
        Fuel_PP = C * H * para_pp_coalCost / pow(10,3)  # coal price = 11.45/MWh
        # Debt_PP = Cap_PP * 0.0 # debt rate = 10% 
        # D_PP = 0.05 * Cap_PP # depricition rate = 5%
        
        Cap_BE = para_be_capital * C
        OM_BE = (para_be_fixOM + para_be_variOM) * C
        Fuel_BE = (para_be_purchaseCost + para_be_pretreatCost + para_be_trans2) * C * H/pow(10,3) + Sum_j_DBxij * para_be_trans1 / pow(10,3) * scale_Bio
        Debt_BE = Cap_BE * 0.0
        D_BE = Cap_BE * 0.05
        
        Cap_CCS = para_CCS_capital * C
        Emiss_CO2 = C * H * 0.801 / pow(10,3)  # 0.801 t/MWh
        OM_CCS = Emiss_CO2 * (para_CCS_captureCost + para_CCS_storageCost) + Emiss_CO2 * Dccs * para_CCS_transCost
        Debt_CCS = 0.0 * Cap_CCS
        D_CCS = 0.05 * Cap_CCS
        
        add_Cap = Cap_BE + Cap_CCS
        add_OM = OM_BE + OM_CCS
        Fuel_BE_PPpart = C * H * para_pp_coalCost / pow(10,3) - Sum_j_xij_kwh * para_pp_coalCost / pow(10,3) * scale_Bio
        add_Fuel =  Fuel_BE_PPpart + Fuel_BE - Fuel_PP # coal reduction cost and biomass cost
        add_Debt = Debt_BE + Debt_CCS
        add_D = D_BE + D_CCS
    
        Elec = C * H
        r = 1 + 0.05
        lifespan = 40
        
        n = retrofitYear - operateYear + 1 # 发生改造的i 
        # if n == 0: # [0:0] = no value
        #     n = n+1
        LF_0 = np.sum(lcoeFrame[:n, 0:5])
        LF_1 = np.sum(lcoeFrame[:,5])
        # print('BECCS:LF_O:%.2f, LF_1: %.2f' % (LF_0,LF_1))
        ori_cost_i = np.sum(lcoeFrame[n:,0:5], axis=1)
        cost_i = 0
        
        if n < lifespan:
            for i in range(n, lifespan):
                cost_i = ori_cost_i[0]   
                  
                if i == n:  # 改造第一年
                    cost_i = cost_i + (add_Cap + add_OM + add_Fuel) / pow(r, i+1)
                if i < (n + 10) and i > n:
                    cost_i = cost_i + (add_OM + add_Fuel + add_Debt) / pow(r, i+1)
                if i >= (n + 10) and i < lifespan - 1:
                    cost_i = cost_i + (add_OM + add_Fuel) / pow(r, i+1)
                if i == lifespan - 1:
                    cost_i = cost_i + (add_OM + add_Fuel - add_D) / pow(r, i+1)   
                LF_0 += cost_i
    
        lcoe = LF_0/LF_1
    
    return lcoe

def LCOE_Retire(C, H, operateYear, retrofitYear, lcoeFrame, columnName):
    
    para_be_capital, para_be_purchaseCost, para_be_pretreatCost, para_CCS_capital, para_CCS_captureCost, para_CCS_transCost, para_CCS_storageCost = updateParas(columnName)
    
    lcoe = 0.0
    
    if retrofitYear - operateYear + 1 >= 40: 
        lcoe = 0.0
        
    else: 
        r = 1 + 0.05  # rate
        lifespan = 40        
        
        n = retrofitYear - operateYear + 1
        # if n == 0:
        #     n = n+1
        LF_0 = np.sum(lcoeFrame[:n, 0:5])
        LF_1 = np.sum(lcoeFrame[:n,5])
        # print(LF_0,LF_1)
        
        D_retire = np.sum(lcoeFrame[:n, 0:1]) * 0.05 / pow(r, n+1)
        lcoe = (LF_0 - D_retire)/LF_1  
        # print('retire: LF_O:%.2f, LF_1: %.2f, D_retire:%.2f' % (LF_0, LF_1, D_retire))

    return lcoe
    
def LCOE_PP1(C, H, operateYear, retrofitYear, columnName):
    
    para_be_capital, para_be_purchaseCost, para_be_pretreatCost, para_CCS_capital, para_CCS_captureCost, para_CCS_transCost, para_CCS_storageCost = updateParas(columnName)

    # basic parameter, furthur explaination can be seen in documentation
    r = 1.05  # rate
    lifespan = 40
        
    Cap_PP = para_pp_capital * C # CAPEX = 3274 $/kw
    OM_PP = (para_pp_fixOM + para_pp_variOM) * C   # O & M = 41.66 + 31.35 $/kw
    Fuel_PP = C * H * para_pp_coalCost / pow(10,6)  # coal price = 11.45/MWh
    Debt_PP = Cap_PP * 0.0 # debt rate = 10% 
    D_PP = 0.05 * Cap_PP # depricition rate = 5%
    columnName = ['Equip','OM','Fuel','Debt','D','Elec']
    
    LCOEframe = np.zeros(shape=(lifespan, 6))
    elec = C * H

    for i in range(lifespan):
        
        if i == 0:
            LCOEframe[i] = np.divide([Cap_PP, OM_PP, Fuel_PP, Debt_PP, 0. , elec], pow(r, i + 1))
        if i < 10 and i > 0:
            LCOEframe[i] = np.divide([0., OM_PP, Fuel_PP, Debt_PP, 0. , elec], pow(r, i + 1))
        if i == lifespan - 1:
            LCOEframe[i] = np.divide([0., OM_PP, Fuel_PP, 0. , -D_PP , elec], pow(r, i + 1))
        if i >= 10 and i < lifespan - 1:
            LCOEframe[i] = np.divide([0., OM_PP, Fuel_PP, 0. , 0. , elec], pow(r, i + 1))

    lcoe = np.sum(LCOEframe[:, 0:5])/np.sum(LCOEframe[:, 5])

    if retrofitYear - operateYear + 1 >= 40:
        lcoe = 0.0

    return lcoe, LCOEframe

def LCOE_BE1(C, H, Sum_j_xij_kwh, Sum_j_DBxij, operateYear, retrofitYear, ori_lcoeframe, columnName):
    
    para_be_capital, para_be_purchaseCost, para_be_pretreatCost, para_CCS_capital, para_CCS_captureCost, para_CCS_transCost, para_CCS_storageCost = updateParas(columnName)

    # Cap_PP = 3274 * C # CAPEX = 3274 $/kw
    # OM_PP = (41.66 + 31.35) * C   # O & M = 41.66 + 31.35 $/kw
    Fuel_PP = C * H * para_pp_coalCost / pow(10,3)  # coal price = 11.45/MWh
    # Debt_PP = Cap_PP * 0.0 # debt rate = 10% 
    # D_PP = 0.05 * Cap_PP # depricition rate = 5%
    
    Cap_BE = para_be_capital * C
    OM_BE = (para_be_fixOM + para_be_variOM) * C
    Fuel_BE = (para_be_purchaseCost + para_be_pretreatCost + para_be_trans2) * C * H/pow(10,3) + Sum_j_DBxij * para_be_trans1 / pow(10,3) * scale_Bio
    Debt_BE = Cap_BE * 0.0
    D_BE = Cap_BE * 0.05
    
    add_Cap = Cap_BE
    add_OM = OM_BE
    Fuel_BE_PPpart = C * H * para_pp_coalCost / pow(10,3) - Sum_j_xij_kwh * para_pp_coalCost / pow(10,3) * scale_Bio
    add_Fuel =  Fuel_BE_PPpart + Fuel_BE - Fuel_PP # coal reduction cost and biomass cost        
    add_Debt = Debt_BE
    add_D = D_BE
    
    elec = C * H
    r = 1 + 0.05
    lifespan = 40
    
    n = retrofitYear - operateYear + 1 # retrofit year i
    LCOEframe = ori_lcoeframe.copy()
    
    if n < lifespan:
    # i 从改造年份开始
        for i in range(n, lifespan):
        #         print(i)
            if i == n:  # the first year of retrofit year        
        #             print('%.f,%.1f,%.1f, %.1f, %.1f'%(i,np.sum(LCOEframe[i,0:5])/pow(10,8), add_Cap,add_OM,add_Fuel))
                LCOEframe[i] =  LCOEframe[i] + np.divide([add_Cap, add_OM, add_Fuel, 0, 0., 0.], pow(r, i+1))
            if i < (n + 10) and i > n:
        #             print('%.f,%.1f, %.1f, %.1f, %.1f'%(i,np.sum(LCOEframe[i,0:5])/pow(10,8),add_OM,add_Fuel,add_Debt))
                LCOEframe[i] = LCOEframe[i] + np.divide([0., add_OM, add_Fuel, add_Debt, 0. , 0], pow(r, i + 1))
            if i >= (n + 10) and i < lifespan - 1:
        #             print('%.f,%.1f, %.1f, %.1f'%(i,np.sum(LCOEframe[i,0:5])/pow(10,8),add_OM,add_Fuel))
                LCOEframe[i] = LCOEframe[i] + np.divide([0., add_OM, add_Fuel, 0., 0. , 0], pow(r, i + 1))
            if i == lifespan - 1:
        #             print('%.f,%.1f, %.1f, %.1f, %.1f'%(i,np.sum(LCOEframe[i,0:5])/pow(10,8),add_OM,add_Fuel,add_D))
                LCOEframe[i] = LCOEframe[i] + np.divide([0., add_OM, add_Fuel, 0., -add_D , 0], pow(r, i + 1))
            cost_i = np.sum(LCOEframe[i][0:5])    
    
    lcoe = np.sum(LCOEframe[:, 0:5])/np.sum(LCOEframe[:, 5])
    
    if retrofitYear - operateYear + 1 >= 40:
        lcoe = 0.0
        
    return lcoe, LCOEframe
            
def LCOE_CCS1(C, H, Dccs, operateYear, retrofitYear, ori_lcoeframe, columnName):
    
    para_be_capital, para_be_purchaseCost, para_be_pretreatCost, para_CCS_capital, para_CCS_captureCost, para_CCS_transCost, para_CCS_storageCost = updateParas(columnName)
    
    # Cap_PP = 3274 * C # CAPEX = 3274 $/kw
    # OM_PP = (41.66 + 31.35) * C   # O & M = 41.66 + 31.35 $/kw
    # Fuel_PP = C * H * 11.45 / pow(10,3)  # coal price = 11.45/MWh
    # Debt_PP = Cap_PP * 0.0 # debt rate = 10% 
    # D_PP = 0.05 * Cap_PP # depricition rate = 5% 
    
    Fuel_PP = C * H * para_pp_coalCost / pow(10,3)  # coal price = 11.45/MWh
    # Debt_PP = Cap_PP * 0.0 # debt rate = 10% 
    # D_PP = 0.05 * Cap_PP # depricition rate = 5%
    
    Cap_CCS = para_CCS_capital * C
    Emiss_CO2 = C * H * 0.801 / pow(10,3)  # 0.801 t/MWh
    OM_CCS = Emiss_CO2 * (para_CCS_captureCost + para_CCS_storageCost) + Emiss_CO2 * Dccs * para_CCS_transCost
    Debt_CCS = 0.0 * Cap_CCS
    D_CCS = 0.05 * Cap_CCS
    
    add_Cap = Cap_CCS
    add_OM = OM_CCS
    add_Fuel = 0
    add_Debt = Debt_CCS
    add_D = D_CCS
    
    elec = C * H
    r = 1 + 0.05
    lifespan = 40
    
    n = retrofitYear - operateYear + 1 # 发生改造的i 
    LCOEframe = ori_lcoeframe.copy()
    
    if n < lifespan:
        for i in range(n, lifespan):   
            if i == n:  # 改造第一年
                # oriCapCost_add = Cap_CCS - max(LCOEframe[:i,0]) # 用于判断之前的frame中的技术改造选项
                LCOEframe[i] = LCOEframe[i] + np.divide([add_Cap, add_OM, add_Fuel, 0., 0. , 0], pow(r, i + 1)) 
                
            if i < (n + 10) and i > n:
                LCOEframe[i] = LCOEframe[i] + np.divide([0., add_OM, add_Fuel, add_Debt, 0. , 0], pow(r, i + 1))
                
            if i >= (n + 10) and i < lifespan - 1:
                LCOEframe[i] = LCOEframe[i] + np.divide([0., add_OM, add_Fuel, 0., 0. , 0], pow(r, i + 1))
                
            if i == lifespan - 1:
                LCOEframe[i] = LCOEframe[i] + np.divide([0., add_OM, add_Fuel, 0., -add_D , 0], pow(r, i + 1))
            
    
    lcoe = np.sum(LCOEframe[:, 0:5])/np.sum(LCOEframe[:, 5])    
    
    if retrofitYear - operateYear + 1 >= 40:
        lcoe = 0.0
    
    return lcoe, LCOEframe

def LCOE_BECCS1(C, H, Sum_j_xij_kwh, Sum_j_DBxij, Dccs, operateYear, retrofitYear, ori_lcoeframe, columnName):
    
    para_be_capital, para_be_purchaseCost, para_be_pretreatCost, para_CCS_capital, para_CCS_captureCost, para_CCS_transCost, para_CCS_storageCost = updateParas(columnName)
          
    # Cap_PP = 3274 * C # CAPEX = 3274 $/kw
    # OM_PP = (41.66 + 31.35) * C   # O & M = 41.66 + 31.35 $/kw
    Fuel_PP = C * H * para_pp_coalCost / pow(10,3)  # coal price = 11.45/MWh
    # Debt_PP = Cap_PP * 0.0 # debt rate = 10% 
    # D_PP = 0.05 * Cap_PP # depricition rate = 5%
    
    Cap_BE = para_be_capital * C
    OM_BE = (para_be_fixOM + para_be_variOM) * C
    Fuel_BE = (para_be_purchaseCost + para_be_pretreatCost + para_be_trans2) * C * H/pow(10,3) + Sum_j_DBxij * para_be_trans1 / pow(10,3) * scale_Bio
    Debt_BE = Cap_BE * 0.0
    D_BE = Cap_BE * 0.05
    
    Cap_CCS = para_CCS_capital * C
    Emiss_CO2 = C * H * 0.801 / pow(10,3)  # 0.801 t/MWh
    OM_CCS = Emiss_CO2 * (para_CCS_captureCost + para_CCS_storageCost) + Emiss_CO2 * Dccs * para_CCS_transCost
    Debt_CCS = 0.0 * Cap_CCS
    D_CCS = 0.05 * Cap_CCS
    
    add_Cap = Cap_BE + Cap_CCS
    add_OM = OM_BE + OM_CCS
    Fuel_BE_PPpart = C * H * para_pp_coalCost / pow(10,3) - Sum_j_xij_kwh * para_pp_coalCost / pow(10,3) * scale_Bio
    add_Fuel =  Fuel_BE_PPpart + Fuel_BE - Fuel_PP # coal reduction cost and biomass cost
    add_Debt = Debt_BE + Debt_CCS
    add_D = D_BE + D_CCS
    
    elec = C * H
    r = 1 + 0.05
    lifespan = 40
    
    n = retrofitYear - operateYear + 1 # 发生改造的i 
    LCOEframe = ori_lcoeframe.copy()
    
    if n < lifespan:
        for i in range(n, lifespan):   
            if i == n:  # 改造第一年
                # oriCapCost_add = Cap_BECCS - max(LCOEframe[:i,0]) # 用于判断之前的frame中的技术改造选项
                LCOEframe[i] = LCOEframe[i] + np.divide([add_Cap, add_OM, add_Fuel, 0., 0. , 0], pow(r, i + 1)) 
                
            if i < (n + 10) and i > n:
                LCOEframe[i] = LCOEframe[i] + np.divide([0., add_OM, add_Fuel, add_Debt, 0. , 0], pow(r, i + 1))
                
            if i >= (n + 10) and i < lifespan - 1:
                LCOEframe[i] = LCOEframe[i] + np.divide([0., add_OM, add_Fuel, 0., 0. , 0], pow(r, i + 1))
                
            if i == lifespan - 1:
                LCOEframe[i] = LCOEframe[i] + np.divide([0., add_OM, add_Fuel, 0., -add_D , 0], pow(r, i + 1))

    lcoe = np.sum(LCOEframe[:, 0:5])/np.sum(LCOEframe[:, 5])
    
    if retrofitYear - operateYear + 1 >= 40:
        lcoe = 0.0
    
    return lcoe, LCOEframe

def LCOE_Retire1(C, H, operateYear, retrofitYear, ori_lcoeframe, columnName):
    
    para_be_capital, para_be_purchaseCost, para_be_pretreatCost, para_CCS_capital, para_CCS_captureCost, para_CCS_transCost, para_CCS_storageCost = updateParas(columnName)
    
    lcoe = 0.0   

    r = 1 + 0.05
    lifespan = 40
    n = retrofitYear - operateYear + 1
    LCOEframe = ori_lcoeframe.copy()

    D_retire = np.sum(LCOEframe[:n, 0:1]) * 0.05 / pow(r, n+1) # include n
    # print(D_retire)
    
    if n < lifespan:
        for i in range(n, lifespan):
            LCOEframe[i] =  LCOEframe[i] * [0., 0., 0., 0, 0., 0.]
    
        LCOEframe[n] =  LCOEframe[n] + [0., 0., 0., 0., -D_retire, 0.]
    
    lcoe = np.sum(LCOEframe[:n+1, 0:5])/np.sum(LCOEframe[:n, 5])     
    # print('up:%.2f,down:%.2f'%(np.sum(LCOEframe[:n+1, 0:5]),np.sum(LCOEframe[:n, 5])))
    
    if retrofitYear - operateYear + 1 >= 40:
        lcoe = 0.
    
    return lcoe, LCOEframe