from flask_mongoengine import MongoEngine
from bson.objectid import ObjectId
import pymongo
import pandas as pd
import datetime, time
import uuid
import sys
import pickle
import pathlib
import configparser
sys.path.append(str(pathlib.Path().resolve()))
from ml.preprocessing.sequence_preparation import prepare_sisndw

# MongoDB #
client = pymongo.MongoClient('localhost', 27017)
db = client.accounts
conf = configparser.ConfigParser()
conf.read("_conf/config.conf")

# Run #
while True:
  try:
    num_weeks = int(input('Please give number of weeks to take into consideration before predicting next: '))
    if num_weeks <= 0: raise ValueError 
    break
  except ValueError:
      print("Please input positive integer only...")  
      continue
save_path = conf['ml_savepath']['wsp']
df_regtest, df_intakes = prepare_sisndw(7*num_weeks)
with open(conf['ml_savepath']['wn'], 'wb') as handle:
        pickle.dump(num_weeks, handle, protocol=pickle.HIGHEST_PROTOCOL)
df_name = save_path+'w2w_df'
df_regtest.to_pickle(df_name+'_reg', compression='gzip')
df_intakes.to_pickle(df_name+'_int', compression='gzip')