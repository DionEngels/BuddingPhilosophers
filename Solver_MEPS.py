# -*- coding: utf-8 -*-
"""
Created on Mon Jun 15 14:23:21 2020

@author: mepsm
"""
# additions:
    # added storage to list_of_params
    # added calculation of p_sat
    # removed cost_current because we would just calculate it new for
      # each time step anyway
    # added "intermittent" bool to renewables
    # added "name" key to each list_of_params for loop
    # added tau_exp to list_of_params, initial value set
    
# still to be fixed:
    # no storage mix right now
    # fit_factor and exponential growth derivation in general...

from math import log10, log, exp
import numpy as np
import matplotlib.pyplot as plt


def initial_params(energy_mix, t_end, electricity_share_end):
    t_init = 2021
    
    world = {'energy_demand_total': 1000, 'electricity_share_init': 0.18,
             'electricity_share_end': electricity_share_end, 'non_renew_co2': 100}
    
    world['electricity_share'] = [(world['electricity_share_end'] - 
                                   world['electricity_share_init'])/(t_end - t_init)*i
                                + world['electricity_share_init']
                                for i in range(t_end - t_init + 1)]
    
    solar =  {'name': 'solar', 'cost_init': 10, 'power_init': 10,
            'tau_life': 10, 'td0': 1,
            'tau_exp': 1, 'fit_factor': 1e5, 'cap_factor': 1,
            'intermittent': True}
    solar['power_current'] = solar['power_init']
    solar['p_sat'] = world['energy_demand_total']*world['electricity_share_end']*energy_mix['solar']/solar['cap_factor']

    wind = {'name': 'wind', 'cost_init': 1, 'power_init': 1,
            'tau_life': 10, 'td0': 1,
            'tau_exp': 1, 'fit_factor': 1e5, 'cap_factor': 1,
            'intermittent': True}
    wind['power_current'] = wind['power_init']
    wind['p_sat'] = world['energy_demand_total']*world['electricity_share_end']*energy_mix['wind']/wind['cap_factor']

    nuclear = {'name': 'nuclear', 'cost_init': 100, 'power_init': 100,
            'tau_life': 10, 'td0': 1,
            'tau_exp': 1, 'fit_factor': 1e5, 'cap_factor': 1,
            'intermittent': False}
    nuclear['power_current'] = nuclear['power_init']
    nuclear['p_sat'] = world['energy_demand_total']*world['electricity_share_end']*energy_mix['nuclear']/nuclear['cap_factor']

    list_of_params = [solar, wind, nuclear]

    storage = {'name': 'storage', 'cost_init': 1000, 'power_init': 1,
            'tau_exp': 1, 'tau_life': 10, 'td0': 1,'cap_factor': 1,
            'fit_factor': 1e5, 'intermittent': False}
    storage['power_current'] = storage['power_init']
    storage['p_sat'] = sum([i['p_sat']/12/storage['cap_factor'] for i in
                            list_of_params if i['intermittent']==True])

    list_of_params.append(storage)
    
    
    return list_of_params, world, t_init

def solver(parameters, energy_mix, t_end, max_budget, electricity_share_end, visualization):
    
    list_of_params, world, t_init = initial_params(energy_mix, t_end, electricity_share_end)
    co2_total = 0
    cost = 0
    
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
            invest = parameters[renewable['name']][i]*max_budget
            power_current = renewable['power_current']
            cost_current = renewable['cost_init']*(0.5)**log10(power_current/renewable['power_init'])
            tau_life = renewable['tau_life']
            td0 = renewable['td0']
            tau_exp = renewable['tau_exp']
            p_sat = renewable['p_sat']
            fit_factor = renewable['fit_factor']
            p_trans = p_sat*tau_exp/tau_life
                         
            if power_current >= p_sat:
                growth = 0
                invest = 0
                
            elif power_current < p_trans:
                growth = power_current*(exp(log(2)/td0 + invest/(cost_current*fit_factor*p_trans)) - 1)
                renewable['tau_exp'] = 1/(log(2)/td0 + invest/(cost_current*fit_factor*p_trans))
                
            elif power_current >= p_trans:
                growth = p_sat/tau_life + invest/(cost_current*fit_factor)
                
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
            
            if visualization == 1:
                if year == 0:
                    power_matrix[i,year] = power_current-growth
                power_matrix[i,year+1] = power_current
                growth_matrix[i,year+1] = growth
                invest_matrix[i,year+1] = invest
                
    elec_renew = sum([i['power_current'] for i in list_of_params if i['name']!='storage'])
    percentage_renewables = int(elec_renew/(world['energy_demand_total']*world['electricity_share'][-1])*100)
    storage_current = sum([i['power_current']*i['cap_factor'] for i in list_of_params if i['name']=='storage'])
    elec_int = sum([i['power_current'] for i in list_of_params if i['intermittent']==True])
    percentage_storage = int(storage_current/(elec_int/12)*100)
                
    if visualization == 1:
        years = list(range(t_init-1,t_end+1))
        ax = plt.gca()
        for i, row in enumerate(power_matrix):
            plt.plot(years, row, label=list_of_params[i]['name'])
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles, labels)
        plt.xlabel('Year')
        plt.ylabel('Electricity Production')
        plt.show()
    
            
    return cost, co2_total, percentage_renewables, percentage_storage
 