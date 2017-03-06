'''
Created on Jan 13, 2017

Keeps track of when the algo should be trading by accessing Events.csv

@author: Zohar and Alex
'''

import csv
import sys
from datetime import datetime
from datetime import timedelta
from datetime import timezone
import time
from dateutil import parser

class Event:
	def __init__(self, start, end, closed):
		self.start = start
		self.end = end
		self.closed = closed

#Checks if the difference between two datetimes is less than an arbitrary threshold
def checkTimeDifference(time1, time2, deltaSeconds):
	maxAllowableDiff = timedelta(seconds=deltaSeconds)
	diff = abs(parseDate(time1) - parseDate(time2))
	return diff <= maxAllowableDiff

#Checks if the difference between two datetimes is less than an arbitrary threshold when the dates are pre-parsed
def checkTimeDifferenceParsed(time1, time2, deltaSeconds):
	maxAllowableDiff = timedelta(seconds=deltaSeconds)
	diff = abs(time1 - time2)
	return diff <= maxAllowableDiff

#Is it midnight market time?
def isItMidnight(time1):
	temp = parseDate(time1)
	hourCondition = temp.hour>20.5 and temp.hour<22.5
	beforeCondition = temp.hour>20.5 and temp.minute>56
	afterCondition =  temp.hour<22.5 and temp.minute<4
	return hourCondition and (beforeCondition or afterCondition)

#Returns the number of minutes difference
def returnTimeDifference(time1, time2):
	diff = abs(parseDate(time1) - parseDate(time2))
	return diff.seconds//60


#Checks if the current time is between the start and end times of an event
def withinEvent(event):
	now = datetime.now(timezone.utc)
	return event.start < now and now < event.end

#Take a list of events, and returns a list of events that the current time is within
def withinEvents(events):
	within = []
	for event in events:
		if withinEvent(event):
			within.append(event)
	return within

#Take a list of events, and returns a list of events that the current time is within
def withinClosedEvent(events):
	within = []
	for event in events:
		if withinEvent(event) and event.closed == True:
			within.append(event)
	return within

#Waits until the markets open
def waitForOpen(events):
	while(withinClosedEvent(events) != []):
		print("Markets are closed!")
		time.sleep(60)
	if(minutesSinceEvent(getLastClosedEvent(events))<1.1):
		time.sleep(60) #To ensure there is at least one minute of data to load from the server.
		
def timeToMarketClose(events):
	return minutesUntilEvent(getNextClosedEvent(events))

def timeToNextEvent(events):
	return minutesUntilEvent(getNextEvent(events))


#Returns the number of minutes until an event, rounded down
def minutesUntilEvent(event):
	now = datetime.now(timezone.utc)
	diff = event.start - now
	seconds = diff.total_seconds()
	return seconds // 60

#Returns the number of minutes since an event, rounded down
def minutesSinceEvent(event):
	now = datetime.now(timezone.utc)
	diff = now - event.end
	seconds = diff.total_seconds()
	return int(seconds) // 60

#Returns the next event that has not already begun. Returns None if there is no such event.
def getNextEvent(events):
	now = datetime.now(timezone.utc)
	nextEvent = None
	for event in events:
		if now < event.start:
			if nextEvent is None or event.start - now < nextEvent.start - now:
				nextEvent = event
	return nextEvent

#Returns the next "closed" event that has not already begun. Returns None if there is no such event.
def getNextClosedEvent(events):
	now = datetime.now(timezone.utc)
	nextEvent = None
	for event in events:
		if event.closed == True and now < event.start:
			if nextEvent is None or event.start - now < nextEvent.start - now:
				nextEvent = event
	return nextEvent

#Returns the last "closed" event which may have already begun. Returns None if there is no such event.
def getLastClosedEvent(events):
	now = datetime.now(timezone.utc)
	lastEvent = None
	for event in events:
		if event.closed == True and now > event.start:
			if lastEvent is None or event.start - now > lastEvent.start - now:
				lastEvent = event
	return lastEvent

#This parses most datetime strings
def parseDate(datestring):
	return parser.parse(datestring)

#Loads in the events csv file
def readEventsCSV(filename):
	events = []
	try:
		with open(filename, newline='') as csvfile:
			reader = csv.reader(csvfile)
			next(reader, None) #skip first line
			for row in reader:
				start = parseDate(row[0])
				end = parseDate(row[1])
				closed = row[3].lower() == 'true'
				events.append(Event(start, end, closed))
		return events
	except:
		print("Couldn't read in event csv. Code Terminated")
		sys.exit()

##Some Basic testing:
#print(parseDate('2017-01-18T14:48:03.1234567Z'))
#print(readEventsCSV('Events.csv'))
#print(isItMidnight(datetime.now(timezone.utc)))
#print(isItMidnight(parseDate('2017-01-20T21:55:00.0000000Z')))
#print(checkTimeDifference('2017-01-18T14:48:03.1234567Z', '2017-01-20T21:55:00.0000000Z', 30))
