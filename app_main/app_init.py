from flask import Flask, render_template, session, redirect, request, jsonify, json
from flask_mongoengine import MongoEngine
import pymongo
import sys
import pathlib
import pickle
import tensorflow as tf
sys.path.append(str(pathlib.Path().resolve()))
import configparser
    
def init_app():
    """Initialization 

        Returns:
         Configuration File, Application, Client and MongoDB
    """
    print('Loading Configuration File')
    conf = configparser.ConfigParser()
    conf.read("_conf/config.conf")
    print('Flask Initialization...')
    app = Flask(__name__)
    app.secret_key = conf['flask']['api_key']
    print('MongoDB integration')
    host, port, accounts = conf['mongodb']['host'], int(conf['mongodb']['port']), conf['mongodb']['dbname']
    client = pymongo.MongoClient(host, port)
    db = client.accounts
    app.config['MONGODB_SETTINGS'] = {
        'db': accounts,
        'host': host,
        'port': port
    }
    qb = MongoEngine()
    qb.init_app(app)
    return conf, app, client, db, qb

def init_ml_system(conf):
    """Initializes the Machine Learning System
        Args:
         conf: configuration file

        Returns:
         matching dictionaries, number of days/weeks selected during training, max array sequence and the two models.
    """
    print('Preparing Machine Learning...')
    with open(conf['ml_savepath']['dmd'], 'rb') as f:
            days_matching_dict = pickle.load(f)
    with open(conf['ml_savepath']['wmd'], 'rb') as f:
            week_matching_dict = pickle.load(f)
    with open(conf['ml_savepath']['dn'], 'rb') as f:
            num_days = pickle.load(f)
    with open(conf['ml_savepath']['dms'], 'rb') as f:
            maxseq_days = pickle.load(f)
    with open(conf['ml_savepath']['wms'], 'rb') as f:
            maxseq_weeks = pickle.load(f)
    with open(conf['ml_savepath']['wn'], 'rb') as f:
            num_weeks = pickle.load(f)
    days_model = tf.keras.models.load_model(conf['ml_savepath']['dm'])
    week_model = tf.keras.models.load_model(conf['ml_savepath']['wm'])
    return days_matching_dict, week_matching_dict, num_days, maxseq_days, maxseq_weeks, num_weeks, days_model, week_model