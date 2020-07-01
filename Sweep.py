# -*- coding: utf-8 -*-
"""
Created on Tue Jun 30 11:18:43 2020

@author: mepsm
"""


import numpy as np
import Solver_for_sweep
# from main import norm_vector_not_full, change_params, increase_params, norm_params
#import main.norm_vector_not_full, main.change_params, main.increase_params, main.norm_params
import time
import matplotlib.pyplot as plt
import sys


#%% Input

input_end_year = int(2050)#int(input("What year does the transition have to be complete?: "))
input_total_CO2_limit = np.inf#float(input("What is the total Gt CO2 allowed to be emitted (standard XXX Gt)?: "))

input_energy_mix = {'solar': 0.33 ,'wind': 0.34, 'nuclear': 0.33}

set_start_year  = 2021
set_storages = ['storage']
set_renewables = ['solar','nuclear','wind']

dutch_budget = 1e11
input_elec_share = 0.26 #high estimate 0.54

fit_factor_exp = 0.1 #exponential
td0 = -1
fit_factor_lin = 1 #linear

set_number_of_loops = 200000
final_visualization = input('Do you want optimization visuals? n=0/y=1: ')

#%% Initialization 2
years = np.array(range(set_start_year,input_end_year+1))
set_tech = set_storages +set_renewables

#%% Definition of sweep function

sweep_var = ['input_elec_share','input_energy_mix','dutch_budget','fit_factor_exp','td0','fit_factor_lin']
# sweep_var = ['fit_factor_exp','td0','fit_factor_lin'] # example if you only wanted to sweep these parameters
# sweep_var = ['td0']
def sweep(name_of_sweep_variable):
    assert type(name_of_sweep_variable) == str
    
    if name_of_sweep_variable == 'input_elec_share':
        print('Sweeping', name_of_sweep_variable, 'now')
        sweep_values = [0.1, 0.3, 0.5, 0.7, 1]
        return sweep_values
    
    # this one is different (not just one value to set)
    if name_of_sweep_variable == 'input_energy_mix':
        print('Sweeping', name_of_sweep_variable, 'now')
        # set values for nuclear share, then calc wind and solar as even split of the rest
        sweep_values = [0.1, 0.3, 0.5, 0.7, 0.9]
        return sweep_values
    
    if name_of_sweep_variable == 'dutch_budget':
        print('Sweeping', name_of_sweep_variable, 'now')
        sweep_values = [1e8, 5e8, 1e9, 5e9, 1e10, 5e10, 1e11, 5e11]
        return sweep_values
    
    if name_of_sweep_variable == 'fit_factor_exp':
        print('Sweeping', name_of_sweep_variable, 'now')
        sweep_values = [0.001, 0.005, 0.01, 0.01, 0.05, 0.1, 0.5, 1, 10, 100]
        return sweep_values

    if name_of_sweep_variable == 'td0':
        print('Sweeping', name_of_sweep_variable, 'now')
        sweep_values = [-10 ,-3, -2, -1, -0.1, 2, 4, 6, 8, 10, 15]
        return sweep_values
    
    if name_of_sweep_variable == 'fit_factor_lin':
        print('Sweeping', name_of_sweep_variable, 'now')
        sweep_values = [0.01, 0.2, 0.6, 1, 1.4, 1.8, 10]
        return sweep_values
        
#%% optimization functions

def norm_vector_not_full(method, years, storage_buff):
    total = np.zeros([len(method),len(years)])
    for year_index, year in enumerate(years):
        vector = np.random.rand(len(method))
        vector[0] = vector[0]*storage_buff
        total[:,year_index] = vector/sum(vector)#*np.random.rand()

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


#%% Main part

sweep_values_full = []
sweep_co2_full = []
sweep_cost_full = [] #here store sweep results for all trials, so can access after loop is finished

pass_count = 0
full_time = time.time()

for sweep_number, variable in enumerate(sweep_var):
    
    #reset all sweeped values to original
    fit_factor_exp = 0.1 #exponential
    td0 = -1
    fit_factor_lin = 1 #linear
    dutch_budget = 1e11
    input_elec_share = 0.26
    input_energy_mix = {'solar': 0.33 ,'wind': 0.34, 'nuclear': 0.33}
    
    sweep_values = sweep(variable)
    sweep_co2 = np.zeros(len(sweep_values))
    sweep_cost = np.zeros(len(sweep_values))
    
    for value_index in range(len(sweep_values)):
        try:
            if variable == 'input_energy_mix':
                globals()[variable]['nuclear'] = sweep_values[value_index]
                globals()[variable]['solar'] = 0.5*(1 - sweep_values[value_index])
                globals()[variable]['wind'] = 0.5*(1 - sweep_values[value_index])
            else:
                globals()[variable] = sweep_values[value_index]
            print('New value for',variable,'=',globals()[variable])
        
            storage_buff = 20
            lowest_cost = float('Inf')
            best_parameters = []
            
            loop = 0
            max_iter = 500
            
            start = time.time()
            
            if final_visualization == 1:
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
                    cost, co2_total, percentage, saturation_years = Solver_for_sweep.solver(parameters, input_energy_mix, input_end_year, dutch_budget, input_elec_share, fit_factor_exp, td0, fit_factor_lin, 0)
            
                    if loop % (set_number_of_loops/5) == 0:    
                        print('Starting '+str(loop)+' of ' + str(set_number_of_loops))
                    
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
                        
                        if final_visualization == 1:
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
            
            if final_visualization == 1:
                dominance_co2 = dominance_co2[dominance_co2 > 0]
                dominance_cost = dominance_cost[dominance_cost > 0]
                dominance_loop = dominance_loop[dominance_loop > 0]
            
            
            
            print('Time taken: ', round((time.time() - start)/60, 3), 'minutes')
            
            if best_parameters==[]:
                print("No solution found")
            else:
                cost, co2_total, percentage, saturation_years = Solver_for_sweep.solver(best_parameters,
                                 input_energy_mix, input_end_year, dutch_budget, input_elec_share,
                                 fit_factor_exp, td0, fit_factor_lin, final_visualization)
                
                sweep_co2[value_index] = co2_total
                sweep_cost[value_index] = cost
                
                low_money  = False
                
                if final_visualization == 1:
                    ax = plt.gca()
                    scatter = plt.scatter(dominance_cost/1e9, dominance_co2/1e9, c=dominance_co2/1e9, cmap = 'Purples',s=500, edgecolors="black")
                    plt.xlabel('Total cost (billion euros)')
                    plt.ylabel('Integrated CO2 emission (billion kg)')
                    handles, _ = scatter.legend_elements(num=2)
                    labels = ['first iteration','last iteration']
                    plt.legend(handles, labels)
                    plt.show()
            if low_money == True:
                print("You are too poor. Increase total budget")
            if high_co2 == True:
                print("You are over the CO2 limit. Increase CO2 limit or spend more.")
        except:
            pass_count += 1
            print('Encountered error:', sys.exc_info()[0],'... passing')
            pass
#%%
    sweep_values_full.append(sweep_values)
    sweep_co2_full.append(sweep_co2)
    sweep_cost_full.append(sweep_cost)
    
print('Number of errors:', pass_count)
print('Full time taken: ', round((time.time() - full_time)/60, 3), 'minutes')
#%%
for sweep_number, variable in enumerate(sweep_var):
    if variable == 'input_energy_mix':
        variable = 'nuclear share'
    sweep_values = sweep_values_full[sweep_number]
    sweep_co2 = sweep_co2_full[sweep_number]
    sweep_cost = sweep_cost_full[sweep_number]
    
    fig, ax1 = plt.subplots()
    if variable == 'dutch_budget' or variable == 'fit_factor_exp' or variable == 'fit_factor_lin':
        plt.xscale("log")
        ax1.set_xlim(0.90*min(sweep_values), 1.10*max(sweep_values))
    color = 'tab:red'
    ax1.set_xlabel('Sweep values for '+variable)
    ax1.set_ylabel('Integrated CO2 emission (billion kg)', color=color)
    ax1.plot(sweep_values, sweep_co2/1e9, '--o', color=color)
    ax1.tick_params(axis='y', labelcolor=color)
    plt.grid(True)
    plt.tick_params(direction='in', axis='both', which='both', top='True', right='True')
    
    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
    
    color = 'tab:blue'
    ax2.set_xlabel('Sweep values for '+variable)
    ax2.set_ylabel('Total cost (billion euros)', color=color)
    ax2.plot(sweep_values, sweep_cost/1e9, '--o', color=color)
    ax2.tick_params(axis='y', labelcolor=color)
    
    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    plt.tick_params(direction='in', axis='both', which='both', top='True', right='True')
    plt.show()