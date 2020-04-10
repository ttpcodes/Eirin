from flask import Flask, render_template
from flask_dance.contrib.discord import discord, make_discord_blueprint
from requests import get, put

from json import load
from os import getenv, popen
from shlex import quote

BASE_TEMPLATE = 'base.html'

app = Flask(__name__)

# Load entire configuration from config.json.
with open('config.json') as fp:
    config = load(fp)
    authorization = {'Authorization': 'Bot {}'.format(config['discord']['token'])}
    blueprint = make_discord_blueprint(config['discord']['id'], config['discord']['secret'],
                                       ['guilds.join', 'identify'], redirect_to='index')
    app.register_blueprint(blueprint)
    app.config.update(SECRET_KEY=config['flask']['secret'])


def get_ldap(kerb):
    f = popen('athrun consult ldaps ' + quote(kerb)).read().split('\n')
    res = {}
    for x in f:
        splt = x.split(' ')
        if len(splt) != 2: continue
        res[splt[0][:-1]] = splt[1]
    return res


@app.context_processor
def base():
    return {'base': config['flask']['base']}


@app.route('/')
def index():
    kerb = getenv('SSL_CLIENT_S_DN_Email').split('@')[0]
    # Check if kerb is in bot table. If it is, set user_id from there. If not, check submissions for kerb. If kerb
    # doesn't exist, we go to the error way at the bottom. If it does exist, create a new record in bot with kerb set.
    # Set user_id to None.
    if kerb in database:
        if discord.authorized:
            user = discord.get('/api/users/@me').json()
            if not user_id:
                # Update the database so that in the bot table, the kerb has user id (stored in user['id']).
                pass
            if user and user['id'] != user:
                return render_template(BASE_TEMPLATE, message=("Your current Discord account doesn't match what we "
                                                               'have on record. Please log into the account you used '
                                                               'previously. Please contact sipb-discord@mit.edu if '
                                                               'this is an error.')), 403
            ldap = get_ldap(kerb)
            roles = [config['discord']['verified'], config['discord']['roles'][ldap['eduPersonAffiliation']]]
            if ldap['eduPersonAffiliation'] == 'student':
                roles.append(config['discord']['roles'][ldap['mitDirStudentYear']])
            r = put('https://discordapp.com/api/guilds/{}/members/{}'.format(config['discord']['guild'], user['id']),
                    json={
                        'access_token': discord.access_token,
                        'roles': roles
                    }, headers=authorization)
            if r.status_code in [201, 204]:
                if r.status_code == 204:
                    for i in roles:
                        r = get('https://discordapp.com/api/guilds/{}/members/{}/roles/{}'
                                .format(config['discord']['guild'], user['id'], i), headers=authorization)
                        if r.status_code != 204:
                            return render_template(BASE_TEMPLATE, message=('There was an error granting you access to '
                                                                           'the Discord server. Please contact '
                                                                           '<a href="mailto:sipb-discord@mit.edu">'
                                                                           'sipb-discord@mit.edu</a> for assistance.')
                                                   ),500
                    return render_template(BASE_TEMPLATE, message=('You should now have access to the CPW 2020 Discord '
                                                                   'server! If you are having problems, please let us '
                                                                   'know.'))
            return render_template(BASE_TEMPLATE, message=('There was an error granting you access to the Discord '
                                                           'server. Please contact '
                                                           '<a href="mailto:sipb-discord@mit.edu">sipb-discord@mit.edu'
                                                           '</a> for assistance.')), 500
        return render_template(BASE_TEMPLATE, message=('You\'re one step away from accessing the CPW 2020 Discord '
                                                       'server! Please <a href="discord">click here</a> to '
                                                       'authenticate with Discord and verify your Discord account.'))
    return render_template(BASE_TEMPLATE, message=('You are not on the list of representatives for the CPW 2020 '
                                                   'Discord server. If this is an error, please contact the other '
                                                   'representatives of your student organization.')), 401
