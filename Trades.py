'''
Created on Jan 18, 2017

@author: Zohar
'''
buyTrade = False
sellTrade = False

class TradeInstance:
    def __init__(self, buyOrSell, price,lots, StopLoss, TrailingStop, scaling = False, tradeID = None):
        if(buyOrSell == 1):
            self.buy = True
            self.sell = False
        elif(buyOrSell == -1):
            self.buy = False
            self.sell = True
        self.opened = False
        self.TS = TrailingStop
        self.SL = StopLoss
        self.algoOpenPrice = price
        self.BestPrice = price
        self.tradeID = tradeID
        self.tradeLots = lots*buyOrSell
        self.markedToClose = False
        self.openTime = None