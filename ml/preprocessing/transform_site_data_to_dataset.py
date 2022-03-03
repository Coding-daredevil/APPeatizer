from flask_mongoengine import MongoEngine
from bson.objectid import ObjectId
import pymongo
import numpy as np
import pandas as pd
import datetime, time
import uuid
import pickle
import configparser

# MongoDB #
client = pymongo.MongoClient('localhost', 27017)
db = client.accounts
conf = configparser.ConfigParser()
conf.read("_conf/config.conf")

def return_collection_names(db):
    """Return Collection Names

        Args:
         db: the database initialized on client.accounts

        Returns:
         All the possible collections created by users (leaving out user_info, users, userbooks).
    """
    col_names = db.list_collection_names()
    col_names.remove('user_info')
    col_names.remove('users')
    col_names.remove('userbooks')
    return col_names

def filter_collections_with_bio(db):
    """Filter Connection with Bio

        Args:
         db: the database initialized on client.accounts

        Returns:
         All the possible collections that their users registered their weight.
    """
    col_names, final = return_collection_names(db), []
    for mail in col_names:
        for res in db['user_info'].find({'email': mail}):
            if res['personal_info']['weight'] != 'Unset':
                final.append(mail)
    return final

def calculate_mean_calorie_intake(mail):
    """Calculation of Mean Calorie Intakes

        Args:
         mail: the mail of the user to retrieve his bio from database (collection name = email address)

        Returns:
         Application of Harris-Benedict formula for BMR with a set goal of 70% (for weight loss).
    """
    #Harris-Benedict formula#
    for res in db['user_info'].find({'email': mail}):
        pi = res['personal_info']
    if pi['sex'] == 'Male':
        bmr = 66.47 + (13.75 * float(pi['weight'])) + (5.003 * float(pi['height'])) - (6.755 * int(pi['age']))
    else:
        bmr = 655.1 + (9.563 * float(pi['weight'])) + (1.850 * float(pi['height'])) - (4.676 * int(pi['age']))
    return round(bmr*0.7)

def create_matching_dictionary(col_names, case):
    """Create DataFrame from Site Data

        Args:
         col_names: the collection names retrieved by filter_collections_with_bio.

        Returns:
         Creates a dictionary with keys the above collection names and assigns each email a unique integer as id, starting from 10.001 (dataset has 9.9k users).
         Saves the dictionary (depending on case) and returns it.
    """
    dct, start = dict.fromkeys(col_names), 10001
    for mail in dct:
        dct[mail] = start
        start += 1
    if case=='days':
        with open(conf['ml_savepath']['dmd'], 'wb') as handle:
            pickle.dump(dct, handle, protocol=pickle.HIGHEST_PROTOCOL)
    else:
        with open(conf['ml_savepath']['wmd'], 'wb') as handle:
            pickle.dump(dct, handle, protocol=pickle.HIGHEST_PROTOCOL)
    return dct

def create_dataframe_from_site_data(case='days'):
    """Create DataFrame from Site Data

        Returns:
         Regtest and Intakes DataFrames similar to the ones created from the original dataset, which will be directly appended to them. This is basically 
         where we transform site data to a dataset. We take all valid collections (with bio), then create sequences and GOALS/TOTALS which we append to the 
         respective lists. Return as DataFrames.
    """
    eating_periods = ['breakfast', 'brunch', 'lunch', 'snack', 'dinner']
    col_names = filter_collections_with_bio(db)
    matching_dict = create_matching_dictionary(col_names, case)
    list_dict_of_new_rows = []
    list_dict_of_total_and_goal_cals = []
    for col_name in col_names:
        for res in db[col_name].find():
            if any(consumption in res for consumption in eating_periods):          ### If there has been any eating, then proceed
                sequence_name = np.empty(0, dtype=object)
                sequence_cals = sequence_carb = sequence_fat = sequence_prot = sequence_sod = sequence_sug = np.empty(0, dtype=float)
                total_day_cals = 0
                intersection = [x for x in eating_periods if x in res.keys()]
                for eating_period in intersection:
                    for log in res[eating_period]:
                        sequence_name = np.append(sequence_name, res[eating_period][log]['name'])
                        sequence_cals = np.append(sequence_cals, round(float(res[eating_period][log]['ENERC_KCAL']['quantity'])))
                        total_day_cals += round(res[eating_period][log]['ENERC_KCAL']['quantity'],3)
                        sequence_carb = np.append(sequence_carb, round(float(res[eating_period][log]['CHOCDF']['quantity'])))
                        sequence_fat  = np.append(sequence_fat, round(float(res[eating_period][log]['FAT']['quantity'])))
                        sequence_prot = np.append(sequence_prot, round(float(res[eating_period][log]['PROCNT']['quantity'])))
                        sequence_sod  = np.append(sequence_sod, round(float(res[eating_period][log]['NA']['quantity'])))
                        sequence_sug  = np.append(sequence_sug, round(float(res[eating_period][log]['SUGAR']['quantity']))) if 'SUGAR' in res[eating_period][log].keys() else np.append(sequence_sug, 0)
                new_row = {
                    'USER_ID': matching_dict[col_name],
                    'sequence_name': sequence_name,
                    'sequence_cals': sequence_cals,
                    'sequence_carb': sequence_carb,
                    'sequence_fat': sequence_fat,
                    'sequence_prot': sequence_prot,
                    'sequence_sod': sequence_sod,
                    'sequence_sug': sequence_sug
                }
                new_row_cals = {
                    'USER_ID': matching_dict[col_name],
                    'DATE': int(datetime.datetime.combine(res['date'].date(), datetime.time()).timestamp()),
                    'TOTAL_CALS': total_day_cals,
                    'GOAL_CALS': calculate_mean_calorie_intake(col_name),
                    'DEFICIT_CALS': calculate_mean_calorie_intake(col_name) - total_day_cals
                }
                list_dict_of_new_rows.append(new_row)
                list_dict_of_total_and_goal_cals.append(new_row_cals)
    return pd.DataFrame(list_dict_of_new_rows), pd.DataFrame(list_dict_of_total_and_goal_cals)