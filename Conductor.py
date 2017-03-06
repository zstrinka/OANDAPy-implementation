'''
Created on Mar 3, 2017
This project interacts with OANDA's v20 python library to place basic trades.
Has basic backtesting capability as well as some basic logging and error handling.
Sends emails for certain known issues, as well as unhandled exceptions.

BASIC FILES:
Algorithm.py contains a basic crossover Moving Average rule
Conductor.py is this main file
Data_Handling.py either accesses a specified .csv file (the included Feb6_2017.csv) or connects to the OANDA server
Events.csv identifies weekends and other no-trade times. This code is designed to treat each week independently
Feb6_2017.csv is historical data produced by choosing Data_Handling.numberOfMins < 5000 and running the code.
OANDA.py manages all the calls to the OANDA server.
Sample_Login.txt shows the correct format of the login file to connect to the v20 practice server. For a discussion on more appropriate ways to do this, see: https://www.reddit.com/r/algotrading/comments/5ucu73/how_should_i_store_my_broker_login_credentials/
Scheduler.py handles date and time management.
Trade_Handling.py either writes trades to a csv file or connects to the OANDA server.
Trades.py is the class file for trades.
Warnings.py sends emails using the specified account. For a discussion of how to save password information better, see: https://github.com/kootenpv/yagmail

OUTPUT FILES:
AccessibleEventLog.csv is a copy of EventLog.csv. If this is open during code operation, nothing bad happens. Only ouput file which is accessible during the run 
EventLog.csv is the main log for the code which keeps track of decisions as they are made and their consequences
ModelOutput.csv records the factors in the algorithms decision making.
TimePriceLog.csv bid-ask data saved as the code runs.
TradeLog.csv records the trades placed
Unhandled.log is written to if the code runs into an unhandled exception.

In order to use this code live, follow the format in the Sample_login.txt file to enter your credentials,
select liveData = True, enter the correct loginFileName, modify Warnings.py to have valid email addresses
and modify the Algorithm.py file extensively to a
(hopefully profitable) strategy. Current numbers are maybe reasonable for a JPY pair currency.

@author: Zohar
'''
loginFileName = "Sample_Login.txt"
#liveData = True # Uncomment if using your OANDA account.
liveData = False # Uncomment instead for basic backtesting
minutesToRun = 8000 #The code should be reset every weekend or set this number very large.

import OANDA
import Algorithm
import Data_Handling
import Trade_Handling
import Scheduler
from datetime import datetime
from datetime import timezone
import time
import logging
import Warnings


def main() :
    #Load in events first so we can make sure the server is open
    EventList = Scheduler.readEventsCSV('Events.csv')
    if(liveData == True):
        Scheduler.waitForOpen(EventList)
    
    #Allows us to know in the main file if there are trades open
    trades = []
    
    #Initialization
    if(liveData == True):
        #Start OANDA instance
        MinutesSinceOpen = Scheduler.minutesSinceEvent(Scheduler.getLastClosedEvent(EventList))
        print("Minutes since market opened are: ", MinutesSinceOpen)
        Trading = OANDA.Account(loginFileName, trades)
        trades = Trading.assessCurrentState()
        data = Data_Handling.InputData(liveData,Trading, SinceOpen = MinutesSinceOpen)
        margin = Trading.margin
        
        #Display if there were trades already opened, load them into the program's awareness
        print(Trading.previouslyOpenedTrades)
        
        ## Code I used to close all currently trades if I needed to reset things
        #openTrades = Trading.getOpenTrades()
        #for tradeIDNum in openTrades:
        #    Trading.closeTrade(None, tradeIDNum)
    else:
        # Initialize the things that still need to exist when just backtesting
        Trading = None
        data = Data_Handling.InputData(liveData,Trading)
        margin = 1000 # Use any number you like that allows your strategy to work
    tradeManagement = Trade_Handling.Trades(liveData,Trading)
    output = Algorithm.AlgoLogging()
    
    #### HERE IS THE EVENT LOOP ####
    for i in range(0,minutesToRun):
        Waiting = True # used to run the code once a minute
        while(Waiting):
            d = datetime.now(timezone.utc)
            time.sleep(.01)
            if(d.second < 2 or liveData == False):
                
                #Time for the once-a-minute run
                if(Scheduler.timeToMarketClose(EventList) < 2): # We closed everything 10 minutes before the weekend already
                    time.sleep(180) # Wait to make sure the market really will be closed
                    Scheduler.waitForOpen(EventList)
                    MinutesSinceOpen = Scheduler.minutesSinceEvent(Scheduler.getLastClosedEvent(EventList))
                    data = Data_Handling.InputData(liveData,Trading, SinceOpen = MinutesSinceOpen)
                Waiting = False
                data.getNextMinute()
                Algorithm.Model(data.dataForAlgorithm(), data.bidAsk(), trades, margin, Scheduler.timeToNextEvent(EventList),  output)
                tradeManagement.manageTrades(trades, data.bidAsk())
                
                i +=1
                if(liveData == True):
                    time.sleep(3)
                    Trading.saveCSVs() #Every minute we close and reopen the accessible event log
                if(d.minute == 30 and liveData== True):
                    Trading.accountInfo() #Updates current margin etc.
                


    #Cleanup when the code ends
    tradeManagement.closeCSVs(trades, data.bidAsk())
    output.closeLog    
    
    
if __name__ == '__main__':
    # Runs the above main file
    # Prints any unhandled exceptions to a log file
    logger = logging.getLogger('myapp')
    hdlr = logging.FileHandler('Unhandled.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr) 
    logger.setLevel(logging.DEBUG)
    try:
        main()
    except:
        logger.exception("Unhandled exception during main")
        Warnings.ProcessError('Code Stopped Running',True,0)