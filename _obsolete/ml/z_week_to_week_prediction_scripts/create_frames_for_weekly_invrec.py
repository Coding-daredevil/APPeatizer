from tqdm import tqdm
import os
import sys
from os import path 
from typing import Dict, Text
import numpy as np
import pandas as pd
import pathlib
sys.path.append(str(pathlib.Path().resolve()))
from _obsolete.ml.preprocessing.sequence_preparation import prepare_sndw
import configparser
conf = configparser.ConfigParser()
conf.read("_conf/config.conf")

save_path = conf['_obsolete_ml_savepath']['w4w']
for i in range(7,29,7):
    for j in range(1,8):
        weekly_regtest, weekly_intakes = prepare_sndw(i,0,j)
        wrn = save_path+'weekly_regtest_'+str(i)+'d_'+str(j)+'thr'
        win = save_path+'weekly_intakes_'+str(i)+'d_'+str(j)+'thr'
        weekly_regtest.to_pickle(wrn, compression='gzip')
        weekly_intakes.to_pickle(win, compression='gzip')