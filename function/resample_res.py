# -*- coding: utf-8 -*-
"""
Created on Mon May 23 15:06:16 2022

@author: vicke
"""

import numpy as np
import pandas as pd

res_1km_GJ = np.load('inputData/bioRes-raw/grossBio_S4_AF11.npy')
res_1km_kwh = res_1km_GJ * 277.8 # 1 GJ = 277.8 kWh
# 重采样数组,输入数据为能源作物数据

tem=np.zeros([200,350])
for i in np.arange(tem.shape[0]):
    for j in np.arange(tem.shape[1]):
        # tem[i*50:(i+1)*50-1,j*50:(j+1)*50-1]=data[i,j]
        tem[i,j]=np.sum(res_1km_kwh[i*20:(i+1)*20,j*20:(j+1)*20])
        # print(tem[i,j])
        
np.save('inputData/res_kwh_20km_S4_AF11', tem)