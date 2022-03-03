from tqdm import tqdm
import os
from os import path
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
from typing import Dict, Text
import glob
import datetime
import re
import pickle
import numpy as np
import pandas as pd
import tensorflow as tf
tf.get_logger().setLevel('ERROR')
import tensorflow_recommenders as tfrs
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.preprocessing.sequence import pad_sequences
import pathlib
import sys
import configparser
sys.path.append(str(pathlib.Path().resolve()))
from ml.preprocessing.sequence_preparation import prepare_deficit_prediction_dataset_sndw
from ml.ml_preparation import get_model, categorize, prepare_dataset, prepare_sets, make_predictions

conf = configparser.ConfigParser()
conf.read("_conf/config.conf")

def prepare_run_and_save():
    """Prepare, Run and Save Model

        Returns:
         Creates, Trains and Saves Model for use in the Application.
    """
    while True:
        try:
            query = int(input('[0, 1, 2] Would you like Train Only, Validation Only, Testing+Validation: '))
            if query!=1 and query!=0 and query!=2: raise ValueError 
            break
        except ValueError:
            print("Wrong input, please try again...")  
            continue
    while True:
            try:
                query2 = int(input('[0, 1] Would you like to log for tensorboard?: '))
                if query2!=1 and query2!=0: raise ValueError 
                break
            except ValueError:
                print("Wrong input, please try again...")  
                continue
    while True:
            try:
                query3 = int(input('[0, 1] Deficit/Lapse Prediction?: '))
                if query3!=1 and query3!=0: raise ValueError 
                break
            except ValueError:
                print("Wrong input, please try again...")  
                continue
    regp = conf['ml_savepath']['w2wreg']
    intp = conf['ml_savepath']['w2wint']
    print('Preparing Dataset...')
    regtest, intakes = pd.read_pickle(regp, compression='gzip'), pd.read_pickle(intp, compression='gzip')
    regtest, intakes = prepare_deficit_prediction_dataset_sndw(regtest, intakes)
    tf_ratings = prepare_dataset(regtest, intakes, 1, query3)
    print('Preparing Sets...')
    train, val, test, cached_train, cached_val, cached_test = prepare_sets(tf_ratings, query)
    print('Preparing Model...')
    model = get_model(tf_ratings, 1, query3, False)
    model.compile(optimizer=tf.keras.optimizers.Adagrad(float(conf['ml']['lrate']))) 
    monitor_loss, stop_patience = 'val_root_mean_squared_error' if query3==0 else 'val_binary_accuracy', int(conf['ml']['patience'])
    if query2:
        logdir = os.path.join(conf['ml_savepath']['w4wlog'], datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
        tensorboard_callback = tf.keras.callbacks.TensorBoard(logdir, histogram_freq=1)
        if query: 
            early_stop = tf.keras.callbacks.EarlyStopping(monitor=monitor_loss, patience=stop_patience, restore_best_weights=False)
            model.fit(cached_train, epochs=int(conf['ml']['epochs']), validation_data=cached_val, callbacks=[early_stop, tensorboard_callback])
        else: 
            model.fit(cached_train, epochs=int(conf['ml']['epochs']), callbacks=[tensorboard_callback])
    else:
        if query: 
            callback = tf.keras.callbacks.EarlyStopping(monitor=monitor_loss, patience=stop_patience, restore_best_weights=False)
            model.fit(cached_train, epochs=int(conf['ml']['epochs']), validation_data=cached_val, callbacks=[callback])
        else: 
            model.fit(cached_train, epochs=int(conf['ml']['epochs']))
    hist = model.history.history
    with open(conf['ml_savepath']['wres']+'hist'+'.pickle', 'wb') as handle:
        pickle.dump(hist, handle, protocol=pickle.HIGHEST_PROTOCOL)
    if query==2:
        metrics = model.evaluate(cached_test, return_dict=True)
        with open(conf['ml_savepath']['wres']+'metr'+'.pickle', 'wb') as handle:
            pickle.dump(metrics, handle, protocol=pickle.HIGHEST_PROTOCOL)
        if query3==1:
            acc = make_predictions(metrics['binary_accuracy'], test, 1)
            with open(conf['ml_savepath']['wres']+'acc'+'.pickle', 'wb') as handle:
                pickle.dump(acc, handle, protocol=pickle.HIGHEST_PROTOCOL)
            print("Model's Accuracy at predicting new day lapse: ", acc)
    print(' Saving Tower Model and Checkpoints')
    model.save(conf['ml_savepath']['wres']+'model')


prepare_run_and_save()
    
    




