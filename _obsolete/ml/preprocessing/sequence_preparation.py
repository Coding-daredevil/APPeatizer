from tqdm import tqdm
import os
from os import path 
from typing import Dict, Text
import numpy as np
import pandas as pd
import tensorflow as tf
import configparser
conf = configparser.ConfigParser()
conf.read("_conf/config.conf")

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

def prepare_snd(day_count=4, pass_day=0, log_threshold=1):
    """Sequencial Nutrition DataFrame Weekly for Site Implementation

        Args:
         day_count: How many days will be taken to predict the next.
         pass_day: If days used will be passed
         log_threshold: The Log threshold

        Returns:
         Final DataFrame to be used in Machine Learning.
    """
    print('Loading and Preparing Data')
    regtest = pd.read_pickle(conf['main_datasets']['reg'], compression='gzip')
    intakes = pd.read_pickle(conf['main_datasets']['int'], compression='gzip')
    ###[Limit User with X Logs]###
    f1 = regtest['LOGS']>=log_threshold  
    regtest = regtest.loc[f1].reset_index(drop=True)
    intakes = intakes.loc[f1].reset_index(drop=True)
    print('Initial DataFrame Size: ', len(regtest))
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
        while ( i < or_sz-day_count-1 ):
            if (UserIDict_regtest[uid].DATE[i+day_count] - UserIDict_regtest[uid].DATE[i]) == 86400*(day_count):
                regtest_row_lst.append({
                    'USER_ID': UserIDict_regtest[uid].USER_ID[0],
                    'DATE': int(UserIDict_regtest[uid][i:i+day_count].DATE.mean()),
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

def prepare_sndw(day_count=14, pass_day=0, log_threshold=1):
    """Sequencial Nutrition DataFrame Weekly

        Args:
         day_count: How many days will be taken to predict the next week.
         pass_day: If days used will be passed
         log_threshold: The Log threshold

        Returns:
         Final DataFrame to be used in Machine Learning.
    """    
    print('Loading and Preparing Data')
    regtest = pd.read_pickle(conf['main_datasets']['reg'], compression='gzip')
    intakes = pd.read_pickle(conf['main_datasets']['int'], compression='gzip')
    ###[Limit User with X Logs]###
    f1 = regtest['LOGS']>=log_threshold  
    regtest = regtest.loc[f1].reset_index(drop=True)
    intakes = intakes.loc[f1].reset_index(drop=True)
    print('Initial DataFrame Size: ', len(regtest))
    regtest['DEFICIT_SCORE'] = np.vectorize(find_deficit_percentage)(regtest['GOAL_CALS'],regtest['DEFICIT_CALS'])
    intakes['DEFICIT_SCORE'] = regtest['DEFICIT_SCORE'].astype(str)
    print('Creating User Dictionaries and Limiting Contents to only Full Weeks (side-by-side):')
    UserIDict_regtest = {x : pd.DataFrame for x in intakes.USER_ID.unique()}
    UserIDict_intakes = {x : pd.DataFrame for x in intakes.USER_ID.unique()}
    UserIDict_regtest_final = {x : pd.DataFrame for x in intakes.USER_ID.unique()}
    UserIDict_intakes_final = {x : pd.DataFrame for x in intakes.USER_ID.unique()}
    regtest_cols = ['USER_ID', 'DATE', 'MEAN_LOGS', 'MEAN_RAW_CAL_OCC', 'MEAN_TOTAL_CALS',
                    'MEAN_TOTAL_CARB', 'MEAN_TOTAL_FAT', 'MEAN_TOTAL_PROT',
                    'MEAN_TOTAL_SOD', 'MEAN_TOTAL_SUG', 'MEAN_GOAL_CALS', 'MEAN_GOAL_CARB',
                    'MEAN_GOAL_FAT', 'MEAN_GOAL_PROT', 'MEAN_GOAL_SOD', 'MEAN_GOAL_SUG',
                    'MEAN_DEFICIT_CALS', 'MEAN_DEFICIT_CARB', 'MEAN_DEFICIT_FAT',
                    'MEAN_DEFICIT_PROT', 'MEAN_DEFICIT_SOD', 'MEAN_DEFICIT_SUG',
                    'MEAN_DEFICIT_SCORE', 'SUM_DEFICIT_SCORE']
    intakes_cols = ['USER_ID', 'sequence_cals', 'sequence_carb', 'sequence_fat', 
                    'sequence_prot', 'sequence_sod', 'sequence_sug',
                    'sequence_scr']
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
                        'USER_ID': int(UserIDict_regtest[uid][i:i+day_count].USER_ID.mean()),
                        'DATE': int(UserIDict_regtest[uid][i:i+day_count].DATE.mean()),
                        'MEAN_LOGS': UserIDict_regtest[uid][i:i+day_count].LOGS.mean(),
                        'MEAN_RAW_CAL_OCC': UserIDict_regtest[uid][i:i+day_count].RAW_CAL_OCC.mean(),
                        'MEAN_TOTAL_CALS': UserIDict_regtest[uid][i:i+day_count].TOTAL_CALS.mean(),
                        'MEAN_TOTAL_CARB': UserIDict_regtest[uid][i:i+day_count].TOTAL_CARB.mean(),
                        'MEAN_TOTAL_FAT': UserIDict_regtest[uid][i:i+day_count].TOTAL_FAT.mean(),
                        'MEAN_TOTAL_PROT': UserIDict_regtest[uid][i:i+day_count].TOTAL_PROT.mean(),
                        'MEAN_TOTAL_SOD': UserIDict_regtest[uid][i:i+day_count].TOTAL_SOD.mean(),
                        'MEAN_TOTAL_SUG': UserIDict_regtest[uid][i:i+day_count].TOTAL_SUG.mean(),
                        'MEAN_GOAL_CALS': UserIDict_regtest[uid][i:i+day_count].GOAL_CALS.mean(),
                        'MEAN_GOAL_CARB': UserIDict_regtest[uid][i:i+day_count].GOAL_CARB.mean(),
                        'MEAN_GOAL_FAT': UserIDict_regtest[uid][i:i+day_count].GOAL_FAT.mean(),
                        'MEAN_GOAL_PROT': UserIDict_regtest[uid][i:i+day_count].GOAL_PROT.mean(),
                        'MEAN_GOAL_SOD': UserIDict_regtest[uid][i:i+day_count].GOAL_SOD.mean(),
                        'MEAN_GOAL_SUG': UserIDict_regtest[uid][i:i+day_count].GOAL_SUG.mean(),
                        'MEAN_DEFICIT_CALS': UserIDict_regtest[uid][i:i+day_count].DEFICIT_CALS.mean(),
                        'MEAN_DEFICIT_CARB': UserIDict_regtest[uid][i:i+day_count].DEFICIT_CARB.mean(),
                        'MEAN_DEFICIT_FAT': UserIDict_regtest[uid][i:i+day_count].DEFICIT_FAT.mean(),
                        'MEAN_DEFICIT_PROT': UserIDict_regtest[uid][i:i+day_count].DEFICIT_PROT.mean(),
                        'MEAN_DEFICIT_SOD': UserIDict_regtest[uid][i:i+day_count].DEFICIT_SOD.mean(),
                        'MEAN_DEFICIT_SUG': UserIDict_regtest[uid][i:i+day_count].DEFICIT_SUG.mean(),
                        'MEAN_DEFICIT_SCORE': UserIDict_regtest[uid][i:i+day_count].DEFICIT_SCORE.mean(),
                        'SUM_DEFICIT_SCORE': UserIDict_regtest[uid][i:i+day_count].DEFICIT_SCORE.sum(),
                    })
                    regtest_row_lst.append({
                        'USER_ID': int(UserIDict_regtest[uid][i+day_count:i+day_count+7].USER_ID.mean()),
                        'DATE': int(UserIDict_regtest[uid][i+day_count:i+day_count+7].DATE.mean()),
                        'MEAN_LOGS': UserIDict_regtest[uid][i+day_count:i+day_count+7].LOGS.mean(),
                        'MEAN_RAW_CAL_OCC': UserIDict_regtest[uid][i+day_count:i+day_count+7].RAW_CAL_OCC.mean(),
                        'MEAN_TOTAL_CALS': UserIDict_regtest[uid][i+day_count:i+day_count+7].TOTAL_CALS.mean(),
                        'MEAN_TOTAL_CARB': UserIDict_regtest[uid][i+day_count:i+day_count+7].TOTAL_CARB.mean(),
                        'MEAN_TOTAL_FAT': UserIDict_regtest[uid][i+day_count:i+day_count+7].TOTAL_FAT.mean(),
                        'MEAN_TOTAL_PROT': UserIDict_regtest[uid][i+day_count:i+day_count+7].TOTAL_PROT.mean(),
                        'MEAN_TOTAL_SOD': UserIDict_regtest[uid][i+day_count:i+day_count+7].TOTAL_SOD.mean(),
                        'MEAN_TOTAL_SUG': UserIDict_regtest[uid][i+day_count:i+day_count+7].TOTAL_SUG.mean(),
                        'MEAN_GOAL_CALS': UserIDict_regtest[uid][i+day_count:i+day_count+7].GOAL_CALS.mean(),
                        'MEAN_GOAL_CARB': UserIDict_regtest[uid][i+day_count:i+day_count+7].GOAL_CARB.mean(),
                        'MEAN_GOAL_FAT': UserIDict_regtest[uid][i+day_count:i+day_count+7].GOAL_FAT.mean(),
                        'MEAN_GOAL_PROT': UserIDict_regtest[uid][i+day_count:i+day_count+7].GOAL_PROT.mean(),
                        'MEAN_GOAL_SOD': UserIDict_regtest[uid][i+day_count:i+day_count+7].GOAL_SOD.mean(),
                        'MEAN_GOAL_SUG': UserIDict_regtest[uid][i+day_count:i+day_count+7].GOAL_SUG.mean(),
                        'MEAN_DEFICIT_CALS': UserIDict_regtest[uid][i+day_count:i+day_count+7].DEFICIT_CALS.mean(),
                        'MEAN_DEFICIT_CARB': UserIDict_regtest[uid][i+day_count:i+day_count+7].DEFICIT_CARB.mean(),
                        'MEAN_DEFICIT_FAT': UserIDict_regtest[uid][i+day_count:i+day_count+7].DEFICIT_FAT.mean(),
                        'MEAN_DEFICIT_PROT': UserIDict_regtest[uid][i+day_count:i+day_count+7].DEFICIT_PROT.mean(),
                        'MEAN_DEFICIT_SOD': UserIDict_regtest[uid][i+day_count:i+day_count+7].DEFICIT_SOD.mean(),
                        'MEAN_DEFICIT_SUG': UserIDict_regtest[uid][i+day_count:i+day_count+7].DEFICIT_SUG.mean(),
                        'MEAN_DEFICIT_SCORE': UserIDict_regtest[uid][i+day_count:i+day_count+7].DEFICIT_SCORE.mean(),
                        'SUM_DEFICIT_SCORE': UserIDict_regtest[uid][i+day_count:i+day_count+7].DEFICIT_SCORE.sum(),
                    })
                    intakes_row_lst.append({
                        'USER_ID': int(UserIDict_intakes[uid][i:i+day_count].USER_ID.mean()),
                        'sequence_cals': np.concatenate(UserIDict_intakes[uid][i:i+day_count].reset_index(drop=True).sequence_cals).astype(float),
                        'sequence_carb': np.concatenate(UserIDict_intakes[uid][i:i+day_count].reset_index(drop=True).sequence_carb).astype(float),
                        'sequence_fat':  np.concatenate(UserIDict_intakes[uid][i:i+day_count].reset_index(drop=True).sequence_fat).astype(float),
                        'sequence_prot': np.concatenate(UserIDict_intakes[uid][i:i+day_count].reset_index(drop=True).sequence_prot).astype(float),
                        'sequence_sod':  np.concatenate(UserIDict_intakes[uid][i:i+day_count].reset_index(drop=True).sequence_sod).astype(float),
                        'sequence_sug':  np.concatenate(UserIDict_intakes[uid][i:i+day_count].reset_index(drop=True).sequence_sug).astype(float),
                        'sequence_scr': np.array(UserIDict_intakes[uid][i:i+day_count].DEFICIT_SCORE.add(' ').sum().rstrip().split(' ')).astype(float)
                    })
                    intakes_row_lst.append({
                        'USER_ID': int(UserIDict_intakes[uid][i+day_count:i+day_count+7].USER_ID.mean()),
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