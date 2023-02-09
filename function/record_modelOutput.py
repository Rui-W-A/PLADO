# -*- coding: utf-8 -*-
"""
Created on Thu Jan 20 21:19:40 2022

@author: vicke
"""

import numpy as np
import pandas as pd
import pickle
import matplotlib.pyplot as plt


def record_ppOutput(ppOptionRecord, pp2ResTake, power, set_retrofitYear, power_station_id, bioScale):
    # update retrofit status for power plant
    # ppOptionRecord record {p:[up, takeRes, costValue, emissValue, cost_dataFrame]})
    # 根据ppOption Record 生成新的power dict
    num_power_option = 9
    num_power_take = 10
    num_power_cost = 11
    num_power_emiss = 12
    num_power_lcoeFrame = 14
    num_power_retrofitYear = 15
    
    num_ppOption_retrofitOption = 0
    num_ppOption_take = 1
    num_ppOption_cost = 2
    num_ppOption_emiss = 3
    num_ppOption_lcoeFrame = 4
    
    power_Result = power.copy() # record power results
    power_Result_csv = dict()
    
    if len(ppOptionRecord) != 0:
        for i in power_station_id:
            power_i = power_Result[i]
            ppOptionRecord_i = ppOptionRecord[i]
            
            power_i[num_power_option] = ppOptionRecord_i[num_ppOption_retrofitOption]
            power_i[num_power_take] = ppOptionRecord_i[num_ppOption_take] * bioScale
            power_i[num_power_cost] = ppOptionRecord_i[num_ppOption_cost]
            power_i[num_power_emiss] = ppOptionRecord_i[num_ppOption_emiss]
            power_i[num_power_lcoeFrame] = ppOptionRecord_i[num_ppOption_lcoeFrame]
            power_i[num_power_retrofitYear] = set_retrofitYear
            
            power_Result[i]=power_i
            
            power_Result_csv[i] = np.delete(power_i, num_power_lcoeFrame, axis = 0)
            # print(i)    
        fileName = 'pp_' + str(set_retrofitYear)
        # 存成pickle文件
        with open('outputData/tmp_pp/%s.pkl' % fileName,'wb') as f:
            pickle.dump(power_Result, f)
        ## 存成csv文件
        # columnsName = ['hours','Capacity_kw','CoalUnit_g/kwh','BioUnit_g/kwh',
        #                 'lon','lat','operateYear','pixelX','pixelY','ccsDis_km',\
        #                 'option','take','cost','emiss','pos','retrofitYear']
            
        columnsName = ['hours', 'Capacity_kw', 'CoalUnit_g/kwh',
                'lon', 'lat', 'year', 'pixelX','pixelY','ccsDis_km',
                'option', 'take','cost','emiss','pos','retrofitYear']
            
        tmpDataFrame = pd.DataFrame.from_dict(power_Result_csv, orient='index', columns=columnsName)
        tmpDataFrame.to_csv('outputData/tmp_pp/%s.csv' % fileName)
        return 2065
    
    else:
        return set_retrofitYear # this year is infeasible
    

def record_resOutput(pp2ResTake,res_loc, resources, set_retrofitYear):
    # 2. 将pairMatrix做成百分比数据，存为numpy
    # 这个res是每个编号对应的行列号
    pp2ResTakeFrame = pd.DataFrame(pp2ResTake,columns = ['ppCode', 'BCPcode', 'take'])
    sumTakeByBCPcode = pp2ResTakeFrame.groupby('BCPcode').sum()
    tmp1 = sumTakeByBCPcode[sumTakeByBCPcode['take'] > 0.] # choose the value of take bigger than zero
    
    # return take to resMatrix 
    takeMatrix = np.zeros([200,350])
    for bcpCode in tmp1.index:       
        # find the number of row and col according to bcpCode
        col = res_loc[str(int(bcpCode))][0]  # x
        row = res_loc[str(int(bcpCode))][1]  # y
        takeMatrix[row][col] = tmp1.loc[bcpCode,'take']
        # print(col,row,tmp1.loc[bcpCode,'take'])
    # plt.imshow(takeMatrix)
    # np.save('output/testData/w_retire/takeMatrix_5opts_%d_%d_%d.npy' % (Power_count,radius,set_retrofitYear), takeMatrix)
    
    # return res to ori_resMatrix
    # ori_resMatrix = np.zeros([400,700])
    # for ikey, ivalue in res_loc.items():
    #     col = ivalue[1][0]
    #     row = ivalue[1][1]
    #     resValue = ivalue[0]
    #     ori_resMatrix[row][col] = resValue
        
    oriMatrix = np.zeros([200, 350])
    for ikey, ivalue in resources.items():
        col = res_loc[ikey][0]
        row = res_loc[ikey][1]
        oriMatrix[row][col] = ivalue
    
    # cal percentage matrix
    oriMatrix[oriMatrix == 0.] = -999
    percen_resMatrix = takeMatrix/oriMatrix
    
    # fig = plt.figure(figsize = (7,4), dpi = 300)
    # plt.imshow(percen_resMatrix)
    # plt.show()
    # plt.close()
    # plt.imshow(percen_resMatrix[150:160,450:500])
    
    fileName = 'resTakePer_' + str(set_retrofitYear)
    np.save('outputData/tmp_res/%s.npy' % fileName, percen_resMatrix)
    
    # # write tif
    # gis.writeTif_wgs84_degree('output/testData/w_retire/takeMatrix_percent_5opts_%d_%d_%d.tif' % (Power_count,radius, set_retrofitYear), percen_resMatrix,0.1)
    
    
    
    
    