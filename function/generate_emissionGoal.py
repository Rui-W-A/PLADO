# -*- coding: utf-8 -*-
"""
Created on Wed Feb 23 20:20:39 2022

@author: vicke
"""

import numpy as np
from scipy import interpolate
import pandas
import matplotlib.pyplot as plt

# def cal_cumulateEmiss(emissPath, timeStep):
#     n = len(emissPath)
#     I_trapz = (timeStep/2) * (emissPath[0] + 2*sum(emissPath[1:n-1]) + emissPath[n-1])
#     return I_trapz

# def set_emissionGoal(ori_emiss_path):
        
#     # interpolate the emission target
#     x = np.array([2020, 2025, 2060])
#     y = np.array([ori_emiss_path[0], ori_emiss_path[0]/2, ori_emiss_path[0]/5])
#     # f=interpolate.interp1d(x,y,kind='quadratic')
#     f=interpolate.interp1d(x,y,kind='linear')
    
#     # store the result in a dict
#     goalDict = dict()
#     for yearKey in range(2020,2065,5):
#         goalDict[yearKey] = int(f(yearKey))
#     print(goalDict)
    
#     goal = [x for x in goalDict.values()]
#     originEmiss = cal_cumulateEmiss(ori_emiss_path,5)/pow(10,9)
#     retrofitEmiss = cal_cumulateEmiss(goal, 5)/pow(10,9)
#     diff = originEmiss - retrofitEmiss
#     print('origin:%.f Gt; retrofit:%.f Gt; diff:%.f Gt'%(originEmiss,retrofitEmiss,diff))   
    
    
#     plt.plot(np.linspace(2020, 2060, 9),np.divide(ori_emiss_path,pow(10,9)), color='black')
#     plt.plot(np.linspace(2020, 2060, 9), np.divide(goal,pow(10,9)),  color='green')
#     plt.ylabel('Carbon Emission (Gt)', fontsize=12)
#     plt.title('origin:%.f Gt; retrofit:%.f Gt; diff:%.f Gt'%(originEmiss,retrofitEmiss,diff))
#     plt.savefig('outputData/emissPath.png')
    
#     return goalDict


def plot_emissGoal(goalDict, ori_emiss_path,cumEmissReduce):
    goalList = list(goalDict.values())
    goalList.insert(0, ori_emiss_path[0])
    goalList.append(goalList[-1])
    oriList = [ori_emiss_path[0] for i in range(2020,2065,5)]
    year = [x for x in range(2020,2065,5)]
    plt.step(year,oriList,where='post',label='ori',color='black')
    plt.step(year,goalList, where='post',label='retrofit',color='green')
    plt.hlines(0, xmin=2020, xmax=2060, color='r')
    plt.plot(year,goalList, 'o--', color='green',alpha=0.5)
    plt.title(cumEmissReduce)
    plt.savefig('outputData/emissPath.png')
    
def cal_culmu(goalDict, ori_emiss_path):
    goalList = list(goalDict.values())
    ori_emiss_sum = np.sum(ori_emiss_path[:]) * 5
    goalEmiss_sum = np.sum(list(goalDict.values())[:]) * 5
    cumEmissReduce = (ori_emiss_sum - goalEmiss_sum)  # tonne
    return [cumEmissReduce, ori_emiss_sum]
    
def set_emissionGoal(ori_emiss_path):
    redeceRatio = [0.02, # 2025
                    0.15, # 2030
                    0.3, # 2035
                    0.49, # 2040
                    0.63, # 2045
                    0.61, # 2050
                    0.51] # 2055
    
    # redeceRatio = [0.7, 0.5, 0.35, 0.15, 0.1, 0.05, 0]
    # redeceRatio = [0.95, 0.85, 0.5, 0.0, -0.1, -0.15, -0.2]
    # redeceRatio = [0.95, 0.85, 0.7, 0.4, 0, -0.35, -0.7]
    
    goalDict = dict()
    emiss = ori_emiss_path[0]
    for yearkey in range(2025,2060,5):
        n = int((yearkey-2025)/5)
        index_path = int((yearkey-2025)/5)
        emiss = (1-redeceRatio[n]) * ori_emiss_path[index_path]
        # print('reduce amount: %.f, %.3f '% (reduceAmount, redeceRatio[n]))
        goalDict[yearkey] = int(emiss)
        # print('emission:%.f'%emiss)
    cumEmissReduce, ori_emiss_sum = cal_culmu(goalDict, ori_emiss_path)
    # plot_emissGoal(goalDict, ori_emiss_path,cumEmissReduce)
    print('reduced cumulemiss: %.f' % cumEmissReduce)
    
    return goalDict

def set_emissionGoal_1(ori_emiss_path, reduceRatioList):
    
    redeceRatio = reduceRatioList
    
    goalDict = dict()
    emiss = ori_emiss_path[0]
    for yearkey in range(2025,2060,5):
        n = int((yearkey-2025)/5)
        index_path = int((yearkey-2025)/5)
        emiss = (1-redeceRatio[n]) * ori_emiss_path[index_path]
        # print('reduce amount: %.f, %.3f '% (reduceAmount, redeceRatio[n]))
        goalDict[yearkey] = int(emiss)
        # print('emission:%.f'%emiss)
    cumEmissReduce = cal_culmu(goalDict, ori_emiss_path)
    # plot_emissGoal(goalDict, ori_emiss_path,cumEmissReduce)
    print('reduced cumulemiss: %.f' % cumEmissReduce)
    
    return [goalDict, cumEmissReduce]

def set_emissionGoal_2(ori_emiss_path, reduceRatioList):
    
    redeceRatio = reduceRatioList
    
    goalDict = dict()
    emiss = ori_emiss_path[0]
    for yearkey in range(2020,2065,5):
        n = int((yearkey-2020)/5)
        index_path = int((yearkey-2020)/5)
        emiss = (1-redeceRatio[yearkey]) * ori_emiss_path[index_path]
        # print('reduce amount: %.f, %.3f '% (reduceAmount, redeceRatio[n]))
        goalDict[yearkey] = int(emiss)
        # print('emission:%.f'%emiss)
    cumEmissReduce, ori_emiss_sum = cal_culmu(goalDict, ori_emiss_path)
    # plot_emissGoal(goalDict, ori_emiss_path,cumEmissReduce)
    print('reduced cumulemiss: %.f' % cumEmissReduce)
    
    return [goalDict, cumEmissReduce, ori_emiss_sum]
    
    