# -*- coding: utf-8 -*-
"""
Created on Mon Jun 15 14:23:21 2020

@authors: B.J. Alers, D.J. Engels, M.E. Smedberg
"""

from math import log10, log, exp
import numpy as np
import matplotlib.pyplot as plt


def initial_params(energy_mix, t_end, electricity_share_end):
    t_init = 2021
    fit_factor = 0.1 # exponential fit factor, from Marion's model
    td0 = -1        # base doubling time,          " 
    
    world = {'energy_demand_total': 874e9, 'electricity_share_init': 0.14,
             'electricity_share_end': electricity_share_end, 'non_renew_co2': 0.45} #co2 kg/kWh
    
    world['electricity_share'] = [(world['electricity_share_end'] - 
                                   world['electricity_share_init'])/(t_end - t_init)*i
                                + world['electricity_share_init']
                                for i in range(t_end - t_init + 1)]

    solar =  {'name': 'solar', 'cost_init': 1300, 'power_init': 3693e6,
            'tau_life': 30, 'td0': td0,
            'tau_exp': 4, 'fit_factor': fit_factor, 'cap_factor': 0.17,
            'intermittent': True}
    solar['power_current'] = solar['power_init']
    solar['p_sat'] = world['energy_demand_total']*world['electricity_share_end']*energy_mix['solar']/solar['cap_factor']
    solar['cost_init'] = solar['cost_init']/(24*365*solar['cap_factor']) #conversion from euro/kW to euro/kWh
    
    
    wind = {'name': 'wind', 'cost_init': 1300, 'power_init': 10030e6,
            'tau_life': 25, 'td0': td0,
            'tau_exp': 4, 'fit_factor': fit_factor, 'cap_factor': 0.45,
            'intermittent': True}
    wind['power_current'] = wind['power_init']
    wind['p_sat'] = world['energy_demand_total']*world['electricity_share_end']*energy_mix['wind']/wind['cap_factor']
    wind['cost_init'] = wind['cost_init']/(24*365*wind['cap_factor'])
                                                 
    nuclear = {'name': 'nuclear', 'cost_init': 6000, 'power_init': 4000e6,
            'tau_life': 40, 'td0': td0,
            'tau_exp': 4, 'fit_factor': fit_factor, 'cap_factor': 0.9,
            'intermittent': False}
    nuclear['power_current'] = nuclear['power_init']
    nuclear['p_sat'] = world['energy_demand_total']*world['electricity_share_end']*energy_mix['nuclear']/nuclear['cap_factor']
    nuclear['cost_init'] = nuclear['cost_init']/(24*365*nuclear['cap_factor'])
                                           
    list_of_params = [solar, wind, nuclear]

    # PHS
    pumped_hydro_capacity_europe = 640 + 1032 + 600 + 560 + 8480 + 504 + 2087 + 590 + 950 + 4018 + 591 + 690 + 2064 + 487 + 3428 + 476 + 523 + 642 + 1300 + 24500 + 36400 + 3600 + 4675
    NL_frac_europe = 0.05
    # 'cost_init': 75, 'power_init': pumped_hydro_capacity_europe*1e6*NL_frac_europe,
    # 'tau_life': 50,
    # Li-ion
    # 'cost_init': 380, 'power_init': 0.03e6,
    # 'tau_life': 15

    storage = {'name': 'storage', 'cost_init': 75, 'power_init': pumped_hydro_capacity_europe*1e6*NL_frac_europe,
            'tau_exp': 4, 'tau_life': 50, 'td0': td0,'cap_factor': 0.85,
            'fit_factor': fit_factor, 'intermittent': False}
    storage['power_current'] = storage['power_init']
    storage['p_sat'] = sum([i['p_sat']/12/storage['cap_factor'] for i in
                            list_of_params if i['intermittent']==True])

    list_of_params.append(storage)
    
    
    return list_of_params, world, t_init

def solver(parameters, energy_mix, t_end, max_budget, electricity_share_end, visualization):
    
    list_of_params, world, t_init = initial_params(energy_mix, t_end, electricity_share_end)
    co2_total = 0
    cost = 0
    saturation_years={method:np.zeros(2) for method in parameters}
    
    if visualization == 1:
        growth_matrix = np.zeros((len(list_of_params),t_end - t_init + 2))
        power_matrix = np.zeros((len(list_of_params),t_end - t_init + 2))
        
        
        invest_matrix = np.zeros((len(list_of_params),t_end - t_init + 2))
        integrated_invest_matrix=np.zeros((len(list_of_params),t_end - t_init + 2))
        
        co2_yearly_matrix = np.zeros((1,t_end - t_init + 2))
        co2_total_matrix = np.zeros((1,t_end - t_init + 2))        
        costs_total_matrix = np.zeros((1,t_end - t_init + 2))
    
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
            invest = parameters[renewable['name']][year]*max_budget
            power_current = renewable['power_current']
            cost_current = renewable['cost_init']*(0.5)**log10(power_current/renewable['power_init'])
            tau_life = renewable['tau_life']
            td0 = renewable['td0']
            tau_exp = renewable['tau_exp']
            p_sat = renewable['p_sat']
            fit_factor = renewable['fit_factor']
            if tau_exp < 0:
                p_trans = p_sat
            else:
                p_trans = p_sat*tau_exp/tau_life
            
       
            if power_current >= p_sat:
                growth = 0
                # invest = 0
                #invest = parameters[renewable['name']][i]*max_budget
                #year of saturation
                if saturation_years[renewable['name']][1] == 0:
                    saturation_years[renewable['name']][1] = year+t_init        
                if     saturation_years[renewable['name']][0] == 0:
                    saturation_years[renewable['name']][0] = year+t_init
                 
            elif power_current < p_trans: #exponential
                               
                growth = power_current*(exp(log(2)/td0 + invest/(cost_current*fit_factor*p_trans)) - 1)
                
                #print(renewable['tau_exp'])
                
                if power_current + growth > p_trans:
                    growth = (p_trans - power_current)*1.01
                else:
                    renewable['tau_exp'] = 1/(log(2)/td0 + invest/(cost_current*fit_factor*p_trans))
                
            elif power_current >= p_trans: #linear
                fit_factor = 1 #linear fit factor
                renewable['fit_factor'] = fit_factor
                growth = p_sat/tau_life + invest/(cost_current*fit_factor)
                if     saturation_years[renewable['name']][0] == 0:
                    saturation_years[renewable['name']][0] = year+t_init
                                    
            if power_current + growth > p_sat:
                growth = p_sat - power_current
                #invest = (growth - p_sat/tau_life)*(cost_current*fit_factor)
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
                integrated_invest_matrix[i,year+1] = sum(invest_matrix[i,0:year+1])
                costs_total_matrix[0,year+1] = cost
                
    percentage={method['name']: int(method['power_current']/method['p_sat']*100) for method in list_of_params}
                    
    if visualization == 1:
        years = list(range(t_init-1,t_end+1))
        ax = plt.gca()
        
        
        #plot for nominal installed capacity per energy source
        for i, row in enumerate(power_matrix):
            plt.plot(years, row/1e9, label=list_of_params[i]['name'])
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles, labels)
        ax.set_ylim(ymin=0)
        ax.set_xlim(xmin=2020)
        plt.xlabel('Year')
        plt.ylabel('Nominal Installed Capacity (TWh)')
        plt.grid(True)
        plt.tick_params(direction='in', axis='both', which='both', top='True', right='True')
        plt.show()
        
        ax = plt.gca()
        
        #plot for normalised electricity production
        for i, row in enumerate(power_matrix):
            plt.plot(years, row/list_of_params[i]['p_sat'], label=list_of_params[i]['name'])
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles, labels)
        ax.set_ylim(ymin=0)
        ax.set_xlim(xmin=2020)
        plt.xlabel('Year')
        plt.ylabel('Electricity Production (norm)')
        plt.grid(True)
        plt.tick_params(direction='in', axis='both', which='both', top='True', right='True')
        plt.show()
        
        
        #plot for yearly co2 production with grand total plotted  
        fig, ax1 = plt.subplots()
        color = 'tab:blue'
        ax1.bar(years, co2_yearly_matrix[0,:]/1e9,color=color)
        ax1.set_ylim(ymin=0)
        ax1.set_xlabel('Year')
        ax1.set_ylabel('CO2 emissions (billion kg/year)',color=color)
        ax1.tick_params(axis='y', labelcolor=color)
        plt.grid(True)
        plt.tick_params(direction='in', axis='both', which='both', top='True', right='True')
        
        ax2 = ax1.twinx()
        color = 'tab:red'
        ax2.plot(years,co2_total_matrix[0,:]/1e9,'--o',color=color)
        ax2.set_ylabel('Integrated CO2 emissions (billion kg)',color=color)
        ax2.set_ylim(ymin=0)
        ax2.tick_params(axis='y', labelcolor=color)
        plt.tick_params(direction='in', axis='both', which='both', top='True', right='True')
        
        fig.tight_layout()  # otherwise the right y-label is slightly clipped
        plt.show()
        
        #plot for the total costs per renewable
        #generation only
        ax = plt.gca()
        for i, row in enumerate(invest_matrix[:-1]):
            if i == 0:
                bottom = np.zeros(len(row))
            else:
                bottom = sum(invest_matrix[:i])/1e9
            plt.bar(years, row/1e9, bottom = bottom, label=list_of_params[i]['name'])
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles, labels)
        ax.set_xlim(xmin=2020)
        plt.xlabel('Year')
        plt.ylabel('Yearly investment per renewable (billion euros)')
        plt.grid(True)
        plt.tick_params(direction='in', axis='both', which='both', top='True', right='True')
        plt.show()
        #storage + generation
        ax = plt.gca()
        plt.bar(years, invest_matrix[-1]/1e9,color='tab:red', label=list_of_params[-1]['name'])
        plt.bar(years, sum(invest_matrix[:-1])/1e9,color='m',bottom=invest_matrix[-1]/1e9, label='all renewables')
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles, labels,loc='lower right')
        ax.set_xlim(xmin=2020)
        plt.xlabel('Year')
        plt.ylabel('Yearly investment (billion euros)')
        plt.grid(True)
        plt.tick_params(direction='in', axis='both', which='both', top='True', right='True')
        plt.show()
        
                
    return cost, co2_total, percentage, saturation_years
 
