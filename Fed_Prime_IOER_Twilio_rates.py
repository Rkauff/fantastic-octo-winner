# -*- coding: utf-8 -*-
"""
Created on Sat Aug 25 13:11:35 2018

@author: Ryan
"""

import datetime
import os
import json
from twilio.rest import Client
import requests
import bs4
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def lambda_handler(event, context):
    """Main Function in the Lambda"""

    client = Client(
        os.environ['TWILIO_ACCOUNT'],
        os.environ['TWILIO_TOKEN'],
    )

    now = datetime.datetime.now()
    now2 = now.strftime("%Y-%m-%d")

#Step 0: Determine the URLs to scrape the data from
    fed_string = 'https://apps.newyorkfed.org/markets/autorates/fed%20funds'
    prime_string = "https://fred.stlouisfed.org/series/DPRIME"
    ioer_string = 'https://fred.stlouisfed.org/series/IOER'


#Step 1: download a webpage with requests.get
    fed_url = requests.get(fed_string)
    prime_url = requests.get(prime_string)
    ioer_url = requests.get(ioer_string)


#Step 2: Pass only the text element of the page to a variable
    fed = bs4.BeautifulSoup(fed_url.text, 'html.parser')
    prime = bs4.BeautifulSoup(prime_url.text, 'html.parser')
    ioer = bs4.BeautifulSoup(ioer_url.text, 'html.parser')


#Step 3: Parse the page for the most recent rate, date, and the second most recent rate and date
    rate = fed.select('td.dirColTight.numData') #Fed data
    #date = fed.select('td.dirColLTight') #Fed data
    prime_rate = prime.select('td.series-obs.value') #Prime data from FRED
    ioer_rate = ioer.select('td.series-obs.value') #IOER data

    todays_ioer_rate = float(ioer_rate[0].getText()) #Current IOER Rate
    yest_ioer_rate = float(ioer_rate[1].getText()) #Yesterday's IOER Rate

    todays_fed_rate = float(rate[0].getText()) #Current Fed Rate
    yest_fed_rate = float(rate[6].getText()) #Yesterday's Fed Rate
    #todays_date = str(date[0].getText()) #Current Fed Date

    todays_prime_rate = float(prime_rate[0].getText()) #Current Prime Rate
    yest_prime_rate = float(prime_rate[1].getText()) #Yesterday's Prime Rate
    #todays_prime_date = prime_date[3].getText() #As of date

    def fed_rate_delta():
        """#function to determine if the fed rate changed day over day"""
        fed_delta = todays_fed_rate - yest_fed_rate
        fed_delta = round(fed_delta, 2)
        return fed_delta

    def fed_up_or_down():
        if todays_fed_rate - yest_fed_rate > 0:
            return str("increased by ")
        else:
            return str("fell by ")

    def prime_rate_delta():
        """function to determine if the prime rate changed day over day"""
        prime_delta = todays_prime_rate - yest_prime_rate
        prime_delta = round(prime_delta, 2)
        return prime_delta

    def prime_up_or_down():
        if todays_prime_rate - yest_prime_rate > 0:
            return str("increased by ")
        else:
            return str("fell by ")

    def ioer_rate_delta():
        """function to determine if the ioer rate changed day over day"""
        ioer_delta = todays_ioer_rate - yest_ioer_rate
        ioer_delta = round(ioer_delta, 2)
        return ioer_delta

    def ioer_up_or_down():
        if todays_ioer_rate - yest_ioer_rate > 0:
            return str("increased by ")
        else:
            return str("fell by ")

    def rate_choice():
        if todays_ioer_rate < todays_fed_rate:
            return str("Use the Fed Funds Rate. It's higher by " + \
                   str(abs(round(todays_ioer_rate - todays_fed_rate, 2))))
        else:
            return str("Use the IOER Rate. It's higher by " + \
                   str(abs(round(todays_fed_rate - todays_ioer_rate, 2))))

    def sendgrid_email():
        """function to use the Sendgrid email API. This replaced the Gmail
        code I originally wrote."""
        message = Mail(
            from_email="koontz2k4@gmail.com",
            to_emails=[os.environ['my_email'], os.environ['gjp3'],\
                os.environ['rk44'], os.environ['dr11'], os.environ['hst1']],
            subject='Fed Funds, Prime and IOER Rates as of ' + now2,
            html_content='<p>Good morning! ' '<br />' '<br />'\
            "The Fed Funds rate is: " + str(todays_fed_rate) + ". (Source: NY Fed)" + '<br />'\
            "The U.S. Prime rate is: " + str(todays_prime_rate) + ". (Source: FRED)" + '<br />'\
            "The IOER rate is: " + str(todays_ioer_rate) + ". (Source: FRED)" + '<br />' '<br />'\
            + str(rate_choice()) + '<br />' '<br />'\
            "-Ryan</p>")
        s_g = SendGridAPIClient(os.environ['SENDGRID_KEY'])
        s_g.send(message)

    num_to_text = os.environ['my_cell'], os.environ['riz_cell'], os.environ['greg_cell'], os.environ['harsh_cell']

    def send_ioer_text():
        """If the ioer rate changes, send a text message to riz, greg, harsh, and myself."""
        if not ioer_rate_delta() == 0:
            for number in num_to_text:
                client.messages.create(
                    to=number,
                    from_="+16305184064",
                    body="Heads up! The IOER Rate " + ioer_up_or_down() + str(ioer_rate_delta()) \
                    + ". The current IOER rate is " + str(todays_ioer_rate) \
                    + ". Please see " + ioer_string + " for details. ")


    def send_fed_text():
        """If the fed rate changes, send a text message to riz, greg, harsh, and myself."""
        if not fed_rate_delta() == 0:
            for number in num_to_text:
                client.messages.create(
                    to=number,
                    from_="+16305184064",
                    body="Heads up! The Fed Rate " + fed_up_or_down() \
                    + str(fed_rate_delta()) \
                    + ". The current Fed rate is " + str(todays_fed_rate) \
                    + ". Please see " + fed_string + " for details.")


    def send_prime_text():
        """If the prime rate changes, send a text message to riz, greg, harsh,and myself."""
        if not prime_rate_delta() == 0:
            for number in num_to_text:
                client.messages.create(
                    to=number,
                    from_="+16305184064",
                    body="Heads up! The Prime Rate " + prime_up_or_down() \
                    + str(prime_rate_delta()) \
                    + ". The current Prime rate is " + str(todays_prime_rate) \
                    + ". Please see " + prime_string + " for details.")

    sendgrid_email()
    send_ioer_text()
    send_fed_text()
    send_prime_text()

    #The API component:
    return {
        "body": json.dumps("Good morning! "\
            "The Fed Funds rate is: " + str(todays_fed_rate) + ". (Source: NY Fed) " +\
            "The U.S. Prime rate is: " + str(todays_prime_rate) + ". (Source: FRED) " +\
            "The IOER rate is: " + str(todays_ioer_rate) + ". (Source: FRED) " +\
            str(rate_choice()) + " -Ryan")
    }
