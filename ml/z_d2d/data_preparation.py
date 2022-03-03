from flask_mongoengine import MongoEngine
from bson.objectid import ObjectId
import pymongo
import pandas as pd
import datetime, time
import uuid
import pickle
import sys
import pathlib
import configparser
sys.path.append(str(pathlib.Path().resolve()))
from ml.preprocessing.sequence_preparation import prepare_sisnd

# MongoDB #
client = pymongo.MongoClient('localhost', 27017)
db = client.accounts
conf = configparser.ConfigParser()
conf.read("_conf/config.conf")

# Run #
while True:
  try:
    num_days = int(input('Please give number of days to take into consideration before predicting next: '))
    if num_days <= 0: raise ValueError 
    break
  except ValueError:
      print("Please input positive integer only...")  
      continue
save_path = conf['ml_savepath']['dsp']
df_regtest, df_intakes = prepare_sisnd(num_days,0)
with open(conf['ml_savepath']['dn'], 'wb') as handle:
        pickle.dump(num_days, handle, protocol=pickle.HIGHEST_PROTOCOL)
df_name = save_path+'d2d_df'
df_regtest.to_pickle(df_name+'_reg', compression='gzip')
df_intakes.to_pickle(df_name+'_int', compression='gzip')



