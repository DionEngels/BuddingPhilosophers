# -*- coding: utf-8 -*-
"""
Created on Thu Jun 25 21:45:08 2020

@author: mepsm
"""

import numpy as np
import Solver_MEPS
import matplotlib.pyplot as plt
from math import log10, log, exp



def invest_calc(tau_exp, energy_mix, t_end, electricity_share_end, visualization):
    
    list_of_params, world, t_init = Solver_MEPS.initial_params(energy_mix, t_end, electricity_share_end)
    cost = 0
    cost_no_storage = 0
    co2_total = 0
    #saturation_years={method:np.zeros(2) for method in parameters}
    
    if visualization == 1:
        growth_matrix = np.zeros((len(list_of_params),t_end - t_init + 2))
        power_matrix = np.zeros((len(list_of_params),t_end - t_init + 2))
        
        invest_matrix = np.zeros((len(list_of_params),t_end - t_init + 2))
        
        co2_yearly_matrix = np.zeros((1,t_end - t_init + 2))
        co2_total_matrix = np.zeros((1,t_end - t_init + 2))
    
    for year in range(t_end - t_init + 1):
        
        elec_total = world['energy_demand_total']*world['electricity_share'][year]
        elec_renew = sum([i['power_current'] for i in list_of_params if i['name']!='storage'])
        elec_non_renew = elec_total - elec_renew
        
        if elec_non_renew < 0:
            storage_current = sum([i['power_current']*i['cap_factor'] for i in list_of_params if i['name']=='storage'])
            elec_int = sum([i['power_current'] for i in list_of_params if i['intermittent']==True])
            required_storage = elec_int/12
            if storage_current < required_storage:
                elec_non_renew = (required_storage - storage_current)
            else:
                elec_non_renew = 0
            
        co2_total += elec_non_renew*world['non_renew_co2']
        
        if visualization == 1:
            co2_yearly_matrix[0,year+1] = elec_non_renew*world['non_renew_co2']
            co2_total_matrix[0,year+1] = co2_total
        
        for i, renewable in enumerate(list_of_params):

            power_current = renewable['power_current']
            cost_current = renewable['cost_init']*(0.5)**log10(power_current/renewable['power_init'])
            tau_life = renewable['tau_life']
            td0 = renewable['td0']
            p_sat = renewable['p_sat']
            fit_factor = renewable['fit_factor']
            p_trans = p_sat*tau_exp/tau_life
            
       
            if power_current >= p_sat:
                growth = 0
                invest = 0          
                 
            elif power_current < p_trans: #exponential
                growth = power_current*(exp(1/tau_exp) - 1)
                invest = cost_current*fit_factor*p_trans*(1/tau_exp - log(2)/td0)
                
                #print(renewable['name'])
                #print(p_trans/1e9, 'TWh')
                #print(cost_current)
                #print(growth/1e6, 'MWh')
                #x = 2
                
            elif power_current >= p_trans: #linear
                if fit_factor != 1:
                    renewable['t_trans'] = year + t_init
            
                fit_factor = 1 #linear fit factor
                renewable['fit_factor'] = fit_factor
                if (p_sat - p_trans)/(t_end - renewable['t_trans']) <= p_sat/tau_life:
                    invest = 0
                    growth = p_sat/tau_life
                    
                else:
                    growth = (p_sat - p_trans)/(t_end - renewable['t_trans'])
                    invest = cost_current*fit_factor*(growth - p_sat/tau_life)
                
            if power_current + growth > p_sat:
                growth = p_sat - power_current
                invest = (growth - p_sat/tau_life)*(cost_current*fit_factor)
                if invest < 0:
                    invest = 0
                power_current = p_sat
                
                renewable['power_current'] = power_current
            
            else:
                power_current = power_current + growth   
                renewable['power_current'] = power_current
                
            cost += invest
            if renewable['name'] != 'storage':
                cost_no_storage += invest
            
            if visualization == 1:
                if year == 0:
                    power_matrix[i,year] = power_current-growth
                power_matrix[i,year+1] = power_current
                growth_matrix[i,year+1] = growth
                invest_matrix[i,year+1] = invest
                
    elec_renew = sum([i['power_current']*i['cap_factor'] for i in list_of_params if i['name']!='storage'])
    percentage_renewables = int(elec_renew/(world['energy_demand_total']*world['electricity_share'][-1])*100)
    storage_current = sum([i['power_current']*i['cap_factor'] for i in list_of_params if i['name']=='storage'])
    elec_int = sum([i['power_current'] for i in list_of_params if i['intermittent']==True])
    percentage_storage = int(storage_current/(elec_int/12)*100)
                
    if visualization == 1:
        years = list(range(t_init-1,t_end+1))
        
        ax = plt.gca()
        for i, row in enumerate(power_matrix):
            plt.plot(years, row/1e9, label=list_of_params[i]['name'])
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles, labels)
        ax.set_ylim(ymin=0)
        plt.xlabel('Year')
        plt.ylabel('Nominal Installed Capacity (TWh)')
        plt.show()
        
        ax = plt.gca()
        for i, row in enumerate(power_matrix):
            plt.plot(years, row/list_of_params[i]['p_sat'], label=list_of_params[i]['name'])
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles, labels)
        ax.set_ylim(ymin=0)
        plt.xlabel('Year')
        plt.ylabel('Electricity Production (norm)')
        plt.show()
        
        ax = plt.gca()
        for i, row in enumerate(invest_matrix):
            if list_of_params[i]['name'] == 'storage':
                continue
            plt.plot(years, row/1e6, label=list_of_params[i]['name'])
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles, labels)
        ax.set_ylim(ymin=0)
        plt.xlabel('Year')
        plt.ylabel('Investment (million euros)')
        plt.show()
                
    return cost, cost_no_storage, co2_total, percentage_renewables, percentage_storage



tau_exp = 4/log(2)
input_energy_mix = {'solar': 0.33 ,'wind': 0.34, 'nuclear': 0.33}
input_end_year = int(2050)#
input_elec_share = 0.26


cost, cost_no_storage, co2_total, percentage_renewables, percentage_storage = invest_calc(tau_exp, input_energy_mix, input_end_year, input_elec_share, 1)

print('Cost (billion euros):', cost/1e9)
print('\nCost without storage (billion euros):', cost_no_storage/1e9)
print('\nRenewables at', percentage_renewables, '%')
print('\nStorage at', percentage_storage, '%')
 