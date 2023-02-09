# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 16:09:13 2022

@author: vicke
"""

# this package should include 
# read data formatted as nc, npy, and tif
# resample data as 10 km * 10 km
# generate resDict, exclude 0 value

import pickle
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


bioScale = pow(10,9)

def reclass_matrix_To10km(data_npy):
    data = data_npy.copy()
    tem=np.zeros([400,700])
    for i in np.arange(tem.shape[0]):
        for j in np.arange(tem.shape[1]):
            tem[i,j]=np.sum(data[i*10:(i+1)*10,j*10:(j+1)*10])
    return tem

def reclass_matrix_To20km(data_npy):
    data = data_npy.copy()
    tem=np.zeros([200,350])
    for i in np.arange(tem.shape[0]):
        for j in np.arange(tem.shape[1]):
            tem[i,j]=np.sum(data[i*20:(i+1)*20,j*20:(j+1)*20])
    return tem

def generate_bioDict(bio_filePath):
    # load biomass resources data, npy format
    data_npy = np.load(bio_filePath)
    
    # reclass the matrix to 10km
    # res_matrix = reclass_matrix_To10km(data_npy)
    res_matrix = data_npy.copy()
    res_matrix = res_matrix / bioScale
    
    # exclude 0 value
    bioDict = {}
    counter = 1
    for y in range(len(res_matrix)):
        for x in range(len(res_matrix[y])):
            if res_matrix[y][x] != 0:
                bioDict[str(counter)] = [res_matrix[y][x], (x, y)]
                counter += 1
            else:
                pass
    print('num: %f grid' % counter)
    return bioDict
