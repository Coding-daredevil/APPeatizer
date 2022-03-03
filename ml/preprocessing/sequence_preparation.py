from tqdm import tqdm
import os
from os import path 
from typing import Dict, Text
import numpy as np
import pandas as pd
import tensorflow as tf
import configparser
from ml.preprocessing.transform_site_data_to_dataset import create_dataframe_from_site_data

####################[Auxiliary Functions]####################

def find_deficit_percentage(goal, deficit):
    """Simple Deficit Percentage Calculation. Meant to be used in vectorization"""
    return round(100*deficit/goal,3) if goal!=0 else 101

def prepare_deficit_prediction_dataset_sndw(regdf, intdf):
    """Deficit Preparation for Dataset

        Args:
         regdf: The Regtest DataFrame containing Goals/Totals/Deficits/etc.
         intdf: The Intakes DataFrame containing Sequences of (Food)Names/Calories/Carbs/Prot/...

        Returns:
          The DataFrames with two new columns with this week's deficit and the next week's deficit. The latter is basically (next week) the Label in ML,
          while the first (current week) another sequence input showing deficit percentages (of each day) (e.g. "50.1, 20.5, 10.3, 0.5, -10.5").
    """
    regdf['WEEK_DEFICIT'] = np.vectorize(find_deficit_percentage)(regdf['MEAN_GOAL_CALS'], regdf['MEAN_DEFICIT_CALS'])
    intdf['WEEK_DEFICIT'] = regdf['WEEK_DEFICIT']
    regdf['NEXT_WEEK_DEFICIT'] = regdf['WEEK_DEFICIT'].shift(-1)
    intdf['NEXT_WEEK_DEFICIT'] = regdf['WEEK_DEFICIT'].shift(-1)
    regdf = regdf.iloc[::2].reset_index(drop=True)
    intdf = intdf.iloc[::2].reset_index(drop=True)
    return regdf, intdf

####################[Main Functions]####################

def prepare_sisnd(day_count=4, pass_day=0):
    """Sequencial Nutrition DataFrame Daily for Site Implementation

        Args:
         day_count: How many days will be taken to predict the next.
         pass_day: If days used will be passed

        Returns:
         Final DataFrame to be used in Machine Learning.
    """
    conf = configparser.ConfigParser()
    conf.read("_conf/config.conf")
    regtest = pd.read_pickle(conf['main_datasets']['reg'], compression='gzip')
    intakes = pd.read_pickle(conf['main_datasets']['int'], compression='gzip')
    ###[Limit User with X Logs]###
    while True:
        try:
            f1 = int(input('Please set minimum logs required to accept user rows: '))
            if f1 < 0: raise ValueError
            break
        except ValueError:
            print("Please input positive integer only or zero...")  
            continue
    f1 = regtest['LOGS']>=f1  
    regtest = regtest.loc[f1].reset_index(drop=True)
    intakes = intakes.loc[f1].reset_index(drop=True)
    print('Initial DataFrame Size: ', len(regtest))
    ###[Necessary Tweaks]###
    while True:
        try:
            f1 = int(input('[0, 1] Append Site Data?: '))
            if f1!=0 and f1!=1: raise ValueError
            break
        except ValueError:
            print("Please input either 0 or 1...")  
            continue
    if f1:
        int_add, reg_add = create_dataframe_from_site_data(case='days')
        regtest = regtest.append(reg_add).reset_index(drop=True)
        intakes = intakes.append(int_add).reset_index(drop=True)
    ########################
    regtest['DEFICIT_SCORE'] = np.vectorize(find_deficit_percentage)(regtest['GOAL_CALS'],regtest['DEFICIT_CALS'])
    intakes['DEFICIT_SCORE'] = regtest['DEFICIT_SCORE'].astype(str)
    print('Creating User Dictionaries and Limiting Contents to consequtive days (side-by-side):')
    UserIDict_regtest = {x : pd.DataFrame for x in intakes.USER_ID.unique()}
    UserIDict_intakes = {x : pd.DataFrame for x in intakes.USER_ID.unique()}
    UserIDict_regtest_final = {x : pd.DataFrame for x in intakes.USER_ID.unique()}
    UserIDict_intakes_final = {x : pd.DataFrame for x in intakes.USER_ID.unique()}
    regtest_cols = ['USER_ID', 'DATE', 'MEAN_TOTAL_CALS','MEAN_GOAL_CALS', 'MEAN_DEFICIT_CALS']
    intakes_cols = ['USER_ID', 'sequence_cals', 'sequence_carb', 'sequence_fat', 'sequence_prot', 'sequence_sod', 'sequence_sug', 'sequence_scr']
    for uid in tqdm(UserIDict_regtest.keys()):
        UserIDict_regtest[uid] = regtest.loc[regtest.USER_ID == uid].reset_index(drop=True)
        UserIDict_intakes[uid] = intakes.loc[intakes.USER_ID == uid].reset_index(drop=True)
        UserIDict_regtest_final[uid] = pd.DataFrame(columns=regtest_cols)
        UserIDict_intakes_final[uid] = pd.DataFrame(columns=intakes_cols)
        or_sz = len(UserIDict_regtest[uid])
        i, regtest_row_lst, intakes_row_lst = 0, [], []
        while ( i < or_sz-day_count-7 ):
            if (UserIDict_regtest[uid].DATE[i+day_count] - UserIDict_regtest[uid].DATE[i]) == 86400*(day_count):
                regtest_row_lst.append({
                    'USER_ID': UserIDict_regtest[uid].USER_ID[0],
                    'DATE': int(UserIDict_regtest[uid][i:i+day_count].DATE.mean()),
                    'MEAN_LOGS': UserIDict_regtest[uid][i:i+day_count].LOGS.mean(),
                    'MEAN_RAW_CAL_OCC': UserIDict_regtest[uid][i:i+day_count].RAW_CAL_OCC.mean(),
                    'MEAN_TOTAL_CALS': UserIDict_regtest[uid][i:i+day_count].TOTAL_CALS.mean(),
                    'MEAN_GOAL_CALS': UserIDict_regtest[uid][i:i+day_count].GOAL_CALS.mean(),
                    'MEAN_DEFICIT_CALS': UserIDict_regtest[uid][i:i+day_count].DEFICIT_CALS.mean(),
                    'DEFICIT_SCORE': UserIDict_regtest[uid].iloc[i+day_count]['DEFICIT_SCORE']
                })
                intakes_row_lst.append({
                    'USER_ID': UserIDict_regtest[uid].USER_ID[0],
                    'sequence_cals': np.concatenate(UserIDict_intakes[uid][i:i+day_count].reset_index(drop=True).sequence_cals).astype(float),
                    'sequence_carb': np.concatenate(UserIDict_intakes[uid][i:i+day_count].reset_index(drop=True).sequence_carb).astype(float),
                    'sequence_fat':  np.concatenate(UserIDict_intakes[uid][i:i+day_count].reset_index(drop=True).sequence_fat).astype(float),
                    'sequence_prot': np.concatenate(UserIDict_intakes[uid][i:i+day_count].reset_index(drop=True).sequence_prot).astype(float),
                    'sequence_sod':  np.concatenate(UserIDict_intakes[uid][i:i+day_count].reset_index(drop=True).sequence_sod).astype(float),
                    'sequence_sug':  np.concatenate(UserIDict_intakes[uid][i:i+day_count].reset_index(drop=True).sequence_sug).astype(float),
                    'sequence_scr': np.array(UserIDict_intakes[uid][i:i+day_count].DEFICIT_SCORE.add(' ').sum().rstrip().split(' ')).astype(float),
                    'DEFICIT_SCORE': UserIDict_regtest[uid].iloc[i+day_count]['DEFICIT_SCORE']
                })
                i= i+1 if pass_day==0 else i+day_count+1
            else:
                i+=1
        UserIDict_regtest_final[uid] = UserIDict_regtest_final[uid].append(regtest_row_lst)
        UserIDict_intakes_final[uid] = UserIDict_intakes_final[uid].append(intakes_row_lst)
    return pd.concat(UserIDict_regtest_final).reset_index(drop=True), pd.concat(UserIDict_intakes_final).reset_index(drop=True)
        
def prepare_sisndw(day_count=14, pass_day=0):
    """Sequencial Nutrition DataFrame Weekly for Site Implementation

        Args:
         day_count: How many days will be taken to predict the next week.
         pass_day: If days used will be passed

        Returns:
         Final DataFrame to be used in Machine Learning.
    """
    print('Loading and Preparing Data')
    conf = configparser.ConfigParser()
    conf.read("_conf/config.conf")
    regtest = pd.read_pickle(conf['main_datasets']['reg'], compression='gzip')
    intakes = pd.read_pickle(conf['main_datasets']['int'], compression='gzip')
    ###[Limit User with X Logs]###
    while True:
        try:
            f1 = int(input('Please set minimum logs required to accept user rows: '))
            if f1 < 0: raise ValueError
            break
        except ValueError:
            print("Please input positive integer only or zero...")  
            continue
    f1 = regtest['LOGS']>=f1  
    regtest = regtest.loc[f1].reset_index(drop=True)
    intakes = intakes.loc[f1].reset_index(drop=True)
    print('Initial DataFrame Size: ', len(regtest))
    ###[Necessary Tweaks]###
    while True:
        try:
            f1 = int(input('[0, 1] Append Site Data?: '))
            if f1!=0 and f1!=1: raise ValueError
            break
        except ValueError:
            print("Please input either 0 or 1...")  
            continue
    if f1:
        int_add, reg_add = create_dataframe_from_site_data(case='weeks')
        regtest = regtest.append(reg_add).reset_index(drop=True)
        intakes = intakes.append(int_add).reset_index(drop=True)
    ########################
    regtest['DEFICIT_SCORE'] = np.vectorize(find_deficit_percentage)(regtest['GOAL_CALS'],regtest['DEFICIT_CALS'])
    intakes['DEFICIT_SCORE'] = regtest['DEFICIT_SCORE'].astype(str)
    print('Creating User Dictionaries and Limiting Contents to only Full Weeks (side-by-side):')
    UserIDict_regtest = {x : pd.DataFrame for x in intakes.USER_ID.unique()}
    UserIDict_intakes = {x : pd.DataFrame for x in intakes.USER_ID.unique()}
    UserIDict_regtest_final = {x : pd.DataFrame for x in intakes.USER_ID.unique()}
    UserIDict_intakes_final = {x : pd.DataFrame for x in intakes.USER_ID.unique()}
    regtest_cols = ['USER_ID', 'DATE', 'MEAN_TOTAL_CALS','MEAN_GOAL_CALS', 'MEAN_DEFICIT_CALS']
    intakes_cols = ['USER_ID', 'sequence_cals', 'sequence_carb', 'sequence_fat', 'sequence_prot', 'sequence_sod', 'sequence_sug', 'sequence_scr']
    for uid in tqdm(UserIDict_regtest.keys()):
            UserIDict_regtest[uid] = regtest.loc[regtest.USER_ID == uid].reset_index(drop=True)
            UserIDict_intakes[uid] = intakes.loc[intakes.USER_ID == uid].reset_index(drop=True)
            UserIDict_regtest_final[uid] = pd.DataFrame(columns=regtest_cols)
            UserIDict_intakes_final[uid] = pd.DataFrame(columns=intakes_cols)
            or_sz = len(UserIDict_regtest[uid])
            i, regtest_row_lst, intakes_row_lst = 0, [], []
            while ( i < or_sz-day_count-7 ):
                if (UserIDict_regtest[uid].DATE[i+day_count+7] - UserIDict_regtest[uid].DATE[i]) == 86400*(day_count+7):
                    regtest_row_lst.append({
                        'USER_ID': UserIDict_regtest[uid].USER_ID[0],
                        'DATE': int(UserIDict_regtest[uid][i:i+day_count].DATE.mean()),
                        'MEAN_TOTAL_CALS': UserIDict_regtest[uid][i:i+day_count].TOTAL_CALS.mean(),
                        'MEAN_GOAL_CALS': UserIDict_regtest[uid][i:i+day_count].GOAL_CALS.mean(),
                        'MEAN_DEFICIT_CALS': UserIDict_regtest[uid][i:i+day_count].DEFICIT_CALS.mean()
                    })
                    regtest_row_lst.append({
                        'USER_ID': UserIDict_regtest[uid].USER_ID[0],
                        'DATE': int(UserIDict_regtest[uid][i+day_count:i+day_count+7].DATE.mean()),
                        'MEAN_TOTAL_CALS': UserIDict_regtest[uid][i+day_count:i+day_count+7].TOTAL_CALS.mean(),
                        'MEAN_GOAL_CALS': UserIDict_regtest[uid][i+day_count:i+day_count+7].GOAL_CALS.mean(),
                        'MEAN_DEFICIT_CALS': UserIDict_regtest[uid][i+day_count:i+day_count+7].DEFICIT_CALS.mean()
                    })
                    intakes_row_lst.append({
                        'USER_ID': UserIDict_regtest[uid].USER_ID[0],
                        'sequence_cals': np.concatenate(UserIDict_intakes[uid][i:i+day_count].reset_index(drop=True).sequence_cals).astype(float),
                        'sequence_carb': np.concatenate(UserIDict_intakes[uid][i:i+day_count].reset_index(drop=True).sequence_carb).astype(float),
                        'sequence_fat':  np.concatenate(UserIDict_intakes[uid][i:i+day_count].reset_index(drop=True).sequence_fat).astype(float),
                        'sequence_prot': np.concatenate(UserIDict_intakes[uid][i:i+day_count].reset_index(drop=True).sequence_prot).astype(float),
                        'sequence_sod':  np.concatenate(UserIDict_intakes[uid][i:i+day_count].reset_index(drop=True).sequence_sod).astype(float),
                        'sequence_sug':  np.concatenate(UserIDict_intakes[uid][i:i+day_count].reset_index(drop=True).sequence_sug).astype(float),
                        'sequence_scr': np.array(UserIDict_intakes[uid][i:i+day_count].DEFICIT_SCORE.add(' ').sum().rstrip().split(' ')).astype(float)
                    })
                    intakes_row_lst.append({
                        'USER_ID': UserIDict_regtest[uid].USER_ID[0],
                        'sequence_cals': np.concatenate(UserIDict_intakes[uid][i+day_count:i+day_count+7].reset_index(drop=True).sequence_cals).astype(float),
                        'sequence_carb': np.concatenate(UserIDict_intakes[uid][i+day_count:i+day_count+7].reset_index(drop=True).sequence_carb).astype(float),
                        'sequence_fat':  np.concatenate(UserIDict_intakes[uid][i+day_count:i+day_count+7].reset_index(drop=True).sequence_fat).astype(float),
                        'sequence_prot': np.concatenate(UserIDict_intakes[uid][i+day_count:i+day_count+7].reset_index(drop=True).sequence_prot).astype(float),
                        'sequence_sod':  np.concatenate(UserIDict_intakes[uid][i+day_count:i+day_count+7].reset_index(drop=True).sequence_sod).astype(float),
                        'sequence_sug':  np.concatenate(UserIDict_intakes[uid][i+day_count:i+day_count+7].reset_index(drop=True).sequence_sug).astype(float),
                        'sequence_scr': np.array(UserIDict_intakes[uid][i+day_count:i+day_count+7].DEFICIT_SCORE.add(' ').sum().rstrip().split(' ')).astype(float)
                    })
                    i= i+1 if pass_day==0 else i+day_count+1
                else:
                    i+=1
            UserIDict_regtest_final[uid] = UserIDict_regtest_final[uid].append(regtest_row_lst)
            UserIDict_intakes_final[uid] = UserIDict_intakes_final[uid].append(intakes_row_lst)
    return pd.concat(UserIDict_regtest_final).reset_index(drop=True), pd.concat(UserIDict_intakes_final).reset_index(drop=True)