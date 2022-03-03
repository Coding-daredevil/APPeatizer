from tqdm import tqdm
import os
from os import path 
import sys
from typing import Dict, Text
import numpy as np
import pandas as pd
import pathlib
sys.path.append(str(pathlib.Path().resolve()))
from _obsolete.ml.preprocessing.sequence_preparation import prepare_snd
import configparser
conf = configparser.ConfigParser()
conf.read("_conf/config.conf")

save_path = conf['_obsolete_ml_savepath']['d4d']
for i in range(1,12):
    for j in range(0, 2):
        for k in range(1, 8):
            variation='keep' if j==0 else 'jump'
            variation=variation+str(i)
            log_threshold='_threshold'+str(k)
            df_name = save_path+variation+log_threshold
            print('Preparing: ', df_name)
            df_regtest, df_intakes = prepare_snd(i,j,k)
            df_regtest.to_pickle(df_name+'_reg', compression='gzip')
            df_intakes.to_pickle(df_name+'_int', compression='gzip')