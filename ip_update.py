#!/usr/bin/env python3

# IP CHECKER
# Checks saved WAN IP against the current IP
# (ideally every 30 mins via a cron job) and 
# emails new IP to email address of your choice
from __future__ import print_function
from datetime import datetime
import logging
import os
from smtplib import SMTP_SSL
import sh # install with pip
import requests # install with pip


import pprint
import tunet

## CHANGE ME! (set network login prefs)
username = 'username'
password = 'password'

## CHANGE ME! (set email prefs)
sender_address = "" # email address you're sending from
receiver_address = "" # email address you're sending to
sender_server = "" # your email server (for sending)
sender_port = "" # SSL email port for sending (usually 465)
sender_username = "" # email account username (for sending)
sender_password = "" # email account password (for sending)

# sets up log file to track saved_ip between reboots
def setup_log_dir():
    homedir = os.path.expanduser('~')
    saved_ip_f = homedir + "/.ip_update/saved_ip"
    if not os.path.exists(saved_ip_f):
        sh.mkdir(homedir+"/.ip_update")
        sh.touch(saved_ip_f)
    return saved_ip_f

# generates a nice looking date/time stamp for emails
def get_date():
    week = {0:'Mon', 1:'Tue', 2:'Weds', 3:'Thur', 4:'Fri', 5:'Sat', 6:'Sun'}
    weekday = week[datetime.today().weekday()]
    return(datetime.now().strftime("%H:%M on {} %d/%m/%y").format(weekday))



# checks retrieved address against last known address
def check_ip():
    saved_ip_file = open(f, "r")
    saved_ip = saved_ip_file.read().strip()
    saved_ip_file.close()
    try:
        #current_ip = requests.get("http://icanhazip.com").text.strip()
        if not tunet.auth4.checklogin():
            # have to login first
            tunet.net.login(username, password)
        login_info = tunet.net.checklogin()
        current_ip = login_info["ipv4_address"]
    except Exception as e:
        logging.exception("Couldn't get IP address. Check your connection")
        return (0, 0)
    else:
        if saved_ip != current_ip:
            return (saved_ip, current_ip)
        return (0, 0)
    
# alerts you of change, providing the old and new addresses
def send_email_update(old_ip, new_ip):
    hostname = str(sh.hostname('-s')).strip()
    date_time = get_date()
    HOST = "{}:{}".format(sender_server, int(sender_port))    
    TO = "To: {}".format(receiver_address)
    FROM = "From: {}".format(sender_address)
    SUBJECT = "Subject: {}'s WAN IP has changed!".format(hostname)
    msg = "{}\n\n{}'s WAN IP has changed from {} to {}".format(date_time, hostname, old_ip, new_ip)
    BODY = "{}\n{}\n{}\n\n{}".format(TO,FROM,SUBJECT,msg)    
    username = "{}".format(sender_username)
    password = "{}".format(sender_password)

    server = SMTP_SSL(HOST)
    server.login(username, password)
    server.sendmail(FROM, TO, BODY)
    server.quit()
    
# updates the stored address with the new address
def update_local_file(new_ip, f):
    with open(f, "w") as saved_ip_file:
        saved_ip_file.write("{}\n".format(new_ip))
        

if __name__ == '__main__':
    f = setup_log_dir()
    old_ip, new_ip = check_ip()
    if new_ip != 0:
        try:
            send_email_update(old_ip, new_ip)
        except Exception as e:
            logging.exception("Failed to send email. Check your settings/connection.")
        else:
            update_local_file(new_ip, f)
