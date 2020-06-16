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
    
energy_mix = {'solar': ,'wind': , 'nuclear': }

def initial_params(energy_mix, t_end):
    t_init = 2021
    
    world = {'energy_demand_total': constant, 'electricity_share_init': 0.18,
             'electricity_share_end': , 'max_budget': }
    
    world['electricity_share'] = [(world['electricity_share_end'] - 
                                   world['electricity_share_init'])/(t_end - t_init)*i
                                + world['electricity_share_init']
                                for i in range(t_end - t_init + 1)]
    
    solar =  {'name': 'solar', 'cost_init': , 'power_init': ,
            'power_current': 'NaN', 'p_sat': 'NaN','tau_life': , 'td0': ,
            'tau_exp': 4, 'fit_factor': 1e5, 'cap_factor': ,
            'intermittent': True}
    solar['p_sat'] = world['energy_demand_total']*world['electricity_share_end']*energy_mix['solar']/solar['cap_factor']

    wind = {'name': 'wind', 'cost_init': , 'power_init': ,
            'power_current': 'NaN', 'p_sat': 'NaN','tau_life': , 'td0': ,
            'tau_exp': 4, 'fit_factor': 1e5, 'cap_factor': ,
            'intermittent': True}
    wind['p_sat'] = world['energy_demand_total']*world['electricity_share_end']*energy_mix['wind']/wind['cap_factor']

    nuclear = {'name': 'nuclear', 'cost_init': , 'power_init': ,
            'power_current': 'NaN', 'p_sat': 'NaN', 'tau_life': , 'td0': ,
            'tau_exp': 4, 'fit_factor': 1e5, 'cap_factor': ,
            'intermittent': False}
    nuclear['p_sat'] = world['energy_demand_total']*world['electricity_share_end']*energy_mix['nuclear']/nuclear['cap_factor']

    list_of_params = [solar, wind, nuclear, ...]

    storage = {'name': 'storage', 'cost_init': , 'power_init': ,
            'power_current': 'NaN', 'p_sat': 'NaN',
            'tau_exp': 4, 'tau_life': , 'td0': ,'cap_factor': ,
            'fit_factor': 1e5}
    storage['c_sat'] = sum(i['p_sat'])/12/storage['efficiency'] for i in list_of_params

    list_of_params.append(storage)
    
    
    return list_of_params, world, t_init


def solver(parameters, energy_mix, t_end):
    
    list_of_params, world, t_init = initial_params(energy_mix, t_end)
    
    for year in range(t_end - t_init + 1):
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
                
            elif power_current < p_trans:
                growth = power_current(exp(log(2)/td0 + invest/(cost_current*fit_factor*p_trans)) - 1)
                renewable['tau_exp'] = 1/(log(2)/td0 + invest/(cost_current*fit_factor*p_trans))
                
            elif power_current >= p_trans:
                growth = p_sat/tau_life + invest/(cost_current*fit_factor)
                
            if power_current + growth > p_sat:
                power_current = p_sat
                renewable['power_current'] = power_current
            
            else:
                power_current = power_current + growth   
                renewable['power_current'] = power_current
            
                
            
            
    return cost, co2_total, percentage_renewables, percentage_storage
 