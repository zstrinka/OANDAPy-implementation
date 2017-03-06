'''
Created on Jan 13, 2017

Keeps track of if we are using live data or historical data.

This is an event-driven backtester because it gets a new row of data and then makes decisions for the future.

@author: Zohar
'''
numberOfMins = 100 #This code assumes you start each week from scratch. This is how many minutes you use to make entry decisions.
import numpy
import csv

class InputData:
    #Time and Price list of lists initialization
    def __init__(self, live, Connection, SinceOpen = numberOfMins):
        if(live == True):
            self.getFromOANDA = True
            self.Connection = Connection
            if(SinceOpen > numberOfMins):
                SinceOpen = numberOfMins
            # If the trading week has already started, call the appropriate amount of bars from the server
            # get numberOfBars from Scheduler
            self.timeAndPrice = numpy.array(self.Connection.getMinuteData(SinceOpen))
        else:
            self.getFromOANDA = False
            self.allData = numpy.array(self.readDataCSV('Feb6_2017.csv'))
            self.timeAndPrice = self.allData[1:SinceOpen,:]
            self.currentRow = SinceOpen
    def readDataCSV(self,filename):
        minuteData = []
        with open(filename, newline='') as csvfile:
            reader = csv.reader(csvfile)
            next(reader, None) #skip first line
            for row in reader:
                time = row[0]
                bid = row[1]
                ask = row[2]
                minuteData.append([time,bid,ask])
        return minuteData
    
       
    def getNextMinute(self):
        if(self.getFromOANDA == True):
            nextMinute = self.Connection.getBidAsk(self.timeAndPrice[-1,0]) 
        else:
            #Load from .csv file
            self.currentRow +=1 
            nextMinute = self.allData[self.currentRow]
        self.timeAndPrice = numpy.vstack([self.timeAndPrice, nextMinute])
    
    def dataForAlgorithm(self):
        #will use slicing to get the right subset of timeAndPrice
        return(self.timeAndPrice[-numberOfMins:,2])
    def bidAsk(self):
        #will use slicing to get the current bid and ask prices
        return(self.timeAndPrice[-1:,])