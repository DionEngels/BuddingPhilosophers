# -*- coding: utf-8 -*-
"""
Created on Mon Jun 15 04:20:20 2020

@author: mepsm
"""

#%%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from math import log


#%% Plot of US hydro, solar, wind generation over time

E_year = pd.read_csv("Downloads\generation-renewable-sources.csv")
E_result = E_year[(E_year['year'] >= 2007) & (E_year['year'] <= 2017)]
print(E_result)
logy = True
ax = plt.gca()
E_year.plot(x='year',y='hydroelectric',logy=logy,ax=ax)
E_year.plot(x='year',y='solar',logy=logy,ax=ax)
E_year.plot(x='year',y='wind',logy=logy,ax=ax)
#solar exponential ~2010-2015, doubling time ~2years
#wind exponential ~2000-2010, doubling time~4years

#%% Calculation of base doubling time and fit factor

# array columns give 2007, 2010, 2013, 2016 values
# array rows give PV, onshore wind
Gi = 1e6*np.array([[14*1.1575,1116,5756,2231],[724*1.1575, 5705,6187,1266]]) #[1] in 2016 dollars
#Gi = np.zeros(np.shape(Gi))
Cw = 1e3*np.array([[7.45,7.06,4.450,2.671],[1.85,2.26,2.354,1.877]]) #[2,3]
E0 = 1e9*np.array([[0.61, 1.21, 9.04, 36.05],[34.45, 94.65, 167.84,226.99]]) #[4]
Cap_factor = np.array([0.20,0.35]) #[3] #from here on first value gives PV, second wind
P0 = np.zeros(np.shape(E0))
for i in range(np.shape(E0)[1]):
    P0[:,i] = E0[:,i]/(24*365*Cap_factor)
Psat = 1e9*np.array([100, 350])/(24*365*Cap_factor) #estimates from graph
tdeff = np.array([2,4]) #estimates from graph/data
#taulife = np.array([2025-2015, 2025-2008]) # "
taulife = np.array([30,30]) # more reasonable
Ptrans = Psat*tdeff/np.log(2)/taulife
td0 = np.zeros([3,2])
fit_factor_est = 1e-1 # 1 -> a bit larger than effective
                      # 1e2 -> even less a bit than effective
                      # 1e-1 -> -1
                      # but this doesn't make sense... government
                        # input gets compounded? price $1/kW, spend
                        # $10, get out 100 kW??
                      # no... get out 1/ff*Ptrans, in this case 10/Ptrans
fit_factor1 = np.zeros([3,2])
fit_factor2 = np.zeros([3,2])
fit_factor3 = np.zeros([3,2])
td0_est = np.array([-1,-1])

for i in range(1,4): #2010,2013,2016
# incorrect formula
    #td0 = 3/(np.log(2**(3/tdeff) - 1.5*(Gi[:,i-1]+Gi[:,i])/(Cw[:,i]*P0[:,i-1]))/np.log(2))
# first formula, exponential
    fit_factor1[i-1,:] = (0.5*(Gi[:,i-1]+Gi[:,i])/(Cw[:,i]*Ptrans))/(log(2)/tdeff - log(2)/td0_est)
# second formula, exponential, estimate
    fit_factor2[i-1,:] = (tdeff*0.5*(Gi[:,i-1]+Gi[:,i]))/(Cw[:,i]*Ptrans*log(2))
# third formula, linear
    fit_factor3[i-1,:] = (0.5*(Gi[:,i-1]+Gi[:,i])/Cw[:,i])*1/((P0[:,i]-P0[:,i-1])/3 - Psat/taulife)
    tau0 = 1/((np.log(2)/tdeff) - 0.5*(Gi[:,i-1]+Gi[:,i])/(fit_factor_est*Cw[:,i]*Ptrans))
    #first data point is the only "reliable" one because in 2016 solar and wind
        #aren't even in exponential growth anymore (see plots below)
    td0[i-1,:] = tau0*np.log(2)
    
    # print('ff2', fit_factor2)
    # print('tdeff?', 1/((0.5*(Gi[:,i-1]+Gi[:,i]))/(fit_factor2[i-1,:]*Cw[:,i]*Ptrans*log(2))))
    # ^ should exactly equal tdeff
    # print('tau0', tau0)
print('ff1 (exponential)\n', fit_factor1)
#print('ff2 (approx)\n', fit_factor2)
print('ff3 (linear)\n', fit_factor3)
print('base doubling time\n', td0)
# problem: first and last confirm each other
# problem: ff exp 0.1 ok, but ff linear 0.5? trending higher though
    # perhaps could define fit factor 1/10 td0 -0.5 ish, then in linear redefine fit factor 1
#sources: [1] EIA fed financing 2016 and 2007, inflation rate from https://www.in2013dollars.com/
#         [2] EIA cap cost 2016
#         [3] https://openei.org/apps/TCDB/#blank
#         [4] generation-renewable-sources


#%% Calculation of actual doubling times from data, 

# i know this is gross don't judge me
tdouble = [[],[]]
for i, row in E_year.iterrows():
    print(i)
    if i == 68:
        break
    if i == 0:
        pv_prev = row['solar']
        w_prev = row['wind']
    elif pv_prev == 0 or pv_prev == 0:
        pv_prev = row['solar']
        w_prev = row['wind']
        tdouble[0].append(0)
        tdouble[1].append(0)
    elif log(row['solar']/pv_prev)==0 or log(row['wind']/w_prev)==0:
        pv_prev = row['solar']
        w_prev = row['wind']
        tdouble[0].append(0)
        tdouble[1].append(0)
    else:
        tdouble[0].append( 1/log(row['solar']/pv_prev))
        tdouble[1].append( 1/log(row['wind']/w_prev))
        pv_prev = row['solar']
        w_prev = row['wind']

def moving_average(a, n=3) :
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n


#plt.plot(E_year.to_numpy()[1:-2,0], tdouble[0])
#plt.plot(E_year.to_numpy()[1:-2,0], tdouble[1])
plt.plot(E_year.to_numpy()[3:-4,0], moving_average(np.asarray(tdouble[0]),n=5))

    
    
    