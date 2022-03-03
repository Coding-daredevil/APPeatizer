from gc import callbacks
from tqdm import tqdm
import os
from os import path
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import pickle
from typing import Dict, Text
import numpy as np
import pandas as pd
import tensorflow as tf
tf.get_logger().setLevel('ERROR')
import datetime
import tensorflow_recommenders as tfrs
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.preprocessing.sequence import pad_sequences
import pathlib
import sys
sys.path.append(str(pathlib.Path().resolve()))
import configparser
from ml.ml_preparation import get_model, categorize, prepare_dataset, prepare_sets, make_predictions

conf = configparser.ConfigParser()
conf.read("_conf/config.conf")

def prepare_run_and_save():
    """Prepare, Run and Save Model

        Returns:
         Creates, Trains and Saves Model for use in the Application
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
    print('Preparing Dataset...')
    regp = conf['ml_savepath']['d2dreg']
    intp = conf['ml_savepath']['d2dint']
    regtest, intakes = pd.read_pickle(regp, compression='gzip'), pd.read_pickle(intp, compression='gzip')
    tf_ratings = prepare_dataset(regtest, intakes, 0, query3)
    print('Preparing Sets...')
    train, val, test, cached_train, cached_val, cached_test = prepare_sets(tf_ratings, query)
    print('Preparing Model...')
    model = get_model(tf_ratings, 0, query3, False)
    model.compile(optimizer=tf.keras.optimizers.Adagrad(float(conf['ml']['lrate']))) 
    monitor_loss, stop_patience = 'val_root_mean_squared_error' if query3==0 else 'val_binary_accuracy', int(conf['ml']['patience'])
    if query2:
        logdir = os.path.join(conf['ml_savepath']['d4dlog'], datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
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
    with open(conf['ml_savepath']['dres']+'hist'+'.pickle', 'wb') as handle:
        pickle.dump(hist, handle, protocol=pickle.HIGHEST_PROTOCOL)
    if query==2:
        metrics = model.evaluate(cached_test, return_dict=True)
        with open(conf['ml_savepath']['dres']+'metr'+'.pickle', 'wb') as handle:
            pickle.dump(metrics, handle, protocol=pickle.HIGHEST_PROTOCOL)
        if query3==1:
            acc = make_predictions(metrics['binary_accuracy'], test, 0)
            with open(conf['ml_savepath']['dres']+'acc'+'.pickle', 'wb') as handle:
                pickle.dump(acc, handle, protocol=pickle.HIGHEST_PROTOCOL)
            print("Model's Accuracy at predicting new day lapse: ", acc)
    print(' Saving Tower Model and Checkpoints')
    model.save(conf['ml_savepath']['dres']+'model')

prepare_run_and_save()








###[Working Two Tower Model]###
#def get_model(tf_ratings):
#    """Prepare Dataset for Input in Model
#
#        Args:
#         tf_ratings: The tensorflow dataset created above.
#
#        Returns:
#         The CombinedModel
#    """
#    user_ids = tf_ratings.batch(1_000_000).map(lambda x: x["USER_ID"])
#    unique_user_ids = np.unique(np.concatenate(list(user_ids)))
#    class UserModel(tf.keras.Model):
#        def __init__(self):
#            super().__init__()
#            embedding_dimension = 200
#            self.user_embedding = tf.keras.Sequential([
#                tf.keras.layers.experimental.preprocessing.IntegerLookup(
#                        vocabulary=unique_user_ids, mask_token=None),
#                tf.keras.layers.Embedding(len(unique_user_ids)+1, embedding_dimension)
#            ])
#        def call(self, inputs):
#            return tf.concat([self.user_embedding(inputs["USER_ID"]),], axis=1)
#    class SequenceModel(tf.keras.Model):
#        def __init__(self):
#            super().__init__()
#            #embedding_dimension = 200
#            self.cals = tf.keras.layers.Normalization(axis=None)
#            self.carb = tf.keras.layers.Normalization(axis=None)
#            self.fat = tf.keras.layers.Normalization(axis=None)
#            self.prot = tf.keras.layers.Normalization(axis=None)
#            self.sod = tf.keras.layers.Normalization(axis=None)
#            self.sug = tf.keras.layers.Normalization(axis=None)
#            self.scr = tf.keras.layers.Normalization(axis=None)
#        def call(self, inputs):
#            return tf.concat([
#                #self.user_embedding(inputs["USER_ID"]),
#                self.cals(inputs["CALS"]),
#                self.carb(inputs["CARB"]),
#                self.fat(inputs["FAT"]),
#                self.prot(inputs["PROT"]),
#                self.sod(inputs["SOD"]),
#                self.sug(inputs["SUG"]),
#                self.scr(inputs["SCR"])
#            ], axis=1)
#    class CombinedModel(tfrs.models.Model):
#        def __init__(self) -> None:
#            super().__init__()
#            embedding_dimension = 200
#            self.user_model: tf.keras.layers.Layer = tf.keras.Sequential([
#            UserModel(),
#            tf.keras.layers.Dense(embedding_dimension)
#            ])
#            self.sequence_model: tf.keras.layers.Layer = tf.keras.Sequential([
#            SequenceModel(),
#            tf.keras.layers.Dense(embedding_dimension)
#            ])
#            self.rating_model = tf.keras.Sequential([
#                tf.keras.layers.Dense(2048, activation="relu"),
#                tf.keras.layers.Dense(1024, activation="relu"),
#                tf.keras.layers.Dense(512, activation="relu"),
#                tf.keras.layers.Dense(256, activation="relu"),
#                tf.keras.layers.Dense(128, activation="relu"),
#                tf.keras.layers.Dense(64, activation="relu"),
#                tf.keras.layers.Dense(32, activation="relu"),
#                tf.keras.layers.Dense(1),
#            ])
#            self.rating_task: tf.keras.layers.Layer = tfrs.tasks.Ranking(
#                loss=tf.keras.losses.MeanSquaredError(),
#                metrics=[tf.keras.metrics.RootMeanSquaredError()],
#            )
#        def call(self, features: Dict[Text, tf.Tensor]) -> tf.Tensor:
#            user_embeddings = self.user_model({"USER_ID": features["USER_ID"]})
#            sequence_embeddings = self.sequence_model({
#                #"USER_ID": features["USER_ID"],
#                "CALS": features["CALS"],
#                "CARB": features["CARB"],
#                "FAT": features["FAT"],
#                "PROT": features["PROT"],
#                "SOD": features["SOD"],
#                "SUG": features["SUG"],
#                "SCR": features["SCR"],
#            })
#            return self.rating_model(tf.concat([user_embeddings, sequence_embeddings], axis=1))
#            #return self.rating_model(sequence_embeddings)
#        def compute_loss(self, features: Dict[Text, tf.Tensor], training=False) -> tf.Tensor:
#            ratings = features.pop("FINAL")
#            rating_predictions = self(features)
#            rating_loss = self.rating_task(
#                labels=ratings,
#                predictions=rating_predictions,
#            )
#            return rating_loss
#    return CombinedModel()