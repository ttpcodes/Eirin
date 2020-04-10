from email.mime.text import MIMEText
from json import load
from smtplib import SMTP_SSL
from time import sleep

with open('config.json') as fp:
    config = load(fp)

with open('email.txt') as fp:
    template = fp.read()

smtp = SMTP_SSL('outgoing.mit.edu')
smtp.login(config['smtp']['username'], config['smtp']['password'])

# Select all people in the submissions table that aren't currently in the bot table (just the kerberos).
for i in results:
    msg = MIMEText(template.format(), 'html')
    msg['From'] = 'SIPB Discord <sipb-discord@mit.edu>'
    msg['Subject'] = 'CPW 2020 Discord Access'
    msg['To'] = '{}@mit.edu'.format(i[0])
    msg['CC'] = 'sipb-discord-noreply@mit.edu'
    smtp.sendmail('sipb-discord@mit.edu', ['{}@mit.edu'.format(i[0]), msg['CC']], msg.as_string())
    # Add kerberos to the bot table IF NOT EXISTS.
    # Set processed = True for all instances of the Kerberos in the submissions table.
    print('Processed kerberos {}. Waiting 5 seconds for cooldown.'.format(i[0]))
    sleep(5)
print('Kerberoi from the last hour have been processed.')
