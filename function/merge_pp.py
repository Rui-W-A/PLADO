# -*- coding: utf-8 -*-
"""
Created on Fri May 27 09:08:02 2022

@author: vicke
"""

import numpy as np
import pandas as pd
from function.cal_cost_sensitivity import LCOE_PP, LCOE_BE, LCOE_BECCS, LCOE_CCS, LCOE_Retire
from function.cal_cost_sensitivity import LCOE_PP1, LCOE_BE1, LCOE_BECCS1, LCOE_CCS1, LCOE_Retire1


def merge_pp1(mode,emiss_senario,ori_pp_path):
    # ---------------  merge pp to an excel -------------------------------
    inpath_pp = 'outputData/tmp_pp/'
    outpath_pp = 'outputData/tmp_pp/'
    # ori_pp_path = 'inputData/pp_4536_2018_20km.csv'

    output_frame = pd.read_csv(ori_pp_path, index_col=0)
    # output_frame = ori_data[['ID', 'hours', 'Capacity_kw','CoalUnit_g/kwh', 'boilerType'
    #                          'lon', 'lat', 'prov', 'year', 'pixelX', 'pixelY', 'ccsDis_km', 'option']]
    # output_frame = output_frame.set_index(output_frame.columns[0])

    for year in range(2025, 2065, 5):
        data_name = 'pp_' + str(year) + '.csv'
        data_path = inpath_pp + data_name
        tmp_data = pd.read_csv(data_path, index_col=0)
        # if len(tmp_data) == 0:
        #     break
        # tmp_data = tmp_data.set_index(tmp_data.columns[0])

        column_name = ['option','take','cost','emiss','retrofitYear']
        tmp = tmp_data[column_name]
        tmp.columns=[x + str(year) for x in column_name]
        output_frame = pd.merge(output_frame,tmp,how='left',left_index=True,right_index=True)
        
    output_frame = output_frame.sort_index(axis=1)
    output_frame.to_excel(outpath_pp +'result_' + emiss_senario +'_' + mode +'.xls')

def cal_operateYear(power, num):
    retrofitYear = [x for x in range(2025,2060,5)]
    index_retrofitYear = [x for x in range(1,8,1)]
    tmp = power.loc[0:num-1, 'cost2025':'cost2055'].fillna(0)     
    tmp[tmp!=0] = 1
    index_lastYear = tmp.cumsum(axis=1).max(axis=1)         
    tmp['retrofitYear'] = index_lastYear.replace(index_retrofitYear,retrofitYear) 
    tmp['year'] = power.loc[0:num-1, 'year']  
    # 假设是2050年改造，电厂将会持续运行到2055年
    power['lifeTime'] = tmp['retrofitYear'] - power.loc[0:num-1,'year'] + 5
    return power 

def cal_profit(power, num, elecPrice):
    power['finalCost'] = power.loc[0:num-1,'cost2025':'cost2055'].ffill(axis=1).iloc[:,-1]
    power = cal_operateYear(power, num)
    sell = elecPrice * power.loc[0:num-1,'Capacity_kw'] * power.loc[0:num-1,'hours'] * power['lifeTime']
    cost= power.loc[0:num-1,'finalCost']*power.loc[0:num-1,'Capacity_kw']*power.loc[0:num-1,'hours']*power['lifeTime']
    profit = sell - cost
    return profit


def cal_Cost(mode,emiss_scenario,ori_pp_path, infeasibleYear):
    # ---------------  merge pp to an excel -------------------------------
    inpath_pp = 'outputData/tmp_pp/'
    outpath_pp = 'outputData/tmp_pp/'
    # ori_pp_path = 'inputData/pp_4536_2018_20km.csv'
    
    output_frame = pd.read_csv(ori_pp_path, index_col=0)
    

    for year in range(2025, infeasibleYear, 5):
        data_name = 'pp_' + str(year) + '.csv'
        data_path = inpath_pp + data_name
        tmp_data = pd.read_csv(data_path, index_col=0)
        # if len(tmp_data) == 0:
        #     break

        column_name = ['option','take','cost','emiss','retrofitYear']
        tmp = tmp_data[column_name]
        tmp.columns=[x + str(year) for x in column_name]
        output_frame = pd.merge(output_frame,tmp,how='left',left_index=True,right_index=True)
        
    output_frame = output_frame.sort_index(axis=1)
    output_frame.to_excel(outpath_pp +'result_' + emiss_scenario +'_' + mode +'.xls')
    
    num = len(output_frame)
    pp_all = output_frame.copy()
    pp_all['C2020']= pp_all.apply(lambda x: LCOE_PP(x['Capacity_kw'],x['hours'],x['year'], 2020,'Value'), axis=1)
    
    ori_lifeTime = (5 - pp_all['year']%5)
    ori_lifeTime[ori_lifeTime==5]=0
    ori_lifeTime = ori_lifeTime + 40  
    
    elecPrice = 0.1 # USD/kWh
    profit_BAU_unit = elecPrice * pp_all.loc[0:num-1,'Capacity_kw'] * pp_all.loc[0:num-1,'hours'] * ori_lifeTime - pp_all.loc[0:num-1,'C2020'] * pp_all.loc[0:num-1,'Capacity_kw'] * pp_all.loc[0:num-1,'hours'] * ori_lifeTime
    pp_all['profit_BAU'] = profit_BAU_unit
    pp_all['profit_all'] = cal_profit(pp_all, num, elecPrice)
    pp_all['cost'] = pp_all['profit_BAU'] - pp_all['profit_all']
    cost_all = np.sum(pp_all['cost'])
    
    
    # # emission
    # emiss_all = pp_all[['emiss2020','emiss2025','emiss2030','emiss2035','emiss2040','emiss2045','emiss2050','emiss2055']].sum(axis=0)
    # emissList = [] # 记录原始排放量
    # for year in range(2020,2060,5):
    #     pp_emiss = pp_all[['year','emiss2020']]
    #     pp_emiss.loc[(pp_emiss.year + 40 < year),'emiss2020'] = 0 # 如果投产年份+40 小于当年，则该行的排放为0
    #     emiss = np.sum(pp_emiss['emiss2020'])
    #     emissList.append(emiss)
        
    # cumReduce = 0
    # for year in range(0,8):
    #     tmp = (emissList[year] - emiss_all[year])*5
    #     cumReduce = cumReduce + tmp
    
    return cost_all
    