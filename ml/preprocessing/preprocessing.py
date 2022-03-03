import pandas as pd
import numpy as np
from tqdm import tqdm
import json
import configparser

def split_day_final(case, txt):
    """Simple split function meant to be used in vectorization to minimize execution time"""
    if case=='total':return json.loads(txt)['total']
    elif case=='goal':return json.loads(txt)['goal']

def split_intakes(case, txt):
    """Simple split function meant to be used in vectorization to minimize execution time"""
    if case=='meal_name':return json.loads(txt)[0]['meal']
    elif case=='dishes':return json.loads(txt)[0]['dishes']

def food_intakes_count(lst):
    """Simple len function meant to be used in vectorization to minimize execution time"""
    return len(lst)

def quickly_added_calories_occurences(lst):
    """Simple count function that returns number of 'raw calorie occurences'. Meant to be used in vectorization to minimize execution time"""
    sbstr ='Quick Added Calories'
    sbstr_cnt = 0
    for i in range(0, len(lst)):
        if sbstr in lst[i]['name']:
            sbstr_cnt += 1
    return sbstr_cnt

def split_totals_goals(case, lst):
    """Retrieves Nutrients and returns them as numbers.

        Args:
         case: whether its calories, carb, fat, protein, sodium, sugar.
         lst: the DataFrame row taken by the vectorization process.

        Returns:
          The value specified by the case.
    """
    def split_calories(lst):
        index = 0
        while index < len(lst):
            if lst[index]['name'] == 'Calories':
                return int(lst[index]['value'])
            index +=1
        return int(0)
    def split_carbs(lst):
        index = 0
        while index < len(lst):
            if lst[index]['name'] == 'Carbs':
                return int(lst[index]['value'])
            index +=1
        return int(0)
    def split_fat(lst):
        index = 0
        while index < len(lst):
            if lst[index]['name'] == 'Fat':
                return int(lst[index]['value'])
            index +=1
        return int(0)
    def split_protein(lst):
        index = 0
        while index < len(lst):
            if lst[index]['name'] == 'Protein':
                return int(lst[index]['value'])
            index +=1
        return int(0)
    def split_sodium(lst):
        index = 0
        while index < len(lst):
            if lst[index]['name'] == 'Sodium':
                return int(lst[index]['value'])
            index +=1
        return int(0)
    def split_sugar(lst):
        index = 0
        while index < len(lst):
            if lst[index]['name'] == 'Sugar':
                return int(lst[index]['value'])
            index +=1
        return int(0)
    if case == 'Calories':return split_calories(lst)
    elif case == 'Carbs':return split_carbs(lst)
    elif case == 'Fat':return split_fat(lst)
    elif case == 'Protein':return split_protein(lst)
    elif case == 'Sodium':return split_sodium(lst)
    elif case == 'Sugar':return split_sugar(lst)

def sub_cols(x,y):
    """Simple sub function meant to be used in vectorization to minimize execution time"""
    return x-y
        
def split_intakes_to_sequences(case,lst):
    """Splits Intakes into sequences (arrays)

        Args:
         case: whether its name, calories, carb, fat, protein, sodium, sugar.
         lst: the DataFrame row taken by the vectorization process.

        Returns:
          The sequence of food names or nutrient in string.
           E.g. "20 10 50 40 30 50 60 100"
           E.g. "1 mohito ||| 2 bananas ||| 1 steak
    """
    def names():
        names = np.empty(0, dtype=object)
        for row in lst:
            names = np.append(names , row['name'])
        return names
    def num(nutr_type):
        tmp_dict, vals = {}, np.empty(0, dtype=object)
        for row in lst:
            for food in row['nutritions']:
                tmp_dict.update({food['name']: food['value']})
            vals = np.append(vals, tmp_dict[nutr_type].replace(',','')) if nutr_type in tmp_dict.keys() else np.append(vals, 0)
        return vals
    return names() if case=='name' else num(case)

def unique_foods(lst, name_list):
    """Splits foods into a unique list

        Args:
         lst: the DataFrame row taken by the vectorization process.
         name_list: a list containing all the food names (list of uniques).

        Returns:
          The sequence of food names or nutrient in string.
           E.g. "20 10 50 40 30 50 60 100"
           E.g. "1 mohito ||| 2 bananas ||| 1 steak
    """
    tmp_df = pd.DataFrame(columns=['NAME','CALS','CARB','FAT','PROT','SOD','SUG'])
    for row in lst:
        tmp_dict = {}
        for food in row['nutritions']:
            tmp_dict.update({food['name']: food['value'].replace(',','.').rstrip()})
        if row['name'] not in name_list:
            tmp_df = tmp_df.append(pd.DataFrame([[row['name'], str(tmp_dict['Calories']) if 'Calories' in tmp_dict.keys() else 0, str(tmp_dict['Carbs']) if 'Carbs' in tmp_dict.keys() else 0,
                                    str(tmp_dict['Fat']) if 'Fat' in tmp_dict.keys() else 0, str(tmp_dict['Protein']) if 'Protein' in tmp_dict.keys() else 0, 
                                    str(tmp_dict['Sodium']) if 'Sodium' in tmp_dict.keys() else 0, str(tmp_dict['Sugar']) if 'Sugar' in tmp_dict.keys() else 0]],
                                   columns=('NAME','CALS','CARB','FAT','PROT','SOD','SUG')))
    return tmp_df


def create_dataframes():
    """Create DataFrames

        Returns:
            Creates and Saves DataFrames needed on later stages on ml folders.
    """
    print('Importing original CSV...')
    conf = configparser.ConfigParser()
    conf.read("_conf/config.conf")
    df = pd.read_csv(conf['original_dataset']['tsv'], sep='\t')
    df.columns = ['USER_ID','DATE','INTAKES','DAY_FINAL']
    print('Splitting Meal Name & Dishes...')
    df['MEAL_NAME'] = np.vectorize(split_intakes)('meal_name', df['INTAKES'])
    df['FOOD_INTAKES'] = np.vectorize(split_intakes)('dishes', df['INTAKES'])
    df.drop(['INTAKES'], axis=1, inplace=True)
    print('Splitting Totals from Goals...')
    df['TOTAL'] = np.vectorize(split_day_final)('total', df['DAY_FINAL'])
    df['GOAL'] = np.vectorize(split_day_final)('goal', df['DAY_FINAL'])
    df.drop(['DAY_FINAL'], axis=1, inplace=True)
    print('Creating Food Logging Count...')
    df['LOGS'] = np.vectorize(food_intakes_count)(df['FOOD_INTAKES'])
    df['RAW_CAL_OCC'] = np.vectorize(quickly_added_calories_occurences)(df['FOOD_INTAKES'])
    logs_col = df.pop("LOGS")
    rco_col = df.pop("RAW_CAL_OCC")
    df.insert(3, "LOGS", logs_col)
    df.insert(4, "RAW_CAL_OCC", rco_col)
    print('Splitting Totals...')
    df['TOTAL_CALS'] = np.vectorize(split_totals_goals)('Calories', df['TOTAL'])
    df['TOTAL_CARB'] = np.vectorize(split_totals_goals)('Carbs', df['TOTAL'])
    df['TOTAL_FAT'] = np.vectorize(split_totals_goals)('Fat', df['TOTAL'])
    df['TOTAL_PROT'] = np.vectorize(split_totals_goals)('Protein', df['TOTAL'])
    df['TOTAL_SOD'] = np.vectorize(split_totals_goals)('Sodium', df['TOTAL'])
    df['TOTAL_SUG'] = np.vectorize(split_totals_goals)('Sugar', df['TOTAL'])
    df.drop(['TOTAL'],axis=1,inplace=True)
    print('Splitting Goals...')
    df['GOAL_CALS'] = np.vectorize(split_totals_goals)('Calories', df['GOAL'])
    df['GOAL_CARB'] = np.vectorize(split_totals_goals)('Carbs', df['GOAL'])
    df['GOAL_FAT'] = np.vectorize(split_totals_goals)('Fat', df['GOAL'])
    df['GOAL_PROT'] = np.vectorize(split_totals_goals)('Protein', df['GOAL'])
    df['GOAL_SOD'] = np.vectorize(split_totals_goals)('Sodium', df['GOAL'])
    df['GOAL_SUG'] = np.vectorize(split_totals_goals)('Sugar', df['GOAL'])
    df.drop(['GOAL'],axis=1,inplace=True)
    print('Removing Rows with Horrible Values')
    col_list=['TOTAL_CALS','TOTAL_CARB','TOTAL_FAT','TOTAL_PROT','TOTAL_SOD', 'TOTAL_SUG',
              'GOAL_CALS','GOAL_CARB','GOAL_FAT','GOAL_PROT','GOAL_SOD','GOAL_SUG',]
    important=['TOTAL_CALS', 'TOTAL_CARB', 'GOAL_CALS', 'GOAL_CARB']
    flt_list=[]
    for col in col_list:
        flt_list.append(df[col]<=(np.percentile([np.array(x) for x in df[col]], 99)))
        if col in important: flt_list.append(df[col]>=(np.percentile([np.array(x) for x in df[col]], 0.5)))
    fflt=True
    for flt in flt_list:
        fflt = fflt&flt
    df = df.loc[fflt].reset_index(drop=True)
    print('Limiting users to those that have logged at least 30 days...')                       # from 587.186 to 540.495 rows (=46.691)
    df = df[df['USER_ID'].map(df['USER_ID'].value_counts()) > 29].reset_index(drop=True)
    print('Creating Averages DataFrame...')
    df_averages =  df.copy().groupby(['USER_ID']).mean().reset_index()[['USER_ID','LOGS','RAW_CAL_OCC','TOTAL_CALS','TOTAL_CARB','TOTAL_FAT','TOTAL_PROT','TOTAL_SOD','TOTAL_SUG']]
    print('Saving Averages DataFrame')
    df_averages.to_pickle(conf['main_datasets']['averages'], compression='gzip')
    del df_averages
    print('Creating Deficit Columns...')
    df['DEFICIT_CALS'] = np.vectorize(sub_cols)(df['GOAL_CALS'], df['TOTAL_CALS'])
    df['DEFICIT_CARB'] = np.vectorize(sub_cols)(df['GOAL_CARB'], df['TOTAL_CARB'])
    df['DEFICIT_FAT'] = np.vectorize(sub_cols)(df['GOAL_FAT'], df['TOTAL_FAT'])
    df['DEFICIT_PROT'] = np.vectorize(sub_cols)(df['GOAL_PROT'], df['TOTAL_PROT'])
    df['DEFICIT_SOD'] = np.vectorize(sub_cols)(df['GOAL_SOD'], df['TOTAL_SOD'])
    df['DEFICIT_SUG'] = np.vectorize(sub_cols)(df['GOAL_SUG'], df['TOTAL_SUG'])
    print('Transforming DataFrame Columns...')
    df_intakes = df.copy()[['USER_ID','FOOD_INTAKES']] 
    df.drop('FOOD_INTAKES',axis=1,inplace=True)
    df.drop('MEAL_NAME',axis=1,inplace=True)
    df['DATE'] = pd.to_datetime(df['DATE'], format="%Y-%m-%d")
    df['DATE'] = df['DATE'].values.astype(np.int64) // 10 ** 9
    print('Saving Regtest DataFrame...')
    df.to_pickle(conf['main_datasets']['reg'], compression='gzip')
    del df
    print('Creating Intakes DataFrame')
    df_intakes['sequence_name'] = np.vectorize(split_intakes_to_sequences)('name',df_intakes['FOOD_INTAKES'])
    df_intakes['sequence_cals'] = np.vectorize(split_intakes_to_sequences)('Calories',df_intakes['FOOD_INTAKES'])
    df_intakes['sequence_carb'] = np.vectorize(split_intakes_to_sequences)('Carbs',df_intakes['FOOD_INTAKES'])
    df_intakes['sequence_fat'] = np.vectorize(split_intakes_to_sequences)('Fat',df_intakes['FOOD_INTAKES'])
    df_intakes['sequence_prot'] = np.vectorize(split_intakes_to_sequences)('Protein',df_intakes['FOOD_INTAKES'])
    df_intakes['sequence_sod'] = np.vectorize(split_intakes_to_sequences)('Sodium',df_intakes['FOOD_INTAKES'])
    df_intakes['sequence_sug'] = np.vectorize(split_intakes_to_sequences)('Sugar',df_intakes['FOOD_INTAKES'])
    df_intakes.drop(['FOOD_INTAKES'],axis=1,inplace=True)
    print('Saving Intakes DataFrame')
    df_intakes.to_pickle(conf['main_datasets']['int'], compression='gzip')


create_dataframes()