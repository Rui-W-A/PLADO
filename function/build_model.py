# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 16:19:27 2022

@author: vicke
"""

from function.cal_cost_sensitivity import LCOE_PP, LCOE_BE, LCOE_BECCS, LCOE_CCS, LCOE_Retire
from function.cal_cost_sensitivity import LCOE_PP1, LCOE_BE1, LCOE_BECCS1, LCOE_CCS1, LCOE_Retire1
from function.cal_emiss import Emiss_PP, Emiss_BE, Emiss_CCS, Emiss_BECCS, Emiss_Retire
import gurobipy as gp
from gurobipy import GRB
import pandas as pd

bioScale = pow(10,9) # 每块用地大概可以生产0-10万亿千瓦时的发电量
emissScale = pow(10,6) # 每个电厂大概能够产生百万级别的碳排放

def build_model_5opt(name, power_station_id, hours, capacity, 
                    lon, lat, operateYear, retrofitYear, set_retrofitYear,
                    ori_lcoeFrame, pixelX, pixelY, dccs, pp_pos, 
                    y_opt, take, cost, emiss, res_point_id, 
                    resources, power2res, distance, EMISS_GOAL, gap_set, BioSupply, emissScale, columnName, unitCoal):
    
    m = gp.Model(name)
    # m.setParam("Method",1) # dual simplex = 0; primary simplex = 1, simplex method is less sensitive to numerical issues
    m.setParam('MIPGap', gap_set)
    # m.setParam('Threads', 16)
    # m.setParam('DualReductions ',0)

    '''
    Variables
    - take
    - upgrade: y1, y2, y3, y4
    - emission variable: z
    '''
    
    # Create decision variables for how much resource through which combination
    take = m.addVars(power2res, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS, name="x")

    # Create decision variables for upgrade way
    y1 = m.addVars(power_station_id, vtype=GRB.BINARY, name="PP")
    y2 = m.addVars(power_station_id, vtype=GRB.BINARY, name="BE")
    y3 = m.addVars(power_station_id, vtype=GRB.BINARY, name="CCS")
    y4 = m.addVars(power_station_id, vtype=GRB.BINARY, name="BECCS")
    y5 = m.addVars(power_station_id, vtype=GRB.BINARY, name="Retire")

    # total cost
    Cost_sum = (gp.quicksum(
        y1[p] * LCOE_PP(capacity[p], hours[p], operateYear[p], set_retrofitYear, columnName) * (capacity[p] * hours[p]/pow(10,9))
        + y2[p] * LCOE_BE(capacity[p], hours[p], take.sum(p, '*'), take.prod(distance, p, "*"), operateYear[p], set_retrofitYear,ori_lcoeFrame[p], columnName) * (capacity[p] * hours[p]/pow(10,9))
        + y3[p] * LCOE_CCS(capacity[p], hours[p], dccs[p], operateYear[p],set_retrofitYear, ori_lcoeFrame[p], columnName)* (capacity[p] * hours[p]/pow(10,9))
        + y4[p] * LCOE_BECCS(capacity[p], hours[p], take.sum(p, '*'), take.prod(distance, p, "*"),dccs[p], operateYear[p], set_retrofitYear, ori_lcoeFrame[p], columnName)* (capacity[p] * hours[p]/pow(10,9))
        + y5[p] * LCOE_Retire(capacity[p], hours[p], operateYear[p], set_retrofitYear,ori_lcoeFrame[p], columnName) * (capacity[p] * hours[p]/pow(10,9))
        for p in power_station_id))
    

    # total emission
    Emiss_sum = (gp.quicksum(
        y1[p] * Emiss_PP(capacity[p], hours[p], operateYear[p], set_retrofitYear, unitCoal[p]) / emissScale
        + y2[p] * Emiss_BE(capacity[p], hours[p], take.sum(p, '*'), take.prod(distance, p, "*"), operateYear[p], set_retrofitYear, unitCoal[p]) / emissScale
        + y3[p] * Emiss_CCS(capacity[p], hours[p], operateYear[p], set_retrofitYear, unitCoal[p]) / emissScale
        + y4[p] * Emiss_BECCS(capacity[p], hours[p], take.sum(p, '*'), take.prod(distance, p, "*"), operateYear[p], set_retrofitYear, unitCoal[p]) / emissScale
        + y5[p] * Emiss_Retire() / emissScale
        for p in power_station_id))

    '''
    Objective
    '''
    m.setObjective(Cost_sum, GRB.MINIMIZE)

    '''
    Constraints
    '''
    # s.t.: (1) emission goal
    m.addConstr(Emiss_sum <= (EMISS_GOAL / emissScale), name="Emiss")

    # s.t.: (2) for each power station, only choose 1 upgrade method
    for p in power_station_id:
        m.addConstr(y1[p] + y2[p] + y3[p] + y4[p] + y5[p] == 1, "one_method")
        # m.addConstr(y1[p] + y2[p] + y3[p] + y4[p] == 1, "one_method")

    # s.t.: (3) for each r_p, take-out <= resource
    for r in res_point_id:
        m.addRange(take.sum('*', r), 0, resources[r], r)
        
    # s.t.: (4) for each pp, supply <= pp demand
    for p in power_station_id:
        m.addConstr(take.sum(p, '*')  <= hours[p]*capacity[p] / bioScale, "-")
        m.addRange(take.sum(p, '*') , 0, hours[p]*capacity[p] / bioScale,  "Limit")
        
    # s.t.: (5) some options cannot take biomass
    M = 10
    for p in power_station_id:
        m.addConstr((take.sum(p,"*") <= M * (1-y1[p])),"pp technology")
        m.addConstr((take.sum(p,"*") <= M * (1-y3[p])),"ccs technology")
        m.addConstr((take.sum(p,"*") <= M * (1-y5[p])),"retire technology")
        
    # s.t.: (6) intertemporal options forbidden
    for p in power_station_id:
        # read the option last time
        yy1 = y_opt[p]
        
        # option 1: PP, no forbidden
        # option 2: BE, forbidden: y1, y3 = 0
        if yy1 ==  'BE':
            m.addConstr((y1[p] == 0), 'forbidden: pp')
            m.addConstr((y3[p] == 0), 'forbidden: ccs')
        # option 3: CCS, forbidden: y1, y2 = 0
        if yy1 == 'CCS':
            m.addConstr((y1[p] == 0), 'forbidden: pp')
            m.addConstr((y2[p] == 0), 'forbidden: be')
        # option 4: BECCS, forbidden: y1,y2,y3 = 0
        if yy1 == 'BECCS':
            m.addConstr((y1[p] == 0), 'forbidden: pp')
            m.addConstr((y2[p] == 0), 'forbidden: be')
            m.addConstr((y3[p] == 0), 'forbidden: ccs')
        # option 5: Retire, forbidden all options
        if yy1 == 'Retire':
            m.addConstr((y1[p] == 0), 'forbidden: pp')
            m.addConstr((y2[p] == 0), 'forbidden: be')
            m.addConstr((y3[p] == 0), 'forbidden: ccs')
            m.addConstr((y4[p] == 0), 'forbidden: beccs')
            
    # s.t.: (7) biomass supply increase stably
    # m.addConstr((take.sum() >= BioSupply), 'biomass supply increase')
    
    # 查看一下模型的参数情况
    # p=m.presolve() # 查看预处理的数值情况
    # p.printStats()
    # m.Params.Presolve=0 # 关掉预处理过程
    # m.Params.Aggregate=0 # 尝试下是否需要aggregate
    # m.Params.AggFill=0 # 如果aggregate有助于数值问题，但让求解变慢，尝试这个选项
    
    m.optimize()
    print(f"model status is:", m.status)
    
    ppOptionRecord = dict()
    pp2ResTake = []

    # https://www.gurobi.com/documentation/9.5/refman/optimization_status_codes.html
    if m.status == GRB.UNBOUNDED: # code:5
        print('!!!The model cannot be solved because it is unbounded!')
        
    elif m.status == GRB.INFEASIBLE: # code: 3
        print("!!!INFEASIBLE")
        vars = m.getVars()
        ubpen = [1.0] * m.numVars
        m.feasRelax(1, False, vars, None, ubpen, None, None)
        m.optimize()
    elif m.status == GRB.INF_OR_UNBD: # code: 4
        print("!!!INF_OR_UNBD, RELAX")
        vars = m.getVars()
        ubpen = [1.0] * m.numVars
        m.feasRelax(1, False, vars, None, ubpen, None, None)
        m.optimize()
     
    elif m.status == GRB.OPTIMAL: # code: 2
        print('!!!The optimal objective is %g' % m.objVal)
        upgrade_map = {0: 'PP', 1:'BE', 2:'CCS', 3:'BECCS', 4:'Retire'}
        
        for p in power_station_id:
            up = upgrade_map[
                [y1[p].x, y2[p].x, y3[p].x, y4[p].x, y5[p].x].index(
                    max([y1[p].x, y2[p].x, y3[p].x, y4[p].x, y5[p].x]))]
            # up = upgrade_map[
            #     [y1[p].x, y2[p].x, y3[p].x, y4[p].x,].index(
            #         max([y1[p].x, y2[p].x, y3[p].x, y4[p].x]))]
            
            takeRes = take.sum(p,'*').getValue()
            
            costValue = 0.
            emissValue = 0.
            cost_dataFrame = pd.DataFrame()
            
            if up == "PP":
                costValue, cost_dataFrame = LCOE_PP1(capacity[p], hours[p], operateYear[p], set_retrofitYear, columnName)
                emissValue = Emiss_PP(capacity[p], hours[p], operateYear[p], set_retrofitYear, unitCoal[p])
                
            elif up == "BE":
                costValue, cost_dataFrame = LCOE_BE1(capacity[p], hours[p], take.sum(p, '*').getValue(), 
                              take.prod(distance, p, "*").getValue(), operateYear[p], set_retrofitYear, ori_lcoeFrame[p], columnName)
                emissValue = Emiss_BE(capacity[p], hours[p], take.sum(p, '*').getValue(),
                                              take.prod(distance, p, "*").getValue(), operateYear[p], set_retrofitYear, unitCoal[p])
            elif up == "CCS":
                costValue, cost_dataFrame = LCOE_CCS1(capacity[p], hours[p], dccs[p], operateYear[p],
                                                      set_retrofitYear, ori_lcoeFrame[p], columnName)
                emissValue = Emiss_CCS(capacity[p], hours[p], operateYear[p], set_retrofitYear, unitCoal[p])
            elif up == "BECCS":
                costValue, cost_dataFrame = LCOE_BECCS1(capacity[p], hours[p],take.sum(p, '*').getValue(), take.prod(distance, p, "*").getValue(), dccs[p], operateYear[p],
                                 set_retrofitYear, ori_lcoeFrame[p], columnName)
                emissValue = Emiss_BECCS(capacity[p], hours[p], take.sum(p, '*').getValue(), take.prod(distance, p, "*").getValue(), operateYear[p], set_retrofitYear, unitCoal[p])
            elif up == "Retire":
                costValue, cost_dataFrame = LCOE_Retire1(capacity[p], hours[p], operateYear[p], set_retrofitYear, ori_lcoeFrame[p], columnName)
                emissValue = Emiss_Retire()
            
            # ppOptionRecord[p] = [up, takeRes, costValue, emissValue, cost_dataFrame]
            ppOptionRecord.update({p:[up, takeRes, costValue, emissValue, cost_dataFrame]})
            # print(p)
            
        # record residues
        print("take_pairs:")
        for c in power2res:
            pp_id = float(c[0])
            res_id = float(c[1])
            take_value = take[c].x
            pp2ResTake.append([pp_id, res_id, take_value]) 
            # if take_value > 0.0:
            #     pp2ResTake.append([pp_id, res_id, take_value]) 
            
            # pp2ResTake[c] = [pp_id, res_id, take_value]
        # print(pp2ResTake)
        
    elif m.status != GRB.INF_OR_UNBD and m.status != GRB.INFEASIBLE:
        print('!!!Optimization was stopped with status %d' % m.status)

    return ppOptionRecord, pp2ResTake


def build_model_Retire(name, power_station_id, hours, capacity, 
                    lon, lat, operateYear, retrofitYear, set_retrofitYear,
                    ori_lcoeFrame, pixelX, pixelY, dccs, pp_pos, 
                    y_opt, take, cost, emiss, res_point_id, 
                    resources, power2res, distance, EMISS_GOAL, gap_set, BioSupply, emissScale, columnName, unitCoal):
    
    m = gp.Model(name)
    # m.setParam("Method",1) # dual simplex = 0; primary simplex = 1, simplex method is less sensitive to numerical issues
    m.setParam('MIPGap', gap_set)
    # m.setParam('Threads', 16)
    
    # m.setParam('DualReductions ',0)

    '''
    Variables
    - take
    - upgrade: y1, y5
    - emission variable: z
    '''
    y1 = m.addVars(power_station_id, vtype=GRB.BINARY, name="PP")
    y5 = m.addVars(power_station_id, vtype=GRB.BINARY, name="Retire")

    # total cost
    Cost_sum = (gp.quicksum(
        y1[p] * LCOE_PP(capacity[p], hours[p], operateYear[p], set_retrofitYear, columnName) * (capacity[p] * hours[p]/pow(10,9))
        + y5[p] * LCOE_Retire(capacity[p], hours[p], operateYear[p], set_retrofitYear,ori_lcoeFrame[p], columnName) * (capacity[p] * hours[p]/pow(10,9))
        for p in power_station_id))

    # total emission
    Emiss_sum = (gp.quicksum(
        y1[p] * Emiss_PP(capacity[p], hours[p], operateYear[p], set_retrofitYear, unitCoal[p]) / emissScale
        + y5[p] * Emiss_Retire() / emissScale
        for p in power_station_id))

    '''
    Objective
    '''
    m.setObjective(Cost_sum, GRB.MINIMIZE)

    '''
    Constraints
    '''
    # s.t.: (1) emission goal
    m.addConstr(Emiss_sum <= (EMISS_GOAL / emissScale), name="Emiss")

    # s.t.: (2) for each power station, only choose 1 upgrade method
    for p in power_station_id:
        m.addConstr(y1[p] + y5[p] == 1, "one_method")
        
    # s.t.: (6) intertemporal options forbidden
    for p in power_station_id:
        # read the option last time
        yy1 = y_opt[p]
        
        # option 1: PP, no forbidden
        # option 5: Retire, forbidden all options
        if yy1 == 'Retire':
            m.addConstr((y1[p] == 0), 'forbidden: pp')
    
    # 查看一下模型的参数情况
    # p=m.presolve() # 查看预处理的数值情况
    # p.printStats()
    # m.Params.Presolve=0 # 关掉预处理过程
    # m.Params.Aggregate=0 # 尝试下是否需要aggregate
    # m.Params.AggFill=0 # 如果aggregate有助于数值问题，但让求解变慢，尝试这个选项
    
    m.optimize()
    print(f"model status is:", m.status)
    
    ppOptionRecord = dict()
    pp2ResTake = []

    # https://www.gurobi.com/documentation/9.5/refman/optimization_status_codes.html
    if m.status == GRB.UNBOUNDED: # code:5
        print('!!!The model cannot be solved because it is unbounded!')
        
    elif m.status == GRB.INFEASIBLE: # code: 3
        print("!!!INFEASIBLE")
        vars = m.getVars()
        ubpen = [1.0] * m.numVars
        m.feasRelax(1, False, vars, None, ubpen, None, None)
        m.optimize()
    elif m.status == GRB.INF_OR_UNBD: # code: 4
        print("!!!INF_OR_UNBD, RELAX")
        vars = m.getVars()
        ubpen = [1.0] * m.numVars
        m.feasRelax(1, False, vars, None, ubpen, None, None)
        m.optimize()
     
    elif m.status == GRB.OPTIMAL: # code: 2
        print('!!!The optimal objective is %g' % m.objVal)
        upgrade_map = {0: 'PP', 1:'Retire'}
        
        for p in power_station_id:
            up = upgrade_map[
                [y1[p].x, y5[p].x].index(
                    max([y1[p].x,  y5[p].x]))]
            
            costValue = 0.
            emissValue = 0.
            cost_dataFrame = pd.DataFrame()
            
            if up == "PP":
                costValue, cost_dataFrame = LCOE_PP1(capacity[p], hours[p], operateYear[p], set_retrofitYear, columnName)
                emissValue = Emiss_PP(capacity[p], hours[p], operateYear[p], set_retrofitYear, unitCoal[p])
                
            elif up == "Retire":
                costValue, cost_dataFrame = LCOE_Retire1(capacity[p], hours[p], operateYear[p], set_retrofitYear, ori_lcoeFrame[p], columnName)
                emissValue = Emiss_Retire()
                
            takeRes = 0.
            # ppOptionRecord[p] = [up, takeRes, costValue, emissValue, cost_dataFrame]
            ppOptionRecord.update({p:[up, takeRes, costValue, emissValue, cost_dataFrame]})
            # print(p)
        
    elif m.status != GRB.INF_OR_UNBD and m.status != GRB.INFEASIBLE:
        print('!!!Optimization was stopped with status %d' % m.status)

    return ppOptionRecord, pp2ResTake

def build_model_BE(name, power_station_id, hours, capacity, 
                    lon, lat, operateYear, retrofitYear, set_retrofitYear,
                    ori_lcoeFrame, pixelX, pixelY, dccs, pp_pos, 
                    y_opt, take, cost, emiss, res_point_id, 
                    resources, power2res, distance, EMISS_GOAL, gap_set, BioSupply, emissScale, columnName, unitCoal):
    
    m = gp.Model(name)
    # m.setParam("Method",1) # dual simplex = 0; primary simplex = 1, simplex method is less sensitive to numerical issues
    m.setParam('MIPGap', gap_set)
    # m.setParam('Threads', 16)
    # m.setParam('DualReductions ',0)

    '''
    Variables
    - take
    - upgrade: y1, y2, y3, y4
    - emission variable: z
    '''
    
    # Create decision variables for how much resource through which combination
    take = m.addVars(power2res, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS, name="x")

    # Create decision variables for upgrade way
    y1 = m.addVars(power_station_id, vtype=GRB.BINARY, name="PP")
    y2 = m.addVars(power_station_id, vtype=GRB.BINARY, name="BE")
    y5 = m.addVars(power_station_id, vtype=GRB.BINARY, name="Retire")

    # total cost
    Cost_sum = (gp.quicksum(
        y1[p] * LCOE_PP(capacity[p], hours[p], operateYear[p], set_retrofitYear, columnName) * (capacity[p] * hours[p]/pow(10,9))
        + y2[p] * LCOE_BE(capacity[p], hours[p], take.sum(p, '*'), take.prod(distance, p, "*"), operateYear[p], set_retrofitYear,ori_lcoeFrame[p], columnName) * (capacity[p] * hours[p]/pow(10,9))
        + y5[p] * LCOE_Retire(capacity[p], hours[p], operateYear[p], set_retrofitYear,ori_lcoeFrame[p], columnName) * (capacity[p] * hours[p]/pow(10,9))
        for p in power_station_id))
    

    # total emission
    Emiss_sum = (gp.quicksum(
        y1[p] * Emiss_PP(capacity[p], hours[p], operateYear[p], set_retrofitYear, unitCoal[p]) / emissScale
        + y2[p] * Emiss_BE(capacity[p], hours[p], take.sum(p, '*'), take.prod(distance, p, "*"), operateYear[p], set_retrofitYear, unitCoal[p]) / emissScale
        + y5[p] * Emiss_Retire() / emissScale
        for p in power_station_id))

    '''
    Objective
    '''
    m.setObjective(Cost_sum, GRB.MINIMIZE)

    '''
    Constraints
    '''
    # s.t.: (1) emission goal
    m.addConstr(Emiss_sum <= (EMISS_GOAL / emissScale), name="Emiss")

    # s.t.: (2) for each power station, only choose 1 upgrade method
    for p in power_station_id:
        m.addConstr(y1[p] + y2[p] + y5[p] == 1, "one_method")
        # m.addConstr(y1[p] + y2[p] + y3[p] + y4[p] == 1, "one_method")

    # s.t.: (3) for each r_p, take-out <= resource
    for r in res_point_id:
        m.addRange(take.sum('*', r), 0, resources[r], r)
        
    # s.t.: (4) for each pp, supply <= pp demand
    for p in power_station_id:
        m.addConstr(take.sum(p, '*')  <= hours[p]*capacity[p] / bioScale, "-")
        m.addRange(take.sum(p, '*') , 0, hours[p]*capacity[p] / bioScale,  "Limit")
        
    # s.t.: (5) some options cannot take biomass
    M = 10
    for p in power_station_id:
        m.addConstr((take.sum(p,"*") <= M * (1-y1[p])),"pp technology")
        
    # s.t.: (6) intertemporal options forbidden
    for p in power_station_id:
        # read the option last time
        yy1 = y_opt[p]
        
        # option 1: PP, no forbidden
        # option 2: BE, forbidden: y1, y3 = 0
        if yy1 ==  'BE':
            m.addConstr((y1[p] == 0), 'forbidden: pp')
        # option 5: Retire, forbidden all options
        if yy1 == 'Retire':
            m.addConstr((y1[p] == 0), 'forbidden: pp')
            m.addConstr((y2[p] == 0), 'forbidden: be')
        # option 3: CCS, forbidden: y1, y2 = 0
            
    # s.t.: (7) biomass supply increase stably
    # m.addConstr((take.sum() >= BioSupply), 'biomass supply increase')
    
    # 查看一下模型的参数情况
    # p=m.presolve() # 查看预处理的数值情况
    # p.printStats()
    # m.Params.Presolve=0 # 关掉预处理过程
    # m.Params.Aggregate=0 # 尝试下是否需要aggregate
    # m.Params.AggFill=0 # 如果aggregate有助于数值问题，但让求解变慢，尝试这个选项
    
    m.optimize()
    print(f"model status is:", m.status)
    
    ppOptionRecord = dict()
    pp2ResTake = []

    # https://www.gurobi.com/documentation/9.5/refman/optimization_status_codes.html
    if m.status == GRB.UNBOUNDED: # code:5
        print('!!!The model cannot be solved because it is unbounded!')
        
    elif m.status == GRB.INFEASIBLE: # code: 3
        print("!!!INFEASIBLE")
        vars = m.getVars()
        ubpen = [1.0] * m.numVars
        m.feasRelax(1, False, vars, None, ubpen, None, None)
        m.optimize()
    elif m.status == GRB.INF_OR_UNBD: # code: 4
        print("!!!INF_OR_UNBD, RELAX")
        vars = m.getVars()
        ubpen = [1.0] * m.numVars
        m.feasRelax(1, False, vars, None, ubpen, None, None)
        m.optimize()
     
    elif m.status == GRB.OPTIMAL: # code: 2
        print('!!!The optimal objective is %g' % m.objVal)
        upgrade_map = {0: 'PP', 1:'BE', 2:'CCS', 3:'BECCS', 4:'Retire'}
        
        for p in power_station_id:
            up = upgrade_map[
                [y1[p].x, y2[p].x].index(
                    max([y1[p].x, y2[p].x]))]
            
            takeRes = take.sum(p,'*').getValue()
            
            costValue = 0.
            emissValue = 0.
            cost_dataFrame = pd.DataFrame()
            
            if up == "PP":
                costValue, cost_dataFrame = LCOE_PP1(capacity[p], hours[p], operateYear[p], set_retrofitYear, columnName)
                emissValue = Emiss_PP(capacity[p], hours[p], operateYear[p], set_retrofitYear, unitCoal[p])
                
            elif up == "BE":
                costValue, cost_dataFrame = LCOE_BE1(capacity[p], hours[p], take.sum(p, '*').getValue(), 
                              take.prod(distance, p, "*").getValue(), operateYear[p], set_retrofitYear, ori_lcoeFrame[p], columnName)
                emissValue = Emiss_BE(capacity[p], hours[p], take.sum(p, '*').getValue(),
                                              take.prod(distance, p, "*").getValue(), operateYear[p], set_retrofitYear, unitCoal[p])
            elif up == "Retire":
                costValue, cost_dataFrame = LCOE_Retire1(capacity[p], hours[p], operateYear[p], set_retrofitYear, ori_lcoeFrame[p], columnName)
                emissValue = Emiss_Retire()
            # ppOptionRecord[p] = [up, takeRes, costValue, emissValue, cost_dataFrame]
            ppOptionRecord.update({p:[up, takeRes, costValue, emissValue, cost_dataFrame]})
            # print(p)
            
        # record residues
        print("take_pairs:")
        for c in power2res:
            pp_id = float(c[0])
            res_id = float(c[1])
            take_value = take[c].x
            pp2ResTake.append([pp_id, res_id, take_value]) 
            # if take_value > 0.0:
            #     pp2ResTake.append([pp_id, res_id, take_value]) 
            
            # pp2ResTake[c] = [pp_id, res_id, take_value]
        # print(pp2ResTake)
        
    elif m.status != GRB.INF_OR_UNBD and m.status != GRB.INFEASIBLE:
        print('!!!Optimization was stopped with status %d' % m.status)

    return ppOptionRecord, pp2ResTake


def build_model_CCS(name, power_station_id, hours, capacity, 
                    lon, lat, operateYear, retrofitYear, set_retrofitYear,
                    ori_lcoeFrame, pixelX, pixelY, dccs, pp_pos, 
                    y_opt, take, cost, emiss, res_point_id, 
                    resources, power2res, distance, EMISS_GOAL, gap_set, BioSupply, emissScale, columnName, unitCoal):
    
    m = gp.Model(name)
    # m.setParam("Method",1) # dual simplex = 0; primary simplex = 1, simplex method is less sensitive to numerical issues
    m.setParam('MIPGap', gap_set)
    # m.setParam('Threads', 16)
    # m.setParam('DualReductions ',0)

    '''
    Variables
    - take
    - upgrade: y1, y2, y3, y4
    - emission variable: z
    '''
    
    # Create decision variables for how much resource through which combination
    take = m.addVars(power2res, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS, name="x")

    # Create decision variables for upgrade way
    y1 = m.addVars(power_station_id, vtype=GRB.BINARY, name="PP")
    y3 = m.addVars(power_station_id, vtype=GRB.BINARY, name="CCS")
    y5 = m.addVars(power_station_id, vtype=GRB.BINARY, name="Retire")

    # total cost
    Cost_sum = (gp.quicksum(
        y1[p] * LCOE_PP(capacity[p], hours[p], operateYear[p], set_retrofitYear, columnName) * (capacity[p] * hours[p]/pow(10,9))
        + y3[p] * LCOE_CCS(capacity[p], hours[p], dccs[p], operateYear[p],set_retrofitYear, ori_lcoeFrame[p], columnName)* (capacity[p] * hours[p]/pow(10,9))
        + y5[p] * LCOE_Retire(capacity[p], hours[p], operateYear[p], set_retrofitYear,ori_lcoeFrame[p], columnName) * (capacity[p] * hours[p]/pow(10,9))
        for p in power_station_id))
    

    # total emission
    Emiss_sum = (gp.quicksum(
        y1[p] * Emiss_PP(capacity[p], hours[p], operateYear[p], set_retrofitYear, unitCoal[p]) / emissScale
        + y3[p] * Emiss_CCS(capacity[p], hours[p], operateYear[p], set_retrofitYear, unitCoal[p]) / emissScale
        + y5[p] * Emiss_Retire() / emissScale
        for p in power_station_id))

    '''
    Objective
    '''
    m.setObjective(Cost_sum, GRB.MINIMIZE)

    '''
    Constraints
    '''
    # s.t.: (1) emission goal
    m.addConstr(Emiss_sum <= (EMISS_GOAL / emissScale), name="Emiss")

    # s.t.: (2) for each power station, only choose 1 upgrade method
    for p in power_station_id:
        m.addConstr(y1[p] + y3[p] +y5[p] == 1, "one_method")
        # m.addConstr(y1[p] + y2[p] + y3[p] + y4[p] == 1, "one_method")

    # s.t.: (3) for each r_p, take-out <= resource
    for r in res_point_id:
        m.addRange(take.sum('*', r), 0, resources[r], r)
        
    # s.t.: (4) for each pp, supply <= pp demand
    for p in power_station_id:
        m.addConstr(take.sum(p, '*')  <= hours[p]*capacity[p] / bioScale, "-")
        m.addRange(take.sum(p, '*') , 0, hours[p]*capacity[p] / bioScale,  "Limit")
        
    # s.t.: (5) some options cannot take biomass
    M = 10
    for p in power_station_id:
        m.addConstr((take.sum(p,"*") <= M * (1-y1[p])),"pp technology")
        m.addConstr((take.sum(p,"*") <= M * (1-y3[p])),"ccs technology")
        
        
    # s.t.: (6) intertemporal options forbidden
    for p in power_station_id:
        # read the option last time
        yy1 = y_opt[p]
        
        # option 3: CCS, forbidden: y1, y2 = 0
        if yy1 == 'CCS':
            m.addConstr((y1[p] == 0), 'forbidden: pp')
        # option 4: BECCS, forbidden: y1,y2,y3 = 0
        if yy1 == 'Retire':
            m.addConstr((y1[p] == 0), 'forbidden: pp')
            m.addConstr((y3[p] == 0), 'forbidden: ccs')
            
    # s.t.: (7) biomass supply increase stably
    # m.addConstr((take.sum() >= BioSupply), 'biomass supply increase')
    
    # 查看一下模型的参数情况
    # p=m.presolve() # 查看预处理的数值情况
    # p.printStats()
    # m.Params.Presolve=0 # 关掉预处理过程
    # m.Params.Aggregate=0 # 尝试下是否需要aggregate
    # m.Params.AggFill=0 # 如果aggregate有助于数值问题，但让求解变慢，尝试这个选项
    
    m.optimize()
    print(f"model status is:", m.status)
    
    ppOptionRecord = dict()
    pp2ResTake = []

    # https://www.gurobi.com/documentation/9.5/refman/optimization_status_codes.html
    if m.status == GRB.UNBOUNDED: # code:5
        print('!!!The model cannot be solved because it is unbounded!')
        
    elif m.status == GRB.INFEASIBLE: # code: 3
        print("!!!INFEASIBLE")
        vars = m.getVars()
        ubpen = [1.0] * m.numVars
        m.feasRelax(1, False, vars, None, ubpen, None, None)
        m.optimize()
    elif m.status == GRB.INF_OR_UNBD: # code: 4
        print("!!!INF_OR_UNBD, RELAX")
        vars = m.getVars()
        ubpen = [1.0] * m.numVars
        m.feasRelax(1, False, vars, None, ubpen, None, None)
        m.optimize()
     
    elif m.status == GRB.OPTIMAL: # code: 2
        print('!!!The optimal objective is %g' % m.objVal)
        upgrade_map = {0: 'PP', 1:'BE', 2:'CCS', 3:'BECCS', 4:'Retire'}
        
        for p in power_station_id:
            up = upgrade_map[
                [y1[p].x, y3[p].x].index(
                    max([y1[p].x, y3[p].x]))]
            
            takeRes = take.sum(p,'*').getValue()
            
            costValue = 0.
            emissValue = 0.
            cost_dataFrame = pd.DataFrame()
            
            if up == "PP":
                costValue, cost_dataFrame = LCOE_PP1(capacity[p], hours[p], operateYear[p], set_retrofitYear, columnName)
                emissValue = Emiss_PP(capacity[p], hours[p], operateYear[p], set_retrofitYear, unitCoal[p])
                
            elif up == "CCS":
                costValue, cost_dataFrame = LCOE_CCS1(capacity[p], hours[p], dccs[p], operateYear[p],
                                                      set_retrofitYear, ori_lcoeFrame[p], columnName)
                emissValue = Emiss_CCS(capacity[p], hours[p], operateYear[p], set_retrofitYear, unitCoal[p])
            elif up == "Retire":
                costValue, cost_dataFrame = LCOE_Retire1(capacity[p], hours[p], operateYear[p], set_retrofitYear, ori_lcoeFrame[p], columnName)
                emissValue = Emiss_Retire()     
            
            # ppOptionRecord[p] = [up, takeRes, costValue, emissValue, cost_dataFrame]
            ppOptionRecord.update({p:[up, takeRes, costValue, emissValue, cost_dataFrame]})
            # print(p)
            
        # record residues
        print("take_pairs:")
        for c in power2res:
            pp_id = float(c[0])
            res_id = float(c[1])
            take_value = take[c].x
            pp2ResTake.append([pp_id, res_id, take_value]) 
            # if take_value > 0.0:
            #     pp2ResTake.append([pp_id, res_id, take_value]) 
            
            # pp2ResTake[c] = [pp_id, res_id, take_value]
        # print(pp2ResTake)
        
    elif m.status != GRB.INF_OR_UNBD and m.status != GRB.INFEASIBLE:
        print('!!!Optimization was stopped with status %d' % m.status)

    return ppOptionRecord, pp2ResTake


def build_model_BECCS(name, power_station_id, hours, capacity, 
                    lon, lat, operateYear, retrofitYear, set_retrofitYear,
                    ori_lcoeFrame, pixelX, pixelY, dccs, pp_pos, 
                    y_opt, take, cost, emiss, res_point_id, 
                    resources, power2res, distance, EMISS_GOAL, gap_set, BioSupply, emissScale, columnName, unitCoal):
    
    m = gp.Model(name)
    # m.setParam("Method",1) # dual simplex = 0; primary simplex = 1, simplex method is less sensitive to numerical issues
    m.setParam('MIPGap', gap_set)
    # m.setParam('Threads', 16)
    # m.setParam('DualReductions ',0)

    '''
    Variables
    - take
    - upgrade: y1, y2, y3, y4
    - emission variable: z
    '''
    
    # Create decision variables for how much resource through which combination
    take = m.addVars(power2res, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS, name="x")

    # Create decision variables for upgrade way
    y1 = m.addVars(power_station_id, vtype=GRB.BINARY, name="PP")
    y4 = m.addVars(power_station_id, vtype=GRB.BINARY, name="BECCS")
    y5 = m.addVars(power_station_id, vtype=GRB.BINARY, name="Retire")

    # total cost
    Cost_sum = (gp.quicksum(
        y1[p] * LCOE_PP(capacity[p], hours[p], operateYear[p], set_retrofitYear, columnName) * (capacity[p] * hours[p]/pow(10,9))
        + y4[p] * LCOE_BECCS(capacity[p], hours[p], take.sum(p, '*'), take.prod(distance, p, "*"),dccs[p], operateYear[p], set_retrofitYear, ori_lcoeFrame[p], columnName)* (capacity[p] * hours[p]/pow(10,9))
        + y5[p] * LCOE_Retire(capacity[p], hours[p], operateYear[p], set_retrofitYear,ori_lcoeFrame[p], columnName) * (capacity[p] * hours[p]/pow(10,9))
        for p in power_station_id))

    # total emission
    Emiss_sum = (gp.quicksum(
        y1[p] * Emiss_PP(capacity[p], hours[p], operateYear[p], set_retrofitYear, unitCoal[p]) / emissScale
        + y4[p] * Emiss_BECCS(capacity[p], hours[p], take.sum(p, '*'), take.prod(distance, p, "*"), operateYear[p], set_retrofitYear, unitCoal[p]) / emissScale
        + y5[p] * Emiss_Retire() / emissScale
        for p in power_station_id))

    '''
    Objective
    '''
    m.setObjective(Cost_sum, GRB.MINIMIZE)

    '''
    Constraints
    '''
    # s.t.: (1) emission goal
    m.addConstr(Emiss_sum <= (EMISS_GOAL / emissScale), name="Emiss")

    # s.t.: (2) for each power station, only choose 1 upgrade method
    for p in power_station_id:
        m.addConstr(y1[p] + y4[p] + y5[p] == 1, "one_method")
        # m.addConstr(y1[p] + y2[p] + y3[p] + y4[p] == 1, "one_method")

    # s.t.: (3) for each r_p, take-out <= resource
    for r in res_point_id:
        m.addRange(take.sum('*', r), 0, resources[r], r)
        
    # s.t.: (4) for each pp, supply <= pp demand
    for p in power_station_id:
        m.addConstr(take.sum(p, '*')  <= hours[p]*capacity[p] / bioScale, "-")
        m.addRange(take.sum(p, '*') , 0, hours[p]*capacity[p] / bioScale,  "Limit")
        
    # s.t.: (5) some options cannot take biomass
    M = 10
    for p in power_station_id:
        m.addConstr((take.sum(p,"*") <= M * (1-y1[p])),"pp technology")
        
    # s.t.: (6) intertemporal options forbidden
    for p in power_station_id:
        # read the option last time
        yy1 = y_opt[p]
        
        # option 1: PP, no forbidden
        # option 2: BE, forbidden: y1, y3 = 0
        # option 3: CCS, forbidden: y1, y2 = 0
        # option 4: BECCS, forbidden: y1,y2,y3 = 0
        if yy1 == 'BECCS':
            m.addConstr((y1[p] == 0), 'forbidden: pp')
        if yy1 == 'Retire':
            m.addConstr((y1[p] == 0), 'forbidden: pp')
            m.addConstr((y4[p] == 0), 'forbidden: beccs')
            
    # s.t.: (7) biomass supply increase stably
    # m.addConstr((take.sum() >= BioSupply), 'biomass supply increase')
    
    # 查看一下模型的参数情况
    # p=m.presolve() # 查看预处理的数值情况
    # p.printStats()
    # m.Params.Presolve=0 # 关掉预处理过程
    # m.Params.Aggregate=0 # 尝试下是否需要aggregate
    # m.Params.AggFill=0 # 如果aggregate有助于数值问题，但让求解变慢，尝试这个选项
    
    m.optimize()
    print(f"model status is:", m.status)
    
    ppOptionRecord = dict()
    pp2ResTake = []

    # https://www.gurobi.com/documentation/9.5/refman/optimization_status_codes.html
    if m.status == GRB.UNBOUNDED: # code:5
        print('!!!The model cannot be solved because it is unbounded!')
        
    elif m.status == GRB.INFEASIBLE: # code: 3
        print("!!!INFEASIBLE")
        vars = m.getVars()
        ubpen = [1.0] * m.numVars
        m.feasRelax(1, False, vars, None, ubpen, None, None)
        m.optimize()
    elif m.status == GRB.INF_OR_UNBD: # code: 4
        print("!!!INF_OR_UNBD, RELAX")
        vars = m.getVars()
        ubpen = [1.0] * m.numVars
        m.feasRelax(1, False, vars, None, ubpen, None, None)
        m.optimize()
     
    elif m.status == GRB.OPTIMAL: # code: 2
        print('!!!The optimal objective is %g' % m.objVal)
        upgrade_map = {0: 'PP', 1:'BE', 2:'CCS', 3:'BECCS', 4:'Retire'}
        
        for p in power_station_id:
            up = upgrade_map[
                [y1[p].x, y4[p].x].index(
                    max([y1[p].x, y4[p].x]))]
            # up = upgrade_map[
            #     [y1[p].x, y2[p].x, y3[p].x, y4[p].x,].index(
            #         max([y1[p].x, y2[p].x, y3[p].x, y4[p].x]))]
            
            takeRes = take.sum(p,'*').getValue()
            
            costValue = 0.
            emissValue = 0.
            cost_dataFrame = pd.DataFrame()
            
            if up == "PP":
                costValue, cost_dataFrame = LCOE_PP1(capacity[p], hours[p], operateYear[p], set_retrofitYear, columnName)
                emissValue = Emiss_PP(capacity[p], hours[p], operateYear[p], set_retrofitYear, unitCoal[p])
                

            elif up == "BECCS":
                costValue, cost_dataFrame = LCOE_BECCS1(capacity[p], hours[p],take.sum(p, '*').getValue(), take.prod(distance, p, "*").getValue(), dccs[p], operateYear[p],
                                 set_retrofitYear, ori_lcoeFrame[p], columnName)
                emissValue = Emiss_BECCS(capacity[p], hours[p], take.sum(p, '*').getValue(), take.prod(distance, p, "*").getValue(), operateYear[p], set_retrofitYear, unitCoal[p])
            elif up == "Retire":
                costValue, cost_dataFrame = LCOE_Retire1(capacity[p], hours[p], operateYear[p], set_retrofitYear, ori_lcoeFrame[p], columnName)
                emissValue = Emiss_Retire()    
                
            # ppOptionRecord[p] = [up, takeRes, costValue, emissValue, cost_dataFrame]
            ppOptionRecord.update({p:[up, takeRes, costValue, emissValue, cost_dataFrame]})
            # print(p)
            
        # record residues
        print("take_pairs:")
        for c in power2res:
            pp_id = float(c[0])
            res_id = float(c[1])
            take_value = take[c].x
            pp2ResTake.append([pp_id, res_id, take_value]) 
            # if take_value > 0.0:
            #     pp2ResTake.append([pp_id, res_id, take_value]) 
            
            # pp2ResTake[c] = [pp_id, res_id, take_value]
        # print(pp2ResTake)
        
    elif m.status != GRB.INF_OR_UNBD and m.status != GRB.INFEASIBLE:
        print('!!!Optimization was stopped with status %d' % m.status)

    return ppOptionRecord, pp2ResTake



def build_model_Retrofit(name, power_station_id, hours, capacity, 
                    lon, lat, operateYear, retrofitYear, set_retrofitYear,
                    ori_lcoeFrame, pixelX, pixelY, dccs, pp_pos, 
                    y_opt, take, cost, emiss, res_point_id, 
                    resources, power2res, distance, EMISS_GOAL, gap_set, BioSupply, emissScale, columnName, unitCoal):
    
    m = gp.Model(name)
    # m.setParam("Method",1) # dual simplex = 0; primary simplex = 1, simplex method is less sensitive to numerical issues
    m.setParam('MIPGap', gap_set)
    # m.setParam('Threads', 16)
    
    # m.setParam('DualReductions ',0)

    '''
    Variables
    - take
    - upgrade: y1, y2, y3, y4
    - emission variable: z
    '''
    
    # Create decision variables for how much resource through which combination
    take = m.addVars(power2res, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS, name="x")

    # Create decision variables for upgrade way
    y1 = m.addVars(power_station_id, vtype=GRB.BINARY, name="PP")
    y2 = m.addVars(power_station_id, vtype=GRB.BINARY, name="BE")
    y3 = m.addVars(power_station_id, vtype=GRB.BINARY, name="CCS")
    y4 = m.addVars(power_station_id, vtype=GRB.BINARY, name="BECCS")

    # total cost
    Cost_sum = (gp.quicksum(
        y1[p] * LCOE_PP(capacity[p], hours[p], operateYear[p], set_retrofitYear, columnName) * (capacity[p] * hours[p]/pow(10,9))
        + y2[p] * LCOE_BE(capacity[p], hours[p], take.sum(p, '*'), take.prod(distance, p, "*"), operateYear[p], set_retrofitYear,ori_lcoeFrame[p], columnName) * (capacity[p] * hours[p]/pow(10,9))
        + y3[p] * LCOE_CCS(capacity[p], hours[p], dccs[p], operateYear[p],set_retrofitYear, ori_lcoeFrame[p], columnName)* (capacity[p] * hours[p]/pow(10,9))
        + y4[p] * LCOE_BECCS(capacity[p], hours[p], take.sum(p, '*'), take.prod(distance, p, "*"),dccs[p], operateYear[p], set_retrofitYear, ori_lcoeFrame[p], columnName)* (capacity[p] * hours[p]/pow(10,9))
        for p in power_station_id))

    # total emission
    Emiss_sum = (gp.quicksum(
        y1[p] * Emiss_PP(capacity[p], hours[p], operateYear[p], set_retrofitYear, unitCoal[p]) / emissScale
        + y2[p] * Emiss_BE(capacity[p], hours[p], take.sum(p, '*'), take.prod(distance, p, "*"), operateYear[p], set_retrofitYear, unitCoal[p]) / emissScale
        + y3[p] * Emiss_CCS(capacity[p], hours[p], operateYear[p], set_retrofitYear, unitCoal[p]) / emissScale
        + y4[p] * Emiss_BECCS(capacity[p], hours[p], take.sum(p, '*'), take.prod(distance, p, "*"), operateYear[p], set_retrofitYear, unitCoal[p]) / emissScale
        for p in power_station_id))

    '''
    Objective
    '''
    m.setObjective(Cost_sum, GRB.MINIMIZE)

    '''
    Constraints
    '''
    # s.t.: (1) emission goal
    m.addConstr(Emiss_sum <= (EMISS_GOAL / emissScale), name="Emiss")

    # s.t.: (2) for each power station, only choose 1 upgrade method
    for p in power_station_id:
        m.addConstr(y1[p] + y2[p] + y3[p] + y4[p] == 1, "one_method")
        # m.addConstr(y1[p] + y2[p] + y3[p] + y4[p] == 1, "one_method")

    # s.t.: (3) for each r_p, take-out <= resource
    for r in res_point_id:
        m.addRange(take.sum('*', r), 0, resources[r], r)
        
    # s.t.: (4) for each pp, supply <= pp demand
    for p in power_station_id:
        m.addConstr(take.sum(p, '*')  <= hours[p]*capacity[p] / bioScale, "-")
        m.addRange(take.sum(p, '*') , 0, hours[p]*capacity[p] / bioScale,  "Limit")
        
    # s.t.: (5) some options cannot take biomass
    M = 10
    for p in power_station_id:
        m.addConstr((take.sum(p,"*") <= M * (1-y1[p])),"pp technology")
        m.addConstr((take.sum(p,"*") <= M * (1-y3[p])),"ccs technology")
        
    # s.t.: (6) intertemporal options forbidden
    for p in power_station_id:
        # read the option last time
        yy1 = y_opt[p]
        
        # option 1: PP, no forbidden
        # option 2: BE, forbidden: y1, y3 = 0
        if yy1 ==  'BE':
            m.addConstr((y1[p] == 0), 'forbidden: pp')
            m.addConstr((y3[p] == 0), 'forbidden: ccs')
        # option 3: CCS, forbidden: y1, y2 = 0
        if yy1 == 'CCS':
            m.addConstr((y1[p] == 0), 'forbidden: pp')
            m.addConstr((y2[p] == 0), 'forbidden: be')
        # option 4: BECCS, forbidden: y1,y2,y3 = 0
        if yy1 == 'BECCS':
            m.addConstr((y1[p] == 0), 'forbidden: pp')
            m.addConstr((y2[p] == 0), 'forbidden: be')
            m.addConstr((y3[p] == 0), 'forbidden: ccs')
    
    m.optimize()
    print(f"model status is:", m.status)
    
    ppOptionRecord = dict()
    pp2ResTake = []

    # https://www.gurobi.com/documentation/9.5/refman/optimization_status_codes.html
    if m.status == GRB.UNBOUNDED: # code:5
        print('!!!The model cannot be solved because it is unbounded!')
        
    elif m.status == GRB.INFEASIBLE: # code: 3
        print("!!!INFEASIBLE")
        vars = m.getVars()
        ubpen = [1.0] * m.numVars
        m.feasRelax(1, False, vars, None, ubpen, None, None)
        m.optimize()
    elif m.status == GRB.INF_OR_UNBD: # code: 4
        print("!!!INF_OR_UNBD, RELAX")
        vars = m.getVars()
        ubpen = [1.0] * m.numVars
        m.feasRelax(1, False, vars, None, ubpen, None, None)
        m.optimize()
     
    elif m.status == GRB.OPTIMAL: # code: 2
        print('!!!The optimal objective is %g' % m.objVal)
        upgrade_map = {0: 'PP', 1:'BE', 2:'CCS', 3:'BECCS'}
        
        for p in power_station_id:
            up = upgrade_map[
                [y1[p].x, y2[p].x, y3[p].x, y4[p].x].index(
                    max([y1[p].x, y2[p].x, y3[p].x, y4[p].x]))]
            
            takeRes = take.sum(p,'*').getValue()
            
            costValue = 0.
            emissValue = 0.
            cost_dataFrame = pd.DataFrame()
            
            if up == "PP":
                costValue, cost_dataFrame = LCOE_PP1(capacity[p], hours[p], operateYear[p], set_retrofitYear, columnName)
                emissValue = Emiss_PP(capacity[p], hours[p], operateYear[p], set_retrofitYear, unitCoal[p])
                
            elif up == "BE":
                costValue, cost_dataFrame = LCOE_BE1(capacity[p], hours[p], take.sum(p, '*').getValue(), 
                              take.prod(distance, p, "*").getValue(), operateYear[p], set_retrofitYear, ori_lcoeFrame[p], columnName)
                emissValue = Emiss_BE(capacity[p], hours[p], take.sum(p, '*').getValue(),
                                              take.prod(distance, p, "*").getValue(), operateYear[p], set_retrofitYear, unitCoal[p])
            elif up == "CCS":
                costValue, cost_dataFrame = LCOE_CCS1(capacity[p], hours[p], dccs[p], operateYear[p],
                                                      set_retrofitYear, ori_lcoeFrame[p], columnName)
                emissValue = Emiss_CCS(capacity[p], hours[p], operateYear[p], set_retrofitYear, unitCoal[p])
            elif up == "BECCS":
                costValue, cost_dataFrame = LCOE_BECCS1(capacity[p], hours[p],take.sum(p, '*').getValue(), take.prod(distance, p, "*").getValue(), dccs[p], operateYear[p],
                                 set_retrofitYear, ori_lcoeFrame[p], columnName)
                emissValue = Emiss_BECCS(capacity[p], hours[p], take.sum(p, '*').getValue(), take.prod(distance, p, "*").getValue(), operateYear[p], set_retrofitYear, unitCoal[p])
            
            # ppOptionRecord[p] = [up, takeRes, costValue, emissValue, cost_dataFrame]
            ppOptionRecord.update({p:[up, takeRes, costValue, emissValue, cost_dataFrame]})
            # print(p)
            
        # record residues
        print("take_pairs:")
        for c in power2res:
            pp_id = float(c[0])
            res_id = float(c[1])
            take_value = take[c].x
            pp2ResTake.append([pp_id, res_id, take_value]) 
            # if take_value > 0.0:
            #     pp2ResTake.append([pp_id, res_id, take_value]) 
            
            # pp2ResTake[c] = [pp_id, res_id, take_value]
        # print(pp2ResTake)
        
    elif m.status != GRB.INF_OR_UNBD and m.status != GRB.INFEASIBLE:
        print('!!!Optimization was stopped with status %d' % m.status)

    return ppOptionRecord, pp2ResTake