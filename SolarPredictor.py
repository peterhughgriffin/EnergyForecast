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


def GetVals(Solar,Start, End):
        Start = arrow.Arrow.strptime(Start,"%Y-%m-%d")
        End = arrow.Arrow.strptime(End,"%Y-%m-%d")
        
        PeakDays={}
        Peak=[]
        BestDays={}
        Best=[]
        WorstDays={}
        Worst=[]
        
        for First in arrow.Arrow.range('month', Start, End):
            
            Last=First.shift(months=1,days=-1)
            
            FirstInd = Solar.GetInd(First)
            LastInd = Solar.GetInd(Last)
            
            Val_Best = max (Solar.TotalGen[FirstInd : LastInd])
            Ind_Best = Solar.TotalGen[FirstInd : LastInd].index(Val_Best)
            Date = list(Solar.data.keys())[FirstInd+Ind_Best]
            Best.append(Date)
            BestDays[Date] = Val_Best
            
            Val_Peak = max (Solar.PeakGen[FirstInd : LastInd])
            Ind_Peak = Solar.PeakGen[FirstInd : LastInd].index(Val_Peak)
            Date = list(Solar.data.keys())[FirstInd+Ind_Peak]
            Peak.append(Date)
            PeakDays[Date] = Val_Peak
            
            Val_Worst = min (Solar.TotalGen[FirstInd : LastInd])
            Ind_Worst = Solar.TotalGen[FirstInd : LastInd].index(Val_Worst)
            Date = list(Solar.data.keys())[FirstInd+Ind_Worst]
            Worst.append(Date)
            WorstDays[Date] = Val_Worst
            
        Vals={'Peak' : PeakDays,
              'Best' : BestDays,
              'Worst': WorstDays
              }
        
        Indices={'Peak' : Peak,
                 'Best' : Best,
                 'Worst': Worst
                 }
        
        return (Indices,Vals)


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


    def PlotGen(self,Start,End,Leg=True, SpecificPoints = [], Window=1, Peak=False,Total=False):
        """
        This is the plotting function. It has various options that control what you plot.
            Start - Start date of data to plot
            End - End date of data to plot
            Leg - Toggles whether the legend is shown or not.
            SpecificPoints - A list of dates, if non-empty then the generation 
                            solar curves just these dates are plotted against HH.
                The following parameters are only used if SpecificPoints is empty.
            Window - The size of the window used for smoothing via moving average.
            Peak - If true then the Peak value of each day is plotted against date.
            Total - If true then the total generation is plotted against date.
        If SpecificPoints, Peak and Total are all False then generation is
        plotted against HH for each date in the given range.
        """
        
        if SpecificPoints:
            
            fig=plt.figure()
            
            for i in SpecificPoints:
                HH=self.data[i]['HH']
                Gen=self.data[i]['Generation']
                plt.plot(HH,Gen,label=i)
            
            plt.ylabel("Solar (MW)")
            plt.xlabel("HH")
            if Leg:
                fig.legend()
        
        elif Peak or Total:
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
            
            if Leg:
                fig.legend()
        else:
            
            DateList=list(self.data.keys())[self.GetInd(Start):self.GetInd(End)]
            
            fig=plt.figure()
            
            for i in DateList:
                HH=self.data[i]['HH']
                Gen=self.data[i]['Generation']
                plt.plot(HH,Gen,label=i)
            
            plt.ylabel("Solar (MW)\n"+str(Window) + " day moving average")
            plt.xlabel("HH")
            if Leg:
                fig.legend()
                
    



# Start = arrow.get("2017-12-31T23:59:59")
Start = arrow.get("2013-01-01T00:00:00")
# Start = arrow.get("2020-01-01T00:00:00")
# End = arrow.get("2020-06-16T23:59:59")

Solar=SolarData(Start)

Solar.Calculate()

#%%

Start = "2019-01-01"
End = "2019-12-31"

KeyDates , KeyVals = GetVals(Solar,Start,End)

# Plot key dates of interest
Solar.PlotGen(Start,End,SpecificPoints = KeyDates['Best'])
Solar.PlotGen(Start,End,SpecificPoints = KeyDates['Peak'])
Solar.PlotGen(Start,End,SpecificPoints = KeyDates['Worst'])

# Plot key metrics
Solar.PlotGen(Start,End,Window=30,Total=True)
Solar.PlotGen(Start,End,Window=30,Peak=True)

# Plot all by HH
Solar.PlotGen(Start,End,Leg=False)


#%%

    


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



