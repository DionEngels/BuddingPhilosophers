# -*- coding: utf-8 -*-
"""
Created on Mon Jun  1 14:35:39 2020

@authors: B.J. Alers, D.J. Engels, M.E. Smedberg
"""

#%% Functions

import numpy as np
import Solver_MEPS
import time
import matplotlib.pyplot as plt

def norm_vector_not_full(method, years, storage_buff):
    total = np.zeros([len(method),len(years)])
    for year_index, year in enumerate(years):
        vector = np.random.rand(len(method))
        vector[0] = vector[0]*storage_buff
        total[:,year_index] = vector/sum(vector)

    return total

def change_params(set_tech, parameters, saturation_years, input_end_year, set_start_year):
    i=0
    
    new_params = parameters.copy()
    
    for key, values in parameters.items():
        if saturation_years[key][1] != input_end_year:
            new_values=values.copy()
            
            if saturation_years[key][0] < set_start_year + 5:
                new_values[:] = new_values[:]*0.9
            else:
                new_values[int(saturation_years[key][0]-set_start_year-1):] = new_values[int(saturation_years[key][0]-set_start_year-1):]*0.9
            
            new_params[key] = new_values
    
        i +=1

    return new_params


def increase_params(set_tech, parameters, key, input_end_year, set_start_year):
    
    new_params = parameters.copy()

    new_values=parameters[key].copy()
    new_values = new_values*1.05
    new_params[key] = new_values

    return new_params

def norm_params(parameters):
    total = np.zeros([len(parameters),len(list(parameters.values())[0])])
    for i, values in enumerate(list(parameters.values())):
        total[i, :] = values    
        
    for i in range(0, len(list(parameters.values())[0])):
        if np.sum(total[:, i]) > 1.0:
            total[:, i] = total[:, i]/np.sum(total[:, i])
        
    new_params = {method:total[num, :] for num, method in enumerate(parameters.keys())}
    
    return new_params

#%% Input

input_end_year = int(2050)#int(input("What year does the transition have to be complete?: "))
input_total_CO2_limit = np.inf#float(input("What is the total Gt CO2 allowed to be emitted (standard = infinity (don't type, use a very large number) Gt)?: "))
input_budget_fraction = float(1)#float(input("What is the maximum percentage of budget allow to be used (standard = 1%)?: "))/100

input_energy_mix = {'solar': 0.33 ,'wind': 0.34, 'nuclear': 0.33}

set_start_year  = 2021
set_storages = ['storage']
set_renewables = ['solar','nuclear','wind']

dutch_budget = 1e11
input_budget = input_budget_fraction*dutch_budget
input_elec_share = 0.26 #high estimate 0.54

set_number_of_loops = 100000
max_iter = 500
storage_buff = 20

#%% Initialization
years = np.array(range(set_start_year,input_end_year+1))
set_tech = set_storages +set_renewables
#%% Main part
lowest_cost = float('Inf')
best_parameters = []

loop = 0

start = time.time()

# list for dominance (co2 vs cost) plot
dominance_co2 = np.zeros(set_number_of_loops)
dominance_cost = np.zeros(set_number_of_loops)
dominance_loop = np.zeros(set_number_of_loops)

while loop < set_number_of_loops:
    try:
        trans_years = np.asarray([int(sat[0]) for key, sat in saturation_years.items() if key!='storage'])
        trans_years[trans_years == 0] = set_start_year*10
        if np.mean(trans_years) < set_start_year + 10:
            storage_buff = storage_buff*1.2
    except:
        pass
    
    iter_loop = 0
    parameter_values = norm_vector_not_full(set_tech, years, storage_buff)
    parameters = {method:parameter_values[num, :] for num, method in enumerate(set_tech)}
    
    while iter_loop < max_iter:
        cost, co2_total, percentage, saturation_years = Solver_MEPS.solver(parameters, input_energy_mix, input_end_year, input_budget, input_elec_share, 0)

        if loop % (set_number_of_loops/10) == 0:    
            print('Starting '+str(loop)+' of ' + str(set_number_of_loops))
        
        if co2_total > input_total_CO2_limit*1e12: # 1e12 for gigaton
            loop+=1
            high_co2 = True
            break
        
        if any(values == 0 for values in percentage.values()):
            low_money = True
            high_co2 = False
            if iter_loop == 0:
                storage_buff = storage_buff/1.2
        
        if any(values < 100 for values in percentage.values()):
            for key, values in percentage.items():
                if values < 100:
                    parameters = increase_params(set_tech, parameters, key, input_end_year, set_start_year)
                    
            parameters = norm_params(parameters)
            loop+=1
            iter_loop +=1
            if loop == set_number_of_loops:
                break
            else:
                continue

        if cost < lowest_cost:
            low_money = False
            high_co2 = False
            lowest_cost = cost
            best_parameters = parameters.copy()
            
            dominance_co2[loop] = co2_total
            dominance_cost[loop] = cost
            dominance_loop[loop] = loop
            
            iter_loop+=1
            loop+=1
            parameters = change_params(set_tech, parameters,saturation_years, input_end_year, set_start_year)
        else:
            loop+=1
            iter_loop+=1
            parameters = change_params(set_tech, parameters,saturation_years, input_end_year, set_start_year)
            
        if loop == set_number_of_loops:
            break

dominance_co2 = dominance_co2[dominance_co2 > 0]
dominance_cost = dominance_cost[dominance_cost > 0]
dominance_loop = dominance_loop[dominance_loop > 0]

print('\nTime taken: ' + str(round(time.time() - start, 3)))

#%% Run again to visualize best result

if best_parameters==[]:
    print("No solution found")
else:
    cost, co2_total, percentage, saturation_years = Solver_MEPS.solver(best_parameters, input_energy_mix, input_end_year, input_budget, input_elec_share, 1)
    
    low_money  = False
    
    ax = plt.gca()
    scatter = plt.scatter(dominance_cost/1e9, dominance_co2/1e9, c=dominance_co2/1e9, cmap = 'Purples',s=200, edgecolors="black")#,alpha=0.5)
    plt.xlabel('Total cost (billion euros)')
    plt.ylabel('Integrated CO2 emission (billion kg)')
    handles, _ = scatter.legend_elements(num=3)
    labels = ['first iteration','last iteration'] #check size of handles, if 3 then add ,'', in middle or change to 2 in line above
    plt.legend(handles, labels)
    plt.grid(True)
    plt.tick_params(direction='in', axis='both', which='both', top='True', right='True')
    
    plt.show()
    
    print('\nFound lowest total cost achievable: ' + str(round(cost/1e9, 2)) + ' billion euro')
    print('CO2 emitted during transition: '+ str(round(co2_total/1e12, 2)) + ' Gt')
    print('Check plots for more info')
    
if low_money == True:
    print("You are too poor. Increase total budget")
if high_co2 == True:
    print("You are over the CO2 limit. Increase CO2 limit or spend more to transition faster.")
