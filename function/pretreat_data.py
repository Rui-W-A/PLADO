# -*- coding: utf-8 -*-
"""
Created on Thu May 26 17:13:56 2022

@author: vicke
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from function.cal_cost_sensitivity import LCOE_PP, LCOE_PP1, LCOE_BE1, LCOE_CCS1, LCOE_BECCS1, LCOE_Retire1
from function.cal_emiss import Emiss_BE, Emiss_PP, Emiss_CCS, Emiss_BECCS, Emiss_Retire
                          

def pretreat_pp(filePath, power_scale, columnName):
    # filePath = 'inputData/pp_4536_2018_20km.csv'
    pp_data = pd.read_csv(filePath, nrows = power_scale)
    
    pp_data['take'] = 0.
    pp_data['C2020'] = pp_data.apply(lambda x: LCOE_PP(x['Capacity_kw'],x['hours'],x['year'], 2020, columnName), axis=1)
    
    ori_emiss_path = []
    for year in range(2020,2065,5):  # from 2020 to 2065
        pp_data['E'+str(year)] = pp_data.apply(lambda x: Emiss_PP(x['Capacity_kw'], x['hours'], x['year'],year, x['CoalUnit_g/kwh']), axis=1)
        ori_emiss_path.append(pp_data['E'+str(year)].sum())
        # print(pp_data['E'+str(year)].sum())
    
    # columns name
    pick = ['ID', 'hours', 'Capacity_kw', 'CoalUnit_g/kwh',
            'lon', 'lat', 'year', 'pixelX','pixelY','ccsDis_km',
            'option', 'take','C2020','E2020']
    df_selected = pp_data.loc[:,pick]
    
    # use a tuple to record pixelX and Y
    df_selected['pos'] = df_selected[['pixelX','pixelY']].apply(tuple, axis=1)
    df_selected["ID"] = df_selected["ID"].map(str)
    
    # convert dataframe to list, and use ID as key
    powerDict = df_selected.set_index('ID').T.to_dict('list')
    
    # initialize lcoe dataframe
    retrofitYear = 2020
    for i in range(1,len(powerDict)+1):
        C = powerDict[str(i)][1]
        H = powerDict[str(i)][0]
        UC = powerDict[str(i)][2]
        OY = powerDict[str(i)][6]
        
        lcoe, lcoeFrame = LCOE_PP1(C, H, OY, retrofitYear,columnName)
        powerDict[str(i)].append(lcoeFrame)
        powerDict[str(i)].append(retrofitYear)  
        
    return powerDict, ori_emiss_path