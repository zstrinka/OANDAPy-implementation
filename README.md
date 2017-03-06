# OANDAPy-implementation
This code provides a Python framework for algorithmic trading which can handle both event-driven backtesting and connect to OANDA's v20 server.

The current algorithm is based on moving averages, but is only provided as a sample to demonstrate the other portions of the code. This work is meant for educational purposes only, and any errors made using this work (financial or otherwise) are your own responsibility.


BASIC FILES:

Algorithm.py contains a basic crossover Moving Average rule

Conductor.py is the main file

Data_Handling.py either accesses a specified .csv file (like the included Feb6_2017.csv) or connects to the OANDA server

Events.csv identifies weekends and other no-trade times. This code is designed to treat each week independently

Feb6_2017.csv is historical data produced by choosing Data_Handling.numberOfMins <= 5000 and running the code.

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


In order to use this code live, follow the format in the Sample_login.txt file to enter your credentials, select liveData = True, enter the correct loginFileName, modify Warnings.py to have valid email addresses and modify the Algorithm.py file extensively to a (hopefully profitable) strategy. Current numbers are maybe reasonable for a JPY pair currency.
