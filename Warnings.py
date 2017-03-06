'''
Created on Jan 13, 2017

Check for any of the many things that can go wrong and can:
    Sends emails / texts
    Discontinue placing new trades
    Terminate existing trades

How to check if OANDA itself is down: http://developer.oanda.com/rest-live-v20/troubleshooting-errors/


@author: Zohar
'''
# Import smtplib for the actual sending function
import smtplib
import sys
#from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

class ProcessError:
    def __init__(self,errorName, terminateAlgo, emailsSent):
        self.errorDescription = errorName
        if(emailsSent < 3):
            try:
                self.sendEmail()
            except:
                print("Couldn't send email! Code Terminated anyway? ", terminateAlgo)
        else:
            print("Too many emails sent, but there was an error called")
            
        if(terminateAlgo == True):
            self.gracefullExit()

    def sendEmail(self):
        msg = MIMEMultipart()
        msg['Subject'] = self.errorDescription

#        body = "I will add to this later... But for now, just read the subject"
        #msg.attach(MIMEImage(body, 'plain'))
     
        server = smtplib.SMTP('smtp-mail.outlook.com',587)
        server.starttls()
        server.login("FakeFromEmail@fake.com", "MyPasswordHasLotsOfEntropy")
     
        text = msg.as_string()
        server.sendmail("FakeFromEmail@fake.com", "FakeToEmail@gmail.com", text)
        server.quit()

    def closeAllOpenTrades(self):
        print("Here we would have the algo close all open trades if need be") #TODO
    
    def stopOpeningNewTrades(self):
        print("Here we would tell the algo not to open any new trades if need be.") # TODO
    def gracefullExit(self):
        sys.exit()