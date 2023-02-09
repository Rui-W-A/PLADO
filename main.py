# -*- coding: utf-8 -*-
"""
Created on Tue Sep 27 15:11:59 2022

@author: vicke
"""

import gurobipy as gp
from gurobipy import GRB
import pickle
import sys
import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt
from function.generate_bioDict import generate_bioDict
from function.generate_disDict import generate_disDict
from function.build_model import build_model_5opt,build_model_Retire, build_model_Retrofit, build_model_BE, build_model_CCS, build_model_BECCS
from function.record_modelOutput import record_ppOutput, record_resOutput
from function.generate_emissionGoal import set_emissionGoal, set_emissionGoal_1, set_emissionGoal_2
from function.pretreat_data import pretreat_pp
from function.merge_pp import merge_pp1, cal_Cost
from function.update_pp import update_power1
import os
import sys
import csv    

# another scenario, read data from excel
emiss = pd.read_csv('inputData/pp_scenario.csv',index_col=0)

# set emission reduction target according to scenario input
emissReductionRate = emiss.to_dict()
dict_key = ['main']
# dict_key = list(emissReductionRate.keys())
# for i in range(0, 79 + 1, 1):
#     key = dict_key[i]
#     emissReductionRate.pop(key)
# dict_key = list(emissReductionRate.keys())

for sce_key in dict_key:
    # model_main('All','Value',reduceRatioList)
    reduceRatioList = emissReductionRate[sce_key]
    print(reduceRatioList)
    bioScale = pow(10,9)
    emissScale = pow(10,6) 
    
    # scale control
    power_scale = 100
    radius_limit = 5  # distance = radius_limit * 10km
    gap_set = 0.05   # 5%
    resolution = 20
    mode = 'All' # Retrofit, All ,Retire, BE, CCS, BECCS
    columnName = 'Value'
    emiss_scenario = str(sce_key)
    
    # read power plant
    pp_filePath = "inputData/pp_2545_2020_20km.csv"
    pp_dict, ori_emiss_path = pretreat_pp(pp_filePath, power_scale, columnName)
    power = pp_dict.copy()
    with open('outputData/tmp_pp/pp_2020.pkl','wb') as f:
        pickle.dump(power, f)
    
    # read bimass resources
    bio_filePath = 'inputData/res_kwh_20km_S3_AF.npy'
    bio_dict = generate_bioDict(bio_filePath)  # kwh is divided by 10^6
        
    # prepre for modelling
    start = time.time()
    
    EMISS_GOAL_LIST, cumReduce, ori_emiss_sum  = set_emissionGoal_2(ori_emiss_path, reduceRatioList)
    
    BioSupply=0.
    
    for year in range(2025, 2065, 5):
        
        set_retrofitYear = year
        EMISS_GOAL = EMISS_GOAL_LIST[set_retrofitYear]
        print('year %.f, Emission Goal:%.f' % (set_retrofitYear, EMISS_GOAL))
        
        ppOptionRecord = []
        pp2ResTake = []
        
        oldYear = set_retrofitYear - 5
        
        # power dataset pretreatment
        
        power = np.load('outputData/tmp_pp/pp_%s.pkl' % str(year-5), allow_pickle=True)
        power = update_power1(power,year) # natural retire or compulsory retire?
        # if all power plant are retired, no need for further calculation
        if len(power)==0:
            columnsPP = ['hours', 'Capacity_kw', 'CoalUnit_g/kwh',
                    'lon', 'lat', 'year', 'pixelX','pixelY','ccsDis_km',
                    'option', 'take','cost','emiss','pos','retrofitYear']
            fileName = 'pp_' + str(set_retrofitYear)
            tmpDataFrame = pd.DataFrame.from_dict(power, orient='index', columns=columnsPP)
            tmpDataFrame.to_csv('outputData/tmp_pp/%s.csv' % fileName)
            # save as pickle file
            with open('outputData/tmp_pp/%s.pkl' % fileName,'wb') as f:
                pickle.dump(power, f)
            continue

        power_station_id, hours, capacity, unitCoal, lon, lat, operateYear,\
        pixelX, pixelY, dccs, y_opt, take, cost, emiss, pp_pos, ori_lcoeFrame, retrofitYear = gp.multidict(power)
        
        # biomass resources
        res_point_id, resources, res_loc = gp.multidict(bio_dict)
        
        # distance matrix
        power2res, distance = gp.multidict(generate_disDict(pp_pos, res_loc, radius_limit, resolution))
    
        # build and solve model 
        if mode == 'All':
            ppOptionRecord, pp2ResTake = build_model_5opt("model", power_station_id, hours, capacity, 
                                lon, lat, operateYear, retrofitYear, set_retrofitYear,
                                ori_lcoeFrame, pixelX, pixelY, dccs, pp_pos, 
                                y_opt, take, cost, emiss, res_point_id, 
                                resources, power2res, distance, EMISS_GOAL,gap_set, BioSupply, emissScale, columnName, unitCoal)
        elif mode =='Retire':
            ppOptionRecord, pp2ResTake = build_model_Retire("model", power_station_id, hours, capacity, 
                                lon, lat, operateYear, retrofitYear, set_retrofitYear,
                                ori_lcoeFrame, pixelX, pixelY, dccs, pp_pos, 
                                y_opt, take, cost, emiss, res_point_id, 
                                resources, power2res, distance, EMISS_GOAL,gap_set, BioSupply, emissScale, columnName, unitCoal)
        elif mode == 'BE':
                    ppOptionRecord, pp2ResTake = build_model_BE("model", power_station_id, hours, capacity, 
                    lon, lat, operateYear, retrofitYear, set_retrofitYear,
                    ori_lcoeFrame, pixelX, pixelY, dccs, pp_pos, 
                    y_opt, take, cost, emiss, res_point_id, 
                    resources, power2res, distance, EMISS_GOAL,gap_set, BioSupply, emissScale, columnName, unitCoal)    
        
        elif mode == 'BECCS':
                    ppOptionRecord, pp2ResTake = build_model_BECCS("model", power_station_id, hours, capacity, 
                    lon, lat, operateYear, retrofitYear, set_retrofitYear,
                    ori_lcoeFrame, pixelX, pixelY, dccs, pp_pos, 
                    y_opt, take, cost, emiss, res_point_id, 
                    resources, power2res, distance, EMISS_GOAL,gap_set, BioSupply, emissScale, columnName, unitCoal)    
    
        elif mode == 'CCS':
                    ppOptionRecord, pp2ResTake = build_model_CCS("model", power_station_id, hours, capacity, 
                    lon, lat, operateYear, retrofitYear, set_retrofitYear,
                    ori_lcoeFrame, pixelX, pixelY, dccs, pp_pos, 
                    y_opt, take, cost, emiss, res_point_id, 
                    resources, power2res, distance, EMISS_GOAL,gap_set, BioSupply, emissScale, columnName, unitCoal)    
        elif mode == 'Retrofit':
                    ppOptionRecord, pp2ResTake = build_model_Retrofit("model", power_station_id, hours, capacity, 
                    lon, lat, operateYear, retrofitYear, set_retrofitYear,
                    ori_lcoeFrame, pixelX, pixelY, dccs, pp_pos, 
                    y_opt, take, cost, emiss, res_point_id, 
                    resources, power2res, distance, EMISS_GOAL,gap_set, BioSupply, emissScale, columnName, unitCoal)
        
        # record pp results in tmp_pp output file
        infeasibleYear = record_ppOutput(ppOptionRecord, pp2ResTake, power, set_retrofitYear,power_station_id,bioScale)
        
        # record resouces take percentage
        # if mode != 'Retire':
        #     record_resOutput(pp2ResTake, res_loc, resources, set_retrofitYear)
        #     BioSupply = np.sum(pp2ResTake)  
        #     print("biomass amount: %.1f" % BioSupply)
        
        del ppOptionRecord, pp2ResTake
        del power2res, distance        
    
    cost = cal_Cost(mode,emiss_scenario, pp_filePath, infeasibleYear)
    carbonCost = cost/cumReduce
    print('cost: %.3f, reduceEmiss: %.3f, carbonCost: %.3f' % (cost, cumReduce, carbonCost))
    outline = str(cost)+','+ str(cumReduce) +',' + str(carbonCost) + ','+ str(ori_emiss_sum) + '\n'
    with open('out-2545.csv', 'a') as f:  # 'a' append
        f.write(outline)
    
    end = time.time()
    print('Running time: %s minitue' % ((end - start)/60))
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    