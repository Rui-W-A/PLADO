# -*- coding: utf-8 -*-
"""
Created on Thu Jan 20 11:43:22 2022

@author: vicke
"""

import numpy as np

def cal_distance(pos1, pos2):
    return np.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)


def generate_disDict(pp_pos, res_loc, radius_limit, resolution):
    disDict = {}
    for i in pp_pos.keys():
        for j in res_loc.keys():
            dis = cal_distance(pp_pos[str(i)], res_loc[str(j)])
            if dis <= radius_limit:
                disDict[(i, j)] = dis * resolution # km
            else:
                pass
    return disDict