#!/usr/bin/python3
from eirin import app

from json import load
from os import environ
from wsgiref.handlers import CGIHandler

with open('config.json') as fp:
    config = load(fp)
    environ['SCRIPT_NAME'] = config['flask']['root']
CGIHandler().run(app)
