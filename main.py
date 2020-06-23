# -*- coding: utf-8 -*-
"""
Created on Mon Jun  1 14:35:39 2020

@author: s150127
"""

#%% Initialization

import numpy as np
import Solver_MEPS
import time
import cProfile

pr = cProfile.Profile()

set_start_year  = 2021
set_storages = ['storage']
set_renewables = ['solar','nuclear','wind']
set_number_of_loops = 4
set_max_counter = 5
change = 0.1


def norm_vector(method,years):
    total = np.zeros([len(method),len(years)])
    for year_index, year in enumerate(years):
        vector = np.random.rand(len(method))
        total[:,year_index] = vector/sum(vector)

    return total


def norm_vector_not_full(method,years):
    total = np.zeros([len(method),len(years)])
    for year_index, year in enumerate(years):
        vector = np.random.rand(len(method))
        total[:,year_index] = vector/sum(vector)*np.random.rand()

    return total

#%% Input

input_end_year = int(2050)#int(input("What year does the transition have to be complete?: "))
input_total_CO2_limit = np.inf#float(input("What is the total Gt CO2 allowed to be emitted (standard XXX Gt)?: "))
input_budget_fraction = float(100)#float(input("What is the maximum percentage of budget allow to be used (standard XXX%)?: "))/100

input_energy_mix = {'solar': 0.33 ,'wind': 0.34, 'nuclear': 0.33}


dutch_budget = 1e6
input_budget = input_budget_fraction*dutch_budget
input_elec_share = 0.26 #high estimate 0.54

#%% Initialization 2
years = np.array(range(set_start_year,input_end_year+1))
tries = np.array(range(1,set_number_of_loops+1))
set_tech = set_storages +set_renewables

#base = np.ones(years.shape)/(len(set_tech))
#parameters = {method:base for method in set_tech}

#%% Solve method 1, random change

# lowest_cost = float('Inf')
# best_parameters = []
# beun = 0

# for loop in tries:
#     for year_index, year in enumerate(years):
#         for tech in set_tech:
#             parameters = best_parameters
#             counter = 0
#             while counter < set_max_counter:
#                 #[cost, total_CO2] = solver.solve(parameters)
#                 total_CO2 = 5
#                 cost = 5 - beun
#                 beun +=1
#                 if total_CO2 > input_total_CO2_limit:
#                     counter+=1
#                     continue
#                 if cost < lowest_cost:
#                     lowest_cost = cost
#                     best_parameters = parameters
#                     counter = 0

#                     new = parameters[tech].copy()
#                     new[year_index] = new[year_index]+change
#                     parameters.update({tech: new})
#                     change_others = change/(len(set_tech)-1)

#                     for k, v in parameters.items():
#                         if k != tech:
#                             v_new = v.copy()
#                             v_new[year_index] = v_new[year_index] - change_others
#                             parameters.update({k: v_new})

#                 else:
#                     counter+=1

#                     new = parameters[tech].copy()
#                     new[year_index] = new[year_index]+change
#                     parameters.update({tech: new})
#                     change_others = change/(len(set_tech)-1)

#                     for k, v in parameters.items():
#                         if k != tech:
#                             v_new = v.copy()
#                             v_new[year_index] = v_new[year_index] - change_others
#                             parameters.update({k: v_new})


#%% Solve method two, total random
# set_number_of_loops = 100000
# tries = np.array(range(1,set_number_of_loops+1))

# lowest_cost = float('Inf')
# best_parameters = []
# for loop in tries:

#     base = norm_vector(set_tech,years)
#     parameters = {method:base[num,:] for num, method in enumerate(set_tech)}
#     #[cost, total_CO2, percentage] = solver.solve(parameters)
#     total_CO2 =5
#     cost = 5
#     if total_CO2 > input_total_CO2_limit:
#         continue
#     if cost < lowest_cost:
#         lowest_cost = cost
#         best_parameters = parameters

#%% Solve method three, random start, random iter
# base = norm_vector(set_tech,years)
# parameters = {method:base[num,:] for num, method in enumerate(set_tech)}

# for loop in tries:
#     #[cost, total_CO2, percentage] = solver.solve(parameters)
#     total_CO2 =5
#     cost = 5
#     if total_CO2 > input_total_CO2_limit:
#         continue
#     if cost < lowest_cost:
#         lowest_cost = cost
#         best_parameters = parameters

#     year_to_change = int(np.random.rand()*years.shape[0])
#     vector = np.random.rand(len(set_tech))
#     base[:,year_to_change] = vector/sum(vector)
#     new = {method:base[num,:] for num, method in enumerate(set_tech)}
#     parameters.update(new)


#%% Solve method four, random start, random iter, reset

def change_params(set_tech, params, saturation_years, input_end_year, set_start_year):
    i=0
    
    new_params = parameters.copy()
    
    for key, values in parameters.items():
        if saturation_years[i,1]!=input_end_year:
            new_values=values.copy()
            new_values[int(saturation_years[i,0]-set_start_year):] = new_values[int(saturation_years[i,0]-set_start_year):]*0.95
            new_params[key] = new_values
    
        i +=1

    return new_params


set_number_of_loops = 10
lowest_cost = float('Inf')
best_parameters = []

base = norm_vector_not_full(set_tech, years)
parameters = {method:base[num, :] for num, method in enumerate(set_tech)}

loop = 0

start = time.time()
pr.enable()

# list for dominance (co2 vs cost) plot
dominance_co2 = []
dominance_cost = []

while loop < set_number_of_loops:

    parameter_values = norm_vector_not_full(set_tech, years)
    parameters = {method:parameter_values[num, :] for num, method in enumerate(set_tech)}
    

    

    while True:
        cost, co2_total, percentage_renewables, percentage_storage, saturation_years = Solver_MEPS.solver(parameters, input_energy_mix, input_end_year, input_budget, input_elec_share, 1)
        
        if loop % (set_number_of_loops/10) == 0:    
            print('Starting '+str(loop)+' of ' + str(set_number_of_loops))
        
        if co2_total > input_total_CO2_limit or percentage_renewables != 100 or percentage_storage !=100:
            loop+=1
            break
          

        if cost < lowest_cost:
            lowest_cost = cost
            best_parameters = parameters.copy()
            
            dominance_co2.append(co2_total) #this might be real slow bc append ain't great. might be able to do this in outer while loop if this is slow or stores too much?
            dominance_cost.append(cost)
            
            loop+=1
            parameters = change_params(set_tech, parameters,saturation_years, input_end_year, set_start_year)
        else:
            loop+=1
            break
            

        if loop == set_number_of_loops:
            break


print('Time taken: ' + str(round(time.time() - start, 3)))
pr.disable()
pr.print_stats(sort='time')

if best_parameters==[]:
    print("no solution found")
else:
    cost, co2_total, percentage_renewables, percentage_storage, saturation_years = Solver_MEPS.solver(best_parameters, input_energy_mix, input_end_year, input_budget, input_elec_share, 0)

    ax = plt.gca()
    plt.scatter(dominance_cost/1e6, dominance_co2/1e6)
    plt.xlabel('Total cost (million euros)')
    plt.ylabel('Integrated CO2 emission (million kg)')
    plt.show()
    
    
    
    
