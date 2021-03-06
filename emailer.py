from email.mime.text import MIMEText
from json import load
from smtplib import SMTP_SSL
from time import sleep

from mysql.connector import connect, Error
from mysql.connector.errorcode import ER_ACCESS_DENIED_ERROR, ER_BAD_DB_ERROR

submissions = 'testsubmissions'

with open('config.json') as fp:
    config = load(fp)

with open('email.html') as fp:
    template = fp.read()

smtp = SMTP_SSL('outgoing.mit.edu')
smtp.login(config['smtp']['username'], config['smtp']['password'])

# Select all people in the submissions table that aren't currently in the bot table (just the kerberos).
try:
    connection = connect(
        user=config['database']['username'],
        password=config['database']['password'],
        host=config['database']['host'],
        database=config['database']['database'])
except Error as err:
    if err.errno == ER_ACCESS_DENIED_ERROR:
        raise Exception('Could not connect to the database. Check your username or password.')
    elif err.errno == ER_BAD_DB_ERROR:
        raise Exception("Database does not exist.")
    else:
        raise err

cursor = connection.cursor()
cursor.execute("SELECT "+submissions+".kerberos FROM "+submissions+
               " WHERE NOT EXISTS(SELECT NULL FROM bot WHERE bot.kerberos = "+submissions+".kerberos)"
               " AND "+submissions+".processed = 0")
rows = cursor.fetchall()
intermediate = [row[0] for row in rows]
results = set(intermediate)

for i in results:
    msg = MIMEText(template.format(i), 'html')
    msg['From'] = 'SIPB Discord <sipb-discord@mit.edu>'
    msg['Subject'] = 'CPW 2020 Discord Access'
    msg['To'] = '{}@mit.edu'.format(i)
    msg['CC'] = 'sipb-discord-noreply@mit.edu'
    smtp.sendmail('sipb-discord@mit.edu', ['{}@mit.edu'.format(i[0]), msg['CC']], msg.as_string())
    # Add kerberos to the bot table IF NOT EXISTS.
    # Set processed = True for all instances of the Kerberos in the submissions table.
    cursor.execute("UPDATE "+submissions+" SET processed = 1 WHERE kerberos = %s", (i,))
    cursor.execute("INSERT INTO bot (kerberos) VALUES (%s)", (i,))
    connection.commit()
    print('Processed kerberos {}. Waiting 5 seconds for cooldown.'.format(i))
    connection.close()
    sleep(5)
    try:
        connection = connect(
            user=config['database']['username'],
            password=config['database']['password'],
            host=config['database']['host'],
            database=config['database']['database'])
    except Error as err:
        if err.errno == ER_ACCESS_DENIED_ERROR:
            raise Exception('Could not connect to the database. Check your username or password.')
        elif err.errno == ER_BAD_DB_ERROR:
            raise Exception("Database does not exist.")
        else:
            raise err

    cursor = connection.cursor()
connection.close()
print('Kerberoi from the last hour have been processed.')
