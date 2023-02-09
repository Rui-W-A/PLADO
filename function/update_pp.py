# -*- coding: utf-8 -*-
"""
Created on Thu Jun  9 16:33:18 2022

@author: vicke
"""

import numpy as np
import pandas as pd
# from function.cal_cost_sensitivity import LCOE_PP, LCOE_PP1, LCOE_BE1, LCOE_CCS1, LCOE_BECCS1, LCOE_Retire1

# the num = 0
# pick = ['hours', 'Capacity_kw', 'CoalUnit_g/kwh', 'BioUnit_g/kwh', 
#         'lon', 'lat', 'year', 'pixelX','pixelY','ccsDis_km',
#         'option', 'take','C2020','E2020','pos','lcoeFrame','retrofitYear']

# # this function is used to clean the power plant that are supposed to be retired.
# def update_power(before_power, set_retrofitYear):
    
#     powerplant = before_power.copy()
#     OY_num = 6
#     ppType_num = 10
#     lcoe_frame_num = 15
#     C_num = 1
#     H_num = 0    
    
#     lcoeDict = dict()
#     for k,v in powerplant.items():
#         OY = v[OY_num]
#         retrofitType = v[ppType_num]
#         if set_retrofitYear - OY >= 40:
#             # rebuild a new coal power unit as the same generation
#             v[OY_num] = OY + 40
#             v[ppType_num] = 'PP'
#             C = v[C_num]
#             H = v[H_num]
#             lcoe, lcoeFrame = LCOE_PP1(C, H, OY, OY, columnName))
#             v[lcoe_frame_num] = lcoeFrame
        
#         if retrofitType == 'Retire':  # rebuild a new plant
#             v[OY_num] = set_retrofitYear - 5
#             v[ppType_num] = 'PP'
#             C = v[C_num]
#             H = v[H_num]
#             lcoe, lcoeFrame = LCOE_PP1(C, H, OY, OY)
#             v[lcoe_frame_num] = lcoeFrame
        
#         lcoeDict.update({k:v[lcoe_frame_num]})
            
#             # its option is pp
#             # popkey.append(k)
#         # lcoeDict.update({k: v[lcoe_frame_num]})
    
#     return powerplant

def update_power1(power,year):
    power_copy = power.copy()
    index_inYear = 5
    index_option = 9
    pop_id = []
    for pp_key, pp_value in power_copy.items():
        option = pp_value[index_option]
        inYear = int(pp_value[index_inYear])
        # 如果选项是强制淘汰
        if option=='Retire':
            pop_id.append(pp_key)
        
        # 如果改造年份超过了寿命
        elif year - inYear >= 40:
            pop_id.append(pp_key)
            
    for key_id in pop_id:
        power_copy.pop(key_id)
            
    print('the number of retired power: %0.f' % len(pop_id))
    return power_copy
        
    
    
    
    
    
    
    
    