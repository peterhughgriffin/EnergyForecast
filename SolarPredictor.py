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
import numpy as np


def GetHistoricalGen(Start, End, RegionID=0):
    '''
    This function gets Historical Solar data from Sheffield Solar given:
        Start - Start datetime stamp in string format "YYYY-MM-DDTHH:MM:SS"
        End - End datetime stamp in string format "YYYY-MM-DDTHH:MM:SS"
        RegionID -  0 is whole country there are 327 regions, based around NG substations
    '''
    
    Start=Start.format("YYYY-MM-DDTHH:mm:ss")
    print(Start)
    End=End.format("YYYY-MM-DDTHH:mm:ss")
    print(End)
    RegionID=str(RegionID)
    endpoint = "https://api0.solar.sheffield.ac.uk/pvlive/v2/?regionid="+RegionID+"&start="+Start+"&end="+End
    data=requests.get(endpoint)
    print("Requesting data from:\n"+endpoint)
    try:
        data.json()['data']
    except:
        raise ValueError("No data returned from Sheffield Solar server")
            
    return(data)

def toHH(time):
    """
    This function converts a given time to the half hour it is within. Given:
        time - The time as a string
    """
    try:
        str(time)
    except:
        TypeError('Time should be a string')
    Hour = int(time[0:2])
    Mins = int(time[3:5])
    
    HH = Hour*2+math.floor(Mins/30)+1
    return HH


"""
This function performs a moving average on a series, given:
    data - the series
    w - the window size
"""
def MovAve(data,w):
    mask=np.ones((1,w))/w
    mask=mask[0,:]
    
    return np.convolve(data,mask,'valid')



class SolarData:
    """
    A class for collecting and manipulating hostorical solar data.
    
    FUNCTIONS:
        __init__
            This initialises a SolarData object and uses the GetHistoricalGen
            function to get solar data for the requested time period.
    """

    def __init__(self,Start,End = arrow.utcnow()):
        """
        Initialises a SolarData object and use the GetHistoricalGen function to get
        solar data for the requested time period.
            Start - The beginning of the requested time period (earliest available data is "2013-01-01")
            End - The end of the requested time period (default is now)
        """
        # Import the raw data
        response=GetHistoricalGen(Start,End)
        
        PrevDate=arrow.get("1900-01-01")
        self.data={}
        
        for item in response.json()['data']:
            dt = item[1] 
            date, time = dt.split('T')
            date=arrow.get(date)
            gen = item[2]
            HH=toHH(time)
            if date==PrevDate:
                self.data[date]['HH'].append(HH)
                self.data[date]['Generation'].append(gen)
                self.data[date]['dt'].append(dt)
            else:
                PrevDate=date
                self.data[date]={'dt':[dt],'HH':[HH],'Generation':[gen]}


    def GetInd(self,target):  
        """
        This function returns the index for a given date in the calculated values given
            target - The target date either as an Arrow object or one that Arrow can convert
        """
        if type(target)!=arrow.Arrow:
            target=arrow.get(target)
        return list(self.data.keys()).index(target)


    def Calculate(self):
        """
        Calculates some useful metrics across the whole dataset and adds them to the Class object
        """
        self.PeakGen = []
        self.TotalGen = []
        self.GenStart = []
        self.GenEnd = []
        
        for date in self.data:
            
            self.PeakGen.append(max(self.data[date]['Generation']))
            self.TotalGen.append(sum(self.data[date]['Generation']))
            Index = [i for i, e in enumerate(self.data[date]['Generation']) if e != 0]
            self.GenStart.append( self.data[date]['HH'][min(Index)])
            self.GenEnd.append(self.data[date]['HH'][max(Index)])


    def PlotGen(self,Start,End,Window=1,Peak=True,Total=True):
        """
        
        """
        # Check we have something to plot
        if Peak or Total:
            # Check Window size is smaller than data length
            if self.GetInd(End)-(self.GetInd(Start)+Window-1)<=Window:
                raise ValueError("Your window size is smaller than the number of dates requested. Reduce Window")
            
            
            if Peak:
                PeakGen=self.PeakGen[self.GetInd(Start):self.GetInd(End)]
                PeakGenSmooth=MovAve(PeakGen,Window)
                
            if Total:
                TotalGen=self.TotalGen[self.GetInd(Start):self.GetInd(End)]
                TotalGenSmooth=MovAve(TotalGen,Window)
                
                
            DateList=list(self.data.keys())[self.GetInd(Start)+Window-1:self.GetInd(End)]
            
            fig=plt.figure()
            if Peak:
                plt.plot([i.datetime for i in DateList],PeakGenSmooth,label='Peak Generation')
            if Total:
                plt.plot([i.datetime for i in DateList],TotalGenSmooth,label='Total Generation')
            plt.ylabel("Daily Solar (MW)\n"+str(Window) + " day moving average")
            plt.xlabel("Date")
            fig.autofmt_xdate()
            
            fig.legend()
        else:
            print("Nothing to plot :(")


#%%

# Start = arrow.get("2017-12-31T23:59:59")
# Start = arrow.get("2013-01-01T00:00:00")
Start = arrow.get("2020-01-01T00:00:00")
# End = arrow.get("2020-06-16T23:59:59")

Solar=SolarData(Start)

Solar.Calculate()
#%%

Start = "2020-01-01"
End = "2020-06-15"


Solar.PlotGen(Start,End,7,False,True)


#%%
fig=plt.figure()
plt.plot([i.datetime for i in list(Solar.data.keys())],Solar.GenEnd,label='End')
plt.plot([i.datetime for i in list(Solar.data.keys())],Solar.GenStart,label='Start')
plt.ylabel("HH")
plt.xlabel("Date time stamp")
fig.autofmt_xdate()

fig.legend()


#%%
fig=plt.figure()
plt.plot([i.datetime for i in list(Solar.data.keys())],Solar.PeakGen,label='Peak Generation')
plt.plot([i.datetime for i in list(Solar.data.keys())],Solar.TotalGen,label='Total Generation')
plt.ylabel("Generation")
plt.xlabel("Date time stamp")
fig.autofmt_xdate()

fig.legend()
#%%

Start = "2020-01-01"
End = "2020-06-15"

w=1

PeakGenSmooth=MovAve(Solar.PeakGen,w)[Solar.GetInd(Start)+w-1:Solar.GetInd(End)]
TotalGenSmooth=MovAve(Solar.TotalGen,w)[Solar.GetInd(Start)+w-1:Solar.GetInd(End)]

if len(PeakGenSmooth)<=w:
    raise ValueError("Your window size is smaller than the number of dates requested. Reduce w")


fig=plt.figure()
# plt.plot([i.datetime for i in list(Solar.data.keys())[w-1:]],PeakGenSmooth,label='Peak Generation')
plt.plot([i.datetime for i in list(Solar.data.keys())[Solar.GetInd(Start)+w-1:Solar.GetInd(End)]],TotalGenSmooth,label='Total Generation')
plt.ylabel("Daily Solar (MW)\n"+str(w) + " day moving average")
plt.xlabel("Date")
fig.autofmt_xdate()

fig.legend()

#%%



#%%

Start = arrow.get("2020-04-01T00:00:00")
End = arrow.get("2020-04-01T23:59:59")

response=GetHistoricalGen(Start,End)

dt=[]
gen=[]
for item in response.json()['data']:
    dt.append(item[1])
    gen.append(item[2])

SolarGen={'dt':dt,'Generation':gen}


# print(SolarGen)
fig=plt.figure()
plt.plot(SolarGen['dt'],SolarGen['Generation'])
plt.ylabel("Generation (MW)")
plt.xlabel("Date time stamp")
fig.autofmt_xdate()

