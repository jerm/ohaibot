#!/usr/bin/env python
import ConfigParser
import boto.sqs
import json
import logging
import re

from boto.sqs.message import Message
from flask import Flask
from flask import request

formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "progname":' +
            ' "%(name)s", "loglevel": "%(levelname)s", "message":, "%(message)s"}')
log = logging.getLogger(__file__)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
log.addHandler(handler)
log.setLevel(logging.DEBUG)

app = Flask(__name__)
Config = ConfigParser.ConfigParser()
Config.read("api.ini")

class conf():
    token = {
                'ohai': Config.get("api","slack_token_ohai"),
                'bye': Config.get("api","slack_token_bye")
            }
    tobot_queue_name = Config.get("api","tobot_queue_name")
    frombot_queue_name = Config.get("api","frombot_queue_name")
    video_url = Config.get("api","conference_url")
    users = re.sub('\s+',' ', Config.get("api","valid_users").replace(',',' ')).split(' ')
    teams = re.sub('\s+',' ', Config.get("api","valid_teams").replace(',',' ')).split(' ')


def ohaibot(request):
    conn = boto.sqs.connect_to_region(Config.get("api","aws_region"),
                aws_access_key_id=Config.get("api","aws_key"),
                aws_secret_access_key=Config.get("api","aws_secret"))

    tobotq = conn.get_queue(conf.tobot_queue_name)
    frombotq = conn.get_queue(conf.frombot_queue_name)
    command = request.form['text']
    token = request.form['token']
    team = request.form['team_domain']
    user = request.form['user_name']
    command = request.form['command'].replace('/','')
    log.debug(request.form)
    if str(token) != str(conf.token[command]):
        log.debug(token)
        return "Nope nope nope", 403
    if user not in conf.users:  
        log.debug(user)
        return "Nope nope nope", 405
    if team not in conf.teams:  
        log.debug(team)
        return "Nope nope nope", 406
    msg = Message()
    msg.set_body('{}:{}'.format(command, user))
    tobotq.write(msg)
    msg = frombotq.read(wait_time_seconds=2)
    if msg:
        if msg._body == "such face":
            return "Ohai!! Meet here! {}".format(conf.video_url)
        elif msg._body == 'much lonely':
            return "Very sadness, {} not at their desk found!".format(command)
        elif msg._body == 'newfacewhodis':
            return "Imposter alert!".format(command)
        elif msg._body == 'kthxbai':
            return "buh bye!"
        else:
            return "OhaiBot Says: {}".format(msg._body)
    else:
        return "So silence. Very luck."


@app.route("/ohai", methods=['POST'])
def ohai(action=None):
    return ohaibot(request) 


@app.route("/bye", methods=['POST'])
def bye():
    return ohaibot(request) 

    
if __name__ == '__main__':
    print(conf.teams, conf.users)
    app.run()
