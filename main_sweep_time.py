# -*- coding: utf-8 -*-
"""
Created on Mon Jun  1 14:35:39 2020

@authors: B.J. Alers, D.J. Engels, M.E. Smedberg
"""

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
    
    new_params = parameters.copy()
    
    for key, values in parameters.items():
        
        if saturation_years[key][1] != input_end_year:
            new_values=values.copy()
            
            #if saturation_years[key][0] < set_start_year + 5:
            #    new_values[:] = new_values[:]*0.9
            #else:
            new_values[int(saturation_years[key][0]-set_start_year):] = new_values[int(saturation_years[key][0]-set_start_year):]*0.9
            
            new_params[key] = new_values
    
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

#set_number_of_loops = 200000
max_iter = 250

#%% Initialization
years = np.array(range(set_start_year,input_end_year+1))
set_tech = set_storages +set_renewables

#%% Main part
list_number_loops=[10000]
repeat=1000

result_cost=np.zeros(len(list_number_loops))
result_cost_mean=np.zeros(len(list_number_loops))
result_time=np.zeros(len(list_number_loops))
result_cost_relative_spread = np.zeros(len(list_number_loops))

for i, set_number_of_loops in enumerate(list_number_loops):
    counter=0
    time_taken=np.zeros(repeat)
    cost_array=np.zeros(repeat)
    
    while counter < repeat:
    
            #set_number_of_loops = 100
        storage_buff = 100
        lowest_cost = float('Inf')
        best_parameters = []
        
        loop = 0
        
        start = time.time()
    
    
        
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
        
               # if loop % (set_number_of_loops/10) == 0:    
                    #print('Starting '+str(loop)+' of ' + str(set_number_of_loops))
                
                if co2_total > input_total_CO2_limit:
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
                    
               
             
                    iter_loop+=1
                    loop+=1
                    parameters = change_params(set_tech, parameters,saturation_years, input_end_year, set_start_year)
                else:
                    loop+=1
                    iter_loop+=1
                    parameters = change_params(set_tech, parameters,saturation_years, input_end_year, set_start_year)
                    
                if loop == set_number_of_loops:
                    break
        
    
        
        
        
        #print('Time taken: ' + str(round(time.time() - start, 3)))
        
        time_taken[counter]=round(time.time() - start, 3)
    
        #pr.print_stats(sort='time')
        
        if best_parameters==[]:
            #print("No solution found")
            pass
        else:
            cost, co2_total, percentage, saturation_years = Solver_MEPS.solver(best_parameters, input_energy_mix, input_end_year, input_budget, input_elec_share, 0)
            
            low_money  = False
    
            cost_array[counter]=cost
            
    
            
        #if low_money == True:
         #   print("You are too poor. Increase total budget")
        #if high_co2 == True:
         #   print("You are over the CO2 limit. Increase CO2 limit or spend more.")
        counter += 1
        
    
    cost_array =  cost_array[cost_array>0]   
    
    result_cost[i]=np.std(cost_array)
    result_cost_mean[i]=np.mean(cost_array)
    result_cost_relative_spread[i] = result_cost[i]/result_cost_mean[i]
    result_time[i]=np.mean(time_taken)
    
    print('Done with loop of ' + str(set_number_of_loops))
    
    

#%%
#plot iterations vs time
        
fig, ax1 = plt.subplots()

plt.xscale("log")
plt.yscale("log")
ax1.set_xlim(xmin=0.9, xmax=max(list_number_loops)*2)

color = 'tab:red'
ax1.set_xlabel('Number of iterations')
ax1.set_ylabel('Computational Time (seconds)', color=color)
ax1.plot(list_number_loops,result_time, '--o', color=color)
ax1.tick_params(axis='y', labelcolor=color)
plt.grid(True)
plt.tick_params(direction='in', axis='both', which='both', top='True', right='True')

ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

color = 'tab:blue'
ax2.set_ylabel('Spread of result', color=color)
ax2.set_yscale("log")

ax2.plot(list_number_loops, result_cost_relative_spread, '--o', color=color)
ax2.tick_params(axis='y', labelcolor=color)

fig.tight_layout()  # otherwise the right y-label is slightly clipped
plt.tick_params(direction='in', axis='both', which='both', top='True', right='True')
plt.show()