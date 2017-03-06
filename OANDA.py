
'''
Created on Jan 12, 2017

Called by Trade_Handling.py to initialize OANDA connection, pull price data, push trade orders,
verify trade orders, pull balance information, etc.


@author: Zohar
'''

import v20 #Needed to connect at all
import csv
import datetime
import time
import Warnings
import Trades
import sys
import shutil #Used to create "AccessibleEventLog"
import Scheduler
from v20.errors import V20ConnectionError, V20Timeout

class Account:
    def __init__(self, loginFileName, tradeList):
        self.emailsSent = 0
        self.attempts = 0
        self.TimePriceLogging = open('TimePriceLog.csv', 'a',newline='')
        self.TPLog = csv.writer(self.TimePriceLogging)
        self.EventLogging = open('EventLog.csv', 'a',newline='')
        self.ELog = csv.writer(self.EventLogging)
        self.ELog.writerow([datetime.datetime.now(datetime.timezone.utc),"Start" , "Started running code"])
        
        # reads in login.txt
        self.ELog.writerow([datetime.datetime.now(datetime.timezone.utc),"ReadCSV", "Reading login file"])
        try:
            with open(loginFileName, newline='') as csvfile:
                reader = csv.reader(csvfile)
                mydict = {rows[0]:rows[1] for rows in reader}
            self.acct_id = mydict['account_id']
            self.apiToken = mydict['apiToken']
            self.hostname = mydict['hostname']
            self.portname = mydict['portname']
            self.nickname = mydict['nickname']
        except:
            print("Error in login file, please fix! Code has terminated.")
            sys.exit()
                
        #Connects to server
        self.ELog.writerow([datetime.datetime.now(datetime.timezone.utc),"Connection", "Connecting to Server"])
        self.connectToServer()
        self.ELog.writerow([datetime.datetime.now(datetime.timezone.utc),"AccountCall", "Getting account information"])
        self.accountInfo()
        self.previouslyOpenedTrades = []
        
        #If there are open trades when the code is initialized, this loads them into awareness
        if(self.account.positionValue>1.0):
            self.ELog.writerow([datetime.datetime.now(datetime.timezone.utc),"Error", "There are already open positions"])
            response = self.api.account.get(self.acct_id)
            account = response.body['account']         
            for trade in account.trades:
                self.previouslyOpenedTrades.append(trade.id)
                self.ELog.writerow([datetime.datetime.now(datetime.timezone.utc),"OpenTrade", "Trade ID open is: ", trade.id])
        
    def connectToServer(self):
        while True: #Loops indefinitely because connecting to the server is critical to the code working
            try:
                self.api = v20.Context(
                    self.hostname,
                    self.portname,
                    token=self.apiToken)
                return
            except V20Timeout:
                self.timeoutError('Forex could not connect to the server')
            except V20ConnectionError:
                self.connectionError('Forex could not connect to the server')

    # Used to get account balance
    def accountInfo(self):
        while True:
            try:
                response = self.api.account.summary(self.acct_id)
                if(response.status > 250):
                    print(response.status)
                    self.statusError('Error getting account info')
                else:
                    self.account = response.body.get('account',200)
                    self.balance = self.account.balance
                    self.margin = self.account.marginAvailable
                    self.marginrate = self.account.marginRate
                    self.percentMargin = self.account.marginCallPercent
                    self.PandL = self.account.unrealizedPL
                    self.ELog.writerow([datetime.datetime.now(datetime.timezone.utc),"AccountInfo", " Current Balance: ", self.balance, " Current margin ", self.margin, "Unrealized PL ", self.PandL])
                    return response    
            except V20Timeout:
                self.timeoutError('Forex account could not connect')
            except V20ConnectionError:
                self.connectionError('Forex account could not connect') 
        
    def getMinuteData(self, numBars):
        #numBars = 5000 #Used to create backtesting data files
        result = []
        resultTime = []
        resultBid = []
        resultAsk = []
        while True:
            try:
                candlesticksBid = self.api.instrument.candles(
                    price = "B",
                    instrument='CAD_JPY',
                    granularity='M1',
                    count = numBars)
                candlesticksAsk = self.api.instrument.candles(
                    price = "A",
                    instrument='CAD_JPY',
                    granularity='M1',
                    count = numBars)
                for candle in candlesticksBid.get("candles",200):
                    resultTime.append(getattr(candle,"time",None))
                    tempbid = getattr(candle,"bid",None)
                    resultBid.append(tempbid.c)
                for candle in candlesticksAsk.get("candles",200):
                    tempask = getattr(candle,"ask",None)
                    resultAsk.append(tempask.c)
                for i in range(0,numBars):
                    self.TPLog.writerow([resultTime[i],resultBid[i],resultAsk[i]])
                    result.append([resultTime[i],resultBid[i],resultAsk[i]])   
                if(self.attempts>4):
                    Warnings.ProcessError('Error getting data', False, self.emailsSent)
                    self.attempts = 0
                elif(result == []): # Need to correct this one
                    self.attempts+=1
                    self.ELog.writerow([datetime.datetime.now(datetime.timezone.utc),"Error", "Error getting recent historical data"])
                else:
                    return result
            except V20Timeout:
                self.timeoutError('Forex could not get recent historical data')
            except V20ConnectionError:
                self.connectionError('Forex could not get recent historical data')
            # TODO If too many bars were asked for (>5000), produce a warning
    
    def saveCSVs(self):
        try:
            self.EventLogging.close()
            shutil.copy('EventLog.csv', 'AccessibleEventLog.csv') 
            self.EventLogging = open('EventLog.csv','a',newline='')
            self.ELog = csv.writer(self.EventLogging)
        except IOError:
            Warnings.ProcessError('Error when backing up EventLog', False, 7) #The "7" is because we don't need an email sent for this error
            
    def getBidAsk(self, lastMinuteData):
        while True:
            try:
                PricingFetched = self.api.pricing.get(
                    self.acct_id,
                    instruments='CAD_JPY',
                    includeUnitsAvailable=False)
                if(PricingFetched.status > 250):
                    print(PricingFetched.body)
                    self.statusError('Error getting bid-ask')
                else:
                    for price in PricingFetched.get("prices"):
                        #Checks if there was a gap in the data stream and fixes it if so
                        if(Scheduler.checkTimeDifference(price.time, lastMinuteData, 121)):
                            PriceBidAsk = [price.time, price.bids[0].price, price.asks[0].price]
                            self.TPLog.writerow(PriceBidAsk)
                            return(PriceBidAsk)
                        elif(Scheduler.isItMidnight(price.time)): #Around midnight, there are missing minutes
                            PriceBidAsk = [price.time, price.bids[0].price, price.asks[0].price]
                            self.ELog.writerow([datetime.datetime.now(datetime.timezone.utc),"Midnight"])
                            self.TPLog.writerow(PriceBidAsk)
                            return(PriceBidAsk)
                        else:
                            minutesBehind = Scheduler.returnTimeDifference(price.time,lastMinuteData)
                            self.ELog.writerow([datetime.datetime.now(datetime.timezone.utc),"Error", "We are ", minutesBehind, " behind."])
                            return self.getMinuteData(minutesBehind)
            except V20Timeout:
                self.timeoutError('Forex could not get bid-ask')
            except V20ConnectionError:
                self.connectionError('Forex could not get bid-ask')        
            
    # Used to open a trade
    def openTrade(self, trade):
        attempts = 0
        while(attempts < 5):
            try:
                attempts +=1
                stopLoss = {'price':str(round(trade.SL,2)),"type":"STOP_LOSS_ORDER"}
                self.ELog.writerow([ datetime.datetime.now(datetime.timezone.utc),"OpenTrade" ," Stoploss ", stopLoss])
                response = self.api.order.market(
                    self.acct_id,
                    instrument='CAD_JPY',
                    stopLossOnFill = stopLoss,
                    units=trade.tradeLots*100000)
                # Checks more thoroughly that it didn't go through because multiple opens would be worse than not opening at all
                if(response.status > 250):
                    print(response.body)
                    self.statusError('Forex could not place the trade')
                    print(response.status)
                    time.sleep(1)
                    mostRecentTrade = self.assessCurrentState()
                    if(len(mostRecentTrade)>.5 and Scheduler.checkTimeDifferenceParsed(mostRecentTrade[-1].openTime,datetime.datetime.now(datetime.timezone.utc),30)):
                        self.ELog.writerow([ datetime.datetime.now(datetime.timezone.utc),"Error" ," We suspect trade opened despite error message ", mostRecentTrade.tradeID])
                        Warnings.ProcessError('Fabled Trade opened but did not', False,0)
                        return True # Need to check our trades
                else:
                    temp = response.body['orderFillTransaction']
                    if(temp == None):
                        self.ELog.writerow([ datetime.datetime.now(datetime.timezone.utc),"Error" ,"OrderID not successfully found" ])
                        time.sleep(5) #Give it time to really go through
                        self.assessCurrentState()
                        break
                    trade.tradeID = temp.tradeOpened.tradeID
                    self.ELog.writerow([ datetime.datetime.now(datetime.timezone.utc),"OpenTrade" ," Opened trade ", trade.tradeID ," of ", trade.tradeLots*100000, " units at price ", trade.algoOpenPrice ])
                    self.setTrailingStop(trade)
                    self.accountInfo()
                    return
            except V20Timeout:
                self.timeoutError('Timeout while opening a trade')
                mostRecentTrade = self.assessCurrentState()
                if(len(mostRecentTrade)>.5 and Scheduler.minutesSinceEvent(mostRecentTrade[-1].openTime)<.5):
                    self.ELog.writerow([ datetime.datetime.now(datetime.timezone.utc),"Error" ," We suspect trade opened despite error message ", mostRecentTrade.tradeID])
                    Warnings.ProcessError('Fabled Trade opened but did not', False,0)
                    return True # Need to check our trades
            except V20ConnectionError:
                self.connectionError('Connection error while opening a trade')
                mostRecentTrade = self.assessCurrentState()
                if(len(mostRecentTrade)>.5 and Scheduler.minutesSinceEvent(mostRecentTrade[-1].openTime)<.5):
                    self.ELog.writerow([ datetime.datetime.now(datetime.timezone.utc),"Error" ," We suspect trade opened despite error message ", mostRecentTrade.tradeID])
                    Warnings.ProcessError('Fabled Trade opened but did not', False,0)
                    return True
        # Trade didn't open, give up for now since we tried several times and sent an email
        self.ELog.writerow([ datetime.datetime.now(datetime.timezone.utc),"Error" ," Trade not opened successfully"])
        trade = None
                
    def setStopLoss(self, trade):
        attempts = 0
        while attempts<5:
            attempts +=1
            try:
                response = self.api.order.stop_loss(
                    self.acct_id,
                    tradeID = trade.tradeID,
                    price = trade.SL)
                if(response.status>250):
                    print(response.body)
                    self.statusError('Forex could not set the stoploss')
                else:
                    self.ELog.writerow([ datetime.datetime.now(datetime.timezone.utc),"Stoploss" ," Set Stoploss successfully" ])
                    self.accountInfo()
                    return
            except V20Timeout:
                self.timeoutError('Timeout while setting the stoploss on a trade')
            except V20ConnectionError:
                self.connectionError('Timeout while setting the stoploss on a trade')
        # Trade couldn't set stoploss, Note, email, and move on since the trade had A stoploss from the start
        # and if the code keeps running, the algo will still send a close-trade message at most a minute late
        self.ELog.writerow([ datetime.datetime.now(datetime.timezone.utc),"Error" ," Stop loss not set successfully"])
        
    #Set Trailing Stop
    def setTrailingStop(self, trade):
        attempts = 0
        while attempts<5:
            attempts +=1
            try:
                response = self.api.order.trailing_stop_loss(
                    self.acct_id,
                    tradeID = trade.tradeID,
                    distance = str(round(trade.TS,2)))
                if(response.status>250):
                    print(response.body)
                    self.statusError('Forex could not set the Trailing Stop')
                else:
                    self.ELog.writerow([ datetime.datetime.now(datetime.timezone.utc),"TrailingStop" ," Set Trailing Stop successfully" ])
                    self.accountInfo()
                    return
            except V20Timeout:
                self.timeoutError('Timeout while setting the Trailing Stop on a trade')
            except V20ConnectionError:
                self.connectionError('Timeout while setting the Trailing Stop on a trade')
        # Trade couldn't set Trailing stop. This is not an emergency. Email sent since we had >4 errors to get to this point
        self.ELog.writerow([ datetime.datetime.now(datetime.timezone.utc),"Error" ," Trailing stop not set successfully"])
        
    
    # Used to close a specific trade
    def closeTrade(self, trade, tradeID = 0):
        if(tradeID==0):
            tradeID = trade.tradeID
        attempts = 0
        while attempts<5:
            attempts+=1
            try:
                response = self.api.trade.get(self.acct_id, tradeID)
                if(response.body['trade'].state=="CLOSED"): # Need to fix how I access this information
                    self.ELog.writerow([datetime.datetime.now(datetime.timezone.utc),"CloseTrade" ,"Trade ", tradeID ," was already closed"])
                    return
                response = self.api.trade.close(self.acct_id, tradeID)
                if(response.status>250):
                    print(response.body)
                    self.ELog.writerow([datetime.datetime.now(datetime.timezone.utc),"Error" , "Closing trade ", tradeID ," returned error ", response.status])
                    self.statusError('Forex could not close the trade')
                else:
                    self.ELog.writerow([ datetime.datetime.now(datetime.timezone.utc),"CloseTrade", " Closed trade ", tradeID])# , "of ", trade.tradeLots*100000, " units"])
                    self.accountInfo()
                    response = self.api.trade.get(self.acct_id, tradeID)
                    print(response.body['trade'])
                    return
            except V20Timeout:
                self.timeoutError('Forex could not get minute data')
            except V20ConnectionError:
                self.connectionError('Forex could not get minute data')
        #Couldn't close the trade, not an emergency because we should still have a stoploss and email was sent
        # Eventually this should mean we aren't allowed to place a new trade
        self.ELog.writerow([ datetime.datetime.now(datetime.timezone.utc),"Error" ," Trade not successfully closed"])
        
    def getOpenTrades(self):
        openTradeList = []
        attempts = 0
        while attempts<5:
            attempts+=1
            try:
                response = self.api.trade.list_open(self.acct_id)   
                if(response.status > 250):
                    self.ELog.writerow([datetime.datetime.now(datetime.timezone.utc),"Error", "Getting the open trade list returned error ", response.status])
                    self.statusError('Forex could not get the full open trade list')
                else:
                    for trade in response.get("trades"):
                        openTradeList.append(trade.id)
                    openTradeList.sort()
                    return(openTradeList)
            except V20Timeout:
                self.timeoutError('Forex account could not connect')
            except V20ConnectionError:
                self.connectionError('Forex account could not connect')
        # Not an emergency, but sent an email and recorded the issue
        self.ELog.writerow([ datetime.datetime.now(datetime.timezone.utc),"Error" ," Issue getting open trade list"])
        
        
    def assessCurrentState(self):
        openTrades = []
        attempts = 0
        while attempts <5:
            attempts+=1
            try:
                response = self.api.trade.list_open(self.acct_id)   
                if(response.status > 250):
                    self.ELog.writerow([datetime.datetime.now(datetime.timezone.utc),"Error", "Getting the open trade list returned error ", response.status])
                    self.statusError('Forex could not get the full open trade list')
                else:
                    ScaledIn = False
                    if(len(response.get("trades"))>1):
                        ScaledIn = True
                    for trade in response.get("trades"):
                        print(trade)
                        if(trade.currentUnits>0):
                            openTrades.append(Trades.TradeInstance(1, trade.price,trade.currentUnits/100000, trade.price-.2,100, ScaledIn,trade.id))
                            openTrades[-1].opened = True
                        else:
                            openTrades.append(Trades.TradeInstance(-1, trade.price,trade.currentUnits/100000*-1, trade.price+.2,100,ScaledIn,trade.id))
                            openTrades[-1].opened = True
                    return(openTrades)
            except V20Timeout:
                self.timeoutError('Forex account could not connect')
            except V20ConnectionError:
                self.connectionError('Forex account could not connect')
        # Not an emergency. Sent an email and move on for the moment.
        # Eventually this should mean we can't place a new trade
        self.ELog.writerow([ datetime.datetime.now(datetime.timezone.utc),"Error" ," Could not assess current state"])
        

    def closeCSVs(self):
        try:
            self.TimePriceLogging.close()
            self.ELog.writerow([datetime.datetime.now(datetime.timezone.utc),"End", "Code terminated as expected"])
            self.EventLogging.close()        
        except IOError:
            Warnings.ProcessError('Error when closing CSVs', False, 7) # "7" emails sent already because this is not a critical error
                    
                    
    def timeoutError(self, errorDescription):
        self.ELog.writerow([datetime.datetime.now(datetime.timezone.utc),"Error", "Timeout Error"])
        self.attempts +=1
        time.sleep(10)
        if(self.attempts >4):
            self.connectToServer()
        if(self.attempts >4):
            self.emailsSent+=1
            Warnings.ProcessError(errorDescription, False,self.emailsSent)
            self.attempts = 0
    def connectionError(self, errorDescription):
        self.ELog.writerow([datetime.datetime.now(datetime.timezone.utc),"Error", "Connection Error"])
        self.attempts +=1
        time.sleep(10)
        self.connectToServer()
        if(self.attempts >4):
            self.emailsSent+=1
            Warnings.ProcessError(errorDescription, False,self.emailsSent)  
            self.attempts = 0
    def statusError(self, errorDescription):
        self.ELog.writerow([datetime.datetime.now(datetime.timezone.utc),"Error", "Status Error", errorDescription])
        self.attempts +=1
        time.sleep(10)
        if(self.attempts >4):
            self.emailsSent+=1
            Warnings.ProcessError(errorDescription, False,self.emailsSent)
            self.attempts = 0