'''
Created on Jan 18, 2017

Keeps track of if we are using live data or historical data.

Manages if the trades should be sent to OANDA or just written to the file.


@author: Zohar
'''
import csv
import datetime
import numpy
import Warnings

class Trades:
    def __init__(self, live, Connection):
        self.live = live
        self.TradeLog = open('TradeLog.csv', 'a',newline='')
        self.TLog = csv.writer(self.TradeLog)
        #OANDA initialization
        if(self.live == True):
            self.Connection = Connection
            self.sendToOANDA = True
        #Backtesting Initialization
        else:
            self.sendToOANDA = False
            self.Score = 0.0
            self.EventLogging = open('EventLog.csv', 'w',newline='')
            self.ELog = csv.writer(self.EventLogging)
            self.ELog.writerow([datetime.datetime.now(datetime.timezone.utc), "Started running code"])
    
    #Each trade object has variables assigned to assist trade management
    def manageTrades(self,tradeList, currentBidAsk):
        self.currentTime = currentBidAsk[0,0]
        temp = numpy.array(currentBidAsk[0,[1,2]])
        self.currentBidAsk = temp.astype(float)
        for trade in tradeList:
            #Check if we need to open the trade
            if(trade.opened == False):
                #First go of making sure the trade makes sense
                if(self.sendToOANDA == True and self.Connection.percentMargin < .8):
                    self.Connection.openTrade(trade)
                elif(self.sendToOANDA == True and self.Connection.percentMargin > .8):
                    Warnings.ProcessError('More than 80% of Margin used', True, 0)
                #Backtesting trade code
                else:
                    if(trade.buy == True):
                        self.TLog.writerow(["Buy trade started at price:", self.currentBidAsk[1]  ," and time: ", self.currentTime])
                    else:
                        self.TLog.writerow(["Sell trade started at price:", self.currentBidAsk[0]  ," and time: ", self.currentTime])
                    self.Score -= trade.algoOpenPrice*trade.tradeLots
                    self.ELog.writerow([ self.currentTime, "Opened a trade of ", trade.tradeLots*100000, " units at ", " price: ", trade.algoOpenPrice])
                trade.opened = True
            #Check if any trades are to be closed
            if(trade.markedToClose == True):
                #OANDA section
                if(self.sendToOANDA == True): #TODO, doesn't currently enforce FIFO rules
                    self.Connection.closeTrade(trade)
                #Backtesting section
                else:
                    if(trade.buy == True):
                        self.TLog.writerow(["Buy trade ended at price: ", self.currentBidAsk[0] , " and time: ", self.currentTime])
                        self.Score += self.currentBidAsk[0]*trade.tradeLots
                        self.ELog.writerow([ self.currentTime, " Closed a trade of ", trade.tradeLots*100000, " units at ", " price: ", self.currentBidAsk[0] ])
                    if(trade.sell == True):
                        self.TLog.writerow(["Sell trade ended at price: ", self.currentBidAsk[1] , " and time: ", self.currentTime])
                        self.Score += self.currentBidAsk[1]*trade.tradeLots
                        self.ELog.writerow([ self.currentTime, " Closed a trade of ", trade.tradeLots*100000, " units at ", " price: ", self.currentBidAsk[1] ])
                tradeList.remove(trade)

    #For cleanup when the code terminates
    def closeCSVs(self, tradeList, currentBidAsk):
        if(self.sendToOANDA==True):
            self.Connection.closeCSVs()
        else:
            if(len(tradeList)>.5):
                for trade in tradeList: 
                    trade.markedToClose = True
                self.manageTrades(tradeList, currentBidAsk)
            self.ELog.writerow([ datetime.datetime.now(datetime.timezone.utc), "Final Score (MAKE SURE YOU ADJUST HOW THIS IS COMPUTED FOR YOUR CASE!) ", self.Score])
            self.EventLogging.close()