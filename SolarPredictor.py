#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  5 16:30:37 2020

@author: peter


Data Sources:
    Sheffield Solar provide a subscription API service, which forecasts the next 72 hours.
    https://api.solar.sheffield.ac.uk/pvforecast/docs/
    
    Can get historical solar Data from here:
    https://api0.solar.sheffield.ac.uk/pvlive/v2/?regionid=327&start=2017-12-01T12:00:00&end=2017-12-31T23:59:59

    Regions are quite small, 1-327, based around NG substations 0 is national


"""

# Used to import Sheffield Solar data
import requests
import arrow
import matplotlib.pyplot as plt
import matplotlib.dates as dates
import pandas as pd
import math


def GetHistoricalGen(Start, End, RegionID=0):
    '''A function to get Historical Solar data from Sheffield Solar
    INPUTS:
        Start - Start datetime stamp in string format "YYYY-MM-DDTHH:MM:SS"
        End - End datetime stamp in string format "YYYY-MM-DDTHH:MM:SS"
        RegionID -  0 is whole country there are 327 regions, based around NG substations
    
    
    '''
    
    Start=Start.format("YYYY-MM-DDTHH:MM:SS")
    End=End.format("YYYY-MM-DDTHH:MM:SS")
    RegionID=str(RegionID)
    endpoint = "https://api0.solar.sheffield.ac.uk/pvlive/v2/?regionid="+RegionID+"&start="+Start+"&end="+End
    return(requests.get(endpoint))

def toHH(time):
    try:
        str(time)
    except:
        KeyError('time should be a string')
    Hour = int(time[0:2])
    Mins = int(time[3:5])
    
    HH = Hour*2+math.floor(Mins/30)+1
    return HH


#%%
# Start = arrow.get("2020-04-01T00:00:00")
# End = arrow.get("2020-04-01T23:59:59")

# response=GetHistoricalGen(Start,End)

# dt=[]
# gen=[]
# for item in response.json()['data']:
#     dt.append(item[1])
#     gen.append(item[2])

# SolarGen={'dt':dt,'Generation':gen}


# # print(SolarGen)
# fig=plt.figure()
# plt.plot(SolarGen['dt'],SolarGen['Generation'])
# plt.ylabel("Generation (MW)")
# plt.xlabel("Date time stamp")
# fig.autofmt_xdate()



#%%

Start = arrow.get("2017-12-31T23:59:59")
Start = arrow.get("2017-01-01T00:00:00")
# Start = arrow.get("2020-04-01T00:00:00")
End = arrow.get("2020-04-30T23:59:59")

response=GetHistoricalGen(Start,End)

Date=[]
PrevDate=arrow.get("1900-01-01")
Gen={}

for item in response.json()['data']:
    dt = item[1] 
    date, time = dt.split('T')
    date=arrow.get(date)
    gen = item[2]
    HH=toHH(time)
    if date==PrevDate:
        Gen[date]['HH'].append(HH)
        Gen[date]['Generation'].append(gen)
        Gen[date]['dt'].append(dt)
    else:
        PrevDate=date
        Gen[date]={'dt':[dt],'HH':[HH],'Generation':[gen]}

# SolarGen=pd.DataFrame.from_dict(Gen,orient="index")


#%% Calculate some useful metrics and add them into the dict

for date in Gen:
    Gen[date]['PeakGen']=max(Gen[date]['Generation'])
    Gen[date]['TotalGen']=sum(Gen[date]['Generation'])
    Index = [i for i, e in enumerate(Gen[date]['Generation']) if e != 0]
    Gen[date]['GenStart'] = Gen[date]['HH'][min(Index)]
    Gen[date]['GenEnd'] = Gen[date]['HH'][max(Index)]
                                      



#%%

# fig=plt.figure()
# plt.plot(Gen.keys(),Gen[date]['GenStart'])
# # plt.ylabel("Generation (MW)")
# # plt.xlabel("Date time stamp")
# fig.autofmt_xdate()




