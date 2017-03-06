'''
Created on Jan 11, 2017

Called by conductor with data to make decisions about placing or ending trades

TODO Someday: Fix that data comes in as strings to the algo

@author: Zohar
'''
import numpy
import Trades
import csv
import datetime

class Model:
    
    
    
    def __init__(self,data, currentBidAsk, allTrades, margin, minutesToCloseTime, thisLogging):
        self.pricedata = data.astype(numpy.float)
        self.currentPrice = self.pricedata[-1]
        self.currentTime = currentBidAsk[0,0]
        self.nextEvent = minutesToCloseTime
        self.margin = margin
        self.numLots = .01 #Minimum lot size for OANDA
        temp = numpy.array(currentBidAsk[0,[1,2]])
        self.currentBidAsk = temp.astype(float)
        self.checkForTrades(allTrades, thisLogging)
        self.checkForExits(allTrades)

    def checkForTrades(self,tradelist,thisLogging):
        startBuy = False
        startSell = False
        
        # Enter your entry rules here!
        buyCon = numpy.mean(self.pricedata[-100:])+ 0.05 < numpy.minimum(self.currentBidAsk[1],numpy.mean(self.pricedata[-30:]))
        sellCon = numpy.mean(self.pricedata[-100:]) - 0.05 > numpy.maximum(self.currentBidAsk[1],numpy.mean(self.pricedata[-30:]))
        
        thisLogging.ALog.writerow([self.currentTime,buyCon,sellCon,self.currentBidAsk[0],self.currentBidAsk[1]])
    
        if(buyCon):
            startBuy = True
        if(sellCon):
            startSell = True
        
        #This section ensures that if your strategy says it is time to start the opposite trade, you close out that trade
        # Enter Stoploss and Trailing stop values here!
        alreadyHaveTrade = False
        if(startBuy == True):
            for trade in tradelist:
                if(trade.sell == True):
                    alreadyHaveTrade = True
                    trade.markedToClose = True
                elif(trade.buy == True):
                    alreadyHaveTrade = True
            if(alreadyHaveTrade == False and self.nextEvent > 60):
                self.SL =  self.currentBidAsk[1] - .2
                self.TS = .05 #TODO, I think TS is a fraction of the current price, but still working it out for sure
                tradelist.append(Trades.TradeInstance(1, self.currentBidAsk[1],self.numLots,self.SL, self.TS ,False))
        if(startSell == True):
            for trade in tradelist:
                if(trade.buy == True):
                    trade.markedToClose = True
                elif(trade.sell == True):
                    alreadyHaveTrade = True
                    self.numLots = trade.tradeLots
            if(alreadyHaveTrade == False and self.nextEvent > 60):
                self.SL =  self.currentBidAsk[0] + .2
                self.TS = .05 #TODO, I think TS is a fraction of the current price, but still working it out for sure
                tradelist.append(Trades.TradeInstance(-1, self.currentBidAsk[0],self.numLots,self.SL,self.TS,False))
        

    
    def checkForExits(self,allTrades):
        #Enter your exit rules below!
        
        exitAll = False #The code currently only handles one trade at a time, but this function can exit all trades
        for trade in allTrades:
            if(trade.buy == True):
                if(self.currentPrice> trade.BestPrice):
                    trade.BestPrice = self.currentPrice
                if(self.currentPrice < trade.SL or numpy.mean(self.pricedata[-30:]) <numpy.mean(self.pricedata[-100:]) or self.currentPrice < trade.algoOpenPrice*(1- trade.TS) ):
                    trade.markedToClose = True
                    exitAll = True
            if(trade.sell == True):
                if(self.currentPrice< trade.BestPrice):
                    trade.BestPrice = self.currentPrice
                if(self.currentPrice > trade.SL or numpy.mean(self.pricedata[-30:]) >numpy.mean(self.pricedata[-100:]) or self.currentPrice > trade.algoOpenPrice*(1+trade.TS)):
                    trade.markedToClose = True
                    exitAll = True
        for trade in allTrades:
            if(exitAll == True or self.nextEvent<10):
                trade.markedToClose = True


class AlgoLogging:
    def __init__(self):
        self.AlgoOutput = open('ModelOutput.csv', 'a',newline='')
        self.ALog = csv.writer(self.AlgoOutput)
        self.ALog.writerow([datetime.datetime.now(datetime.timezone.utc),"Started running code"])
        self.ALog.writerow(['time','buycon','sellcon','bid','ask'])
        
    def closeLog(self):
        self.ALog.close()