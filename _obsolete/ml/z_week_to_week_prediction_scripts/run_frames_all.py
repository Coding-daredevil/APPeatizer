from tqdm import tqdm
import os
from os import path
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
from typing import Dict, Text
import glob
import re
import pickle
import numpy as np
import pandas as pd
import tensorflow as tf
tf.get_logger().setLevel('ERROR')
import tensorflow_recommenders as tfrs
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.preprocessing.sequence import pad_sequences
import configparser
conf = configparser.ConfigParser()
conf.read("_conf/config.conf")
import pathlib
import sys
sys.path.append(str(pathlib.Path().resolve()))
from _obsolete.ml.preprocessing.sequence_preparation import prepare_deficit_prediction_dataset_sndw
from ml.ml_preparation import get_model, prepare_dataset, natural_keys, make_predictions

#while True:
#    try:
#        query = int(input('[0, 1] Deficit/Lapse Prediction: '))
#        if query!=1 and query!=0: raise ValueError 
#        break
#    except ValueError:
#        print("Wrong input, please try again...")  
#        continue
query = int(conf['ml']['deflap'])
save_path = conf['_obsolete_ml_savepath']['w4w_def'] if query==0 else conf['_obsolete_ml_savepath']['w4w_lap']
regp = glob.glob(conf['_obsolete_ml_savepath']['w4w']+'weekly_regtest*')
regp.sort(key=natural_keys)
intp = glob.glob(conf['_obsolete_ml_savepath']['w4w']+'weekly_intakes*')
intp.sort(key=natural_keys)
for i in range(0, len(regp)):
    print('Preparing Dataset...')
    regtest, intakes = regp[i], intp[i]
    name =  'keep'+regtest.split('\\',1)[1].split('_')[2].split('d')[0]+'_threshold'+regtest.split('\\',1)[1].split('_')[3].split('thr')[0]
    regtest, intakes = pd.read_pickle(regtest, compression='gzip'), pd.read_pickle(intakes, compression='gzip')
    regtest, intakes = prepare_deficit_prediction_dataset_sndw(regtest, intakes)
    tf_ratings = prepare_dataset(regtest, intakes, 1, query)
    num = len(tf_ratings)
    train_set, val_set, test_set = int(num*0.70), int(num*0.15), int(num*0.15)
    shuffled = tf_ratings.shuffle(len(tf_ratings), seed=42, reshuffle_each_iteration=False)
    train, val, test = shuffled.take(train_set), shuffled.skip(train_set).take(val_set), shuffled.skip(train_set+val_set).take(test_set)
    cached_train, cached_val, cached_test = train.shuffle(train_set).batch(int(conf['ml']['train_bsize'])).cache(), val.shuffle(val_set).batch(int(conf['ml']['val_bsize'])).cache(), test.batch(int(conf['ml']['test_bsize'])).cache()
    ###[Model Set/Compile/Fit]###
    print('Preparing Model...')
    model = get_model(tf_ratings, 1, query, True)
    model.compile(optimizer=tf.keras.optimizers.Adagrad(float(conf['ml']['lrate'])))
    monitor_loss, stop_patience = 'val_root_mean_squared_error' if query==0 else 'val_binary_accuracy', int(conf['ml']['patience'])
    callback = tf.keras.callbacks.EarlyStopping(monitor=monitor_loss, patience=stop_patience, restore_best_weights=False)
    model.fit(cached_train, epochs=int(conf['ml']['epochs']), validation_data=cached_val, callbacks=[callback])
    hist = model.history.history
    metrics = model.evaluate(cached_test, return_dict=True)
    with open(save_path+'hist'+'_'+name+'.pickle', 'wb') as handle:
        pickle.dump(hist, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with open(save_path+'metr'+'_'+name+'.pickle', 'wb') as handle:
        pickle.dump(metrics, handle, protocol=pickle.HIGHEST_PROTOCOL)
    if query==1:
        acc = make_predictions(metrics['binary_accuracy'], test, 1)
        with open(save_path+'acc'+'_'+name+'.pickle', 'wb') as handle:
            pickle.dump(acc, handle, protocol=pickle.HIGHEST_PROTOCOL)
        print("Model's Accuracy at predicting new day lapse: ", acc, '\n\n\n\n')
