import os
from os import path
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
from typing import Dict, Text
import pickle
import re
import numpy as np
import pandas as pd
import tensorflow as tf
tf.get_logger().setLevel('ERROR')
import configparser
conf = configparser.ConfigParser()
conf.read("_conf/config.conf")
import tensorflow_recommenders as tfrs
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.preprocessing.sequence import pad_sequences

def make_predictions(model_acc, test, case=0):
    """Make Predictions

        Args:
         model_acc: Model's Testing Accuracy
         test: Testing Set
         case: whether days(0) or weeks(1)

        Returns:
         accuracy dictionary
    """
    label_name = 'FINAL' if not case else 'NWDEF'
    q = np.empty(0, dtype='int')
    for x in test: q = np.append(q, x[label_name])
    baseline = q.sum()/len(q) if q.sum()>=len(q)/2 else 1-q.sum()/len(q)
    return {'Model': 100*round(model_acc,4), 'Baseline': 100*round(baseline,4), 'Difference': 100*round(model_acc-baseline,4)}

def atoi(text):
    """Returns integer if text is a number, otherwise the text"""
    return int(text) if text.isdigit() else text

def natural_keys(text):
    """Function that 'naturally' orders a given list as a human would based on text. Naturally means 1->13 and not 1, 10, 11, 12, 13, 2, 3, etc."""
    return [ atoi(c) for c in re.split(r'(\d+)', text) ]

def prepare_sets(tf_ratings, query):
    """Prepare Sets

        Args:
         tf_ratings: The tensorflow dataset to be used.
         query: whether we want train/train+val/train+val+test

        Returns:
         class of value
    """
    num = len(tf_ratings)
    if not query:
        print(' Training: 100%')
        shuffled = tf_ratings.shuffle(len(tf_ratings), seed=42, reshuffle_each_iteration=False)
        train = shuffled.take(num)
        cached_train = train.shuffle(num).batch(256).cache()
        return train, 0, 0, cached_train, 0, 0
    elif query==1:
        print(' Training: 80%, Validation: 20%')
        train_set, val_set = int(num*0.80), int(num*0.20)
        shuffled = tf_ratings.shuffle(len(tf_ratings), seed=42, reshuffle_each_iteration=False)
        train, val = shuffled.take(train_set), shuffled.skip(train_set).take(val_set)
        cached_train, cached_val = train.shuffle(train_set).batch(int(conf['ml']['train_bsize'])).cache(), val.shuffle(val_set).batch(int(conf['ml']['val_bsize'])).cache()
        return train, val, 0, cached_train, cached_val, 0
    else:
        print(' Training: 70%, Validation: 15%, Testing: 15%')
        train_set, val_set, test_set = int(num*0.70), int(num*0.15), int(num*0.15)
        shuffled = tf_ratings.shuffle(len(tf_ratings), seed=42, reshuffle_each_iteration=False)
        train, val, test = shuffled.take(train_set), shuffled.skip(train_set).take(val_set), shuffled.skip(train_set+val_set).take(test_set)
        cached_train, cached_val, cached_test = train.shuffle(train_set).batch(int(conf['ml']['train_bsize'])).cache(), val.shuffle(val_set).batch(int(conf['ml']['val_bsize'])).cache(), test.batch(int(conf['ml']['test_bsize'])).cache()
        return train, val, test, cached_train, cached_val, cached_test

def categorize(intakes, label, mean):
    """Make Predictions

        Args:
         intakes: intakes value from np.vectorization
         label: the label name, 'DEFICIT_SCORE' or 'NEXT_WEEK_DEFICIT'
         mean: the mean of the column

        Returns:
         class of value
    """
    intakes[label] = intakes[label].apply(lambda x: 1 if x>=mean else 0)

def prepare_dataset(regtest, intakes, case=0, query=0, obsolete=False):
    """Prepare Dataset for Input in Model

        Args:
         regtest: The dataset created for days->day prediction (part containing totals/goals)
         intakes: The dataset created for days->day prediction (part containing array sequences)
         case: days(0) or weeks(1)
         query: Indicates whether the model is meant about predicting calories or lapses (0, 1).
         obsolete: whether we need it for the obsolete folder or the app (we normalize by ourselves in _obsolete).

        Returns:
         tf_ratings (tensorflow dataset) which contains the proper transformation of string sequences into arrays, as well as padding and proper conversion.
    """
    label='DEFICIT_SCORE' if case==0 else 'NEXT_WEEK_DEFICIT'
    label_name = 'FINAL' if case==0 else 'NWDEF'
    perc = [np.array(len(x)) for x in intakes['sequence_cals']]
    maxseq = int(np.percentile(perc, 98))
    if obsolete:
        case_list, arr = ['sequence_cals', 'sequence_carb', 'sequence_fat', 'sequence_prot', 'sequence_sod', 'sequence_sug', 'sequence_scr'], []
        for case in case_list:
            q = np.concatenate(intakes[case].to_numpy())
            std, mean = q.std(), q.mean()
            if case!='sequence_scr': arr.append(pad_sequences([(x-mean)/std for x in intakes[case]], maxlen=maxseq, dtype=float, value=0))
            else: arr.append([(np.array(t)-mean)/std.astype(float) for t in intakes[case]])
        if query:
            mean = intakes[label].mean()
            categorize(intakes, label, mean)
        arr_label =  [np.array([t]).astype(int) for t in intakes[label]]
        arr_cals, arr_carb, arr_fat, arr_prot, arr_sod, arr_sug, arr_scr, arr_label = arr[0], arr[1], arr[2], arr[3], arr[4], arr[5], arr[6]
    else:
        save_path='ml/data/site_implementation/days_to_day_prediction/results/days_maxseq.pickle' if not case else 'ml/data/site_implementation/weeks_to_week_prediction/results/weeks_maxseq.pickle'
        with open(save_path, 'wb') as handle:
            pickle.dump(maxseq, handle, protocol=pickle.HIGHEST_PROTOCOL)
        arr_cals = pad_sequences(intakes['sequence_cals'], maxlen=maxseq, dtype=float, value=0)
        arr_carb = pad_sequences(intakes['sequence_carb'], maxlen=maxseq, dtype=float, value=0)
        arr_fat  = pad_sequences(intakes['sequence_fat'], maxlen=maxseq, dtype=float, value=0)
        arr_prot = pad_sequences(intakes['sequence_prot'], maxlen=maxseq, dtype=float, value=0)
        arr_sod  = pad_sequences(intakes['sequence_sod'], maxlen=maxseq, dtype=float, value=0)
        arr_sug  = pad_sequences(intakes['sequence_sug'], maxlen=maxseq, dtype=float, value=0)
        arr_scr  = [np.array(t).astype(float) for t in intakes['sequence_scr']]
        if query: 
            mean = intakes[label].mean()
            categorize(intakes, label, mean)
        arr_label =  [np.array([t]).astype(int) for t in intakes[label]]
    tf_ratings = tf.data.Dataset.from_tensor_slices({
        'USER_ID': tf.convert_to_tensor(intakes['USER_ID'].astype(int)),
        'CALS': tf.convert_to_tensor(arr_cals),
        'CARB': tf.convert_to_tensor(arr_carb),
        'FAT':  tf.convert_to_tensor(arr_fat),
        'PROT': tf.convert_to_tensor(arr_prot),
        'SOD':  tf.convert_to_tensor(arr_sod),
        'SUG':  tf.convert_to_tensor(arr_sug),
        'SCR':  tf.convert_to_tensor(arr_scr),
        label_name: tf.convert_to_tensor(arr_label),
    })
    return tf_ratings

def get_model(tf_ratings, case=0, deflap=0, obsolete=False):
    """Prepares Model (Diff: 
       We use TF to normalize in app-ml due to inserting queries from the application)

        Args:
         tf_ratings: The tensorflow dataset to be used.
         case: Whether day(0) or week(1)
         deflap: Whether regression(0) or classification(1)
         obsolete: whether we need it for the obsolete folder or the app (we normalize by ourselves in _obsolete).

        Returns:
         The CombinedModel
    """
    user_ids = tf_ratings.batch(1_000_000).map(lambda x: x["USER_ID"])
    unique_user_ids = np.unique(np.concatenate(list(user_ids)))
    class SequenceModel(tf.keras.Model):
        def __init__(self):
            super().__init__()
            embedding_dimension = 16
            self.user_embedding = tf.keras.Sequential([
                tf.keras.layers.experimental.preprocessing.IntegerLookup(
                        vocabulary=unique_user_ids, mask_token=None),
                tf.keras.layers.Embedding(len(unique_user_ids)+1, embedding_dimension)
            ])
            if obsolete:
                self.cals = tf.keras.layers.InputLayer()
                self.carb = tf.keras.layers.InputLayer()
                self.fat = tf.keras.layers.InputLayer()
                self.prot = tf.keras.layers.InputLayer()
                self.sod = tf.keras.layers.InputLayer()
                self.sug = tf.keras.layers.InputLayer()
                self.scr = tf.keras.layers.InputLayer()
            else:
                self.cals = tf.keras.layers.Normalization(axis=None)
                self.carb = tf.keras.layers.Normalization(axis=None)
                self.fat  = tf.keras.layers.Normalization(axis=None)
                self.prot = tf.keras.layers.Normalization(axis=None)
                self.sod  = tf.keras.layers.Normalization(axis=None)
                self.sug  = tf.keras.layers.Normalization(axis=None)
                self.scr  = tf.keras.layers.Normalization(axis=None)
        def call(self, inputs):
            return tf.concat([
                self.user_embedding(inputs["USER_ID"]),
                self.cals(inputs["CALS"]),
                self.carb(inputs["CARB"]),
                self.fat(inputs["FAT"]),
                self.prot(inputs["PROT"]),
                self.sod(inputs["SOD"]),
                self.sug(inputs["SUG"]),
                self.scr(inputs["SCR"])
            ], axis=1)
    class CombinedModel(tfrs.models.Model):
        def __init__(self) -> None:
            super().__init__()
            self.sequence_model: tf.keras.layers.Layer = tf.keras.Sequential([SequenceModel()])
            self.rating_model = tf.keras.Sequential([
                tf.keras.layers.Dense(2048, activation="relu", kernel_regularizer=tf.keras.regularizers.L2(float(conf['ml']['L2reg']))),
                tf.keras.layers.Dense(1024, activation="relu", kernel_regularizer=tf.keras.regularizers.L2(float(conf['ml']['L2reg']))),
                tf.keras.layers.Dense(512, activation="relu", kernel_regularizer=tf.keras.regularizers.L2(float(conf['ml']['L2reg']))),
                tf.keras.layers.Dense(256, activation="relu", kernel_regularizer=tf.keras.regularizers.L2(float(conf['ml']['L2reg']))),
                tf.keras.layers.Dense(128, activation="relu", kernel_regularizer=tf.keras.regularizers.L2(float(conf['ml']['L2reg']))),
                tf.keras.layers.Dense(64, activation="relu", kernel_regularizer=tf.keras.regularizers.L2(float(conf['ml']['L2reg']))),
                tf.keras.layers.Dense(32, activation="relu", kernel_regularizer=tf.keras.regularizers.L2(float(conf['ml']['L2reg']))),
                tf.keras.layers.Dense(1, activation="sigmoid") if deflap else tf.keras.layers.Dense(1)
            ])
            self.rating_task: tf.keras.layers.Layer = tfrs.tasks.Ranking(
                loss=tf.keras.losses.BinaryCrossentropy(from_logits=False) if deflap else tf.keras.losses.MeanSquaredError(),
                metrics=[tf.keras.metrics.BinaryAccuracy()] if deflap else [tf.keras.metrics.RootMeanSquaredError()],
            )
        def call(self, features: Dict[Text, tf.Tensor]) -> tf.Tensor:
            sequence_embeddings = self.sequence_model({
                "USER_ID": features["USER_ID"],
                "CALS": features["CALS"],
                "CARB": features["CARB"],
                "FAT": features["FAT"],
                "PROT": features["PROT"],
                "SOD": features["SOD"],
                "SUG": features["SUG"],
                "SCR": features["SCR"]
            })
            return self.rating_model(sequence_embeddings)
        def compute_loss(self, features: Dict[Text, tf.Tensor], training=False) -> tf.Tensor:
            if case==0: ratings = features.pop('FINAL')
            else: ratings = features.pop("NWDEF")
            rating_predictions = self(features)
            rating_loss = self.rating_task(
                labels=ratings,
                predictions=rating_predictions,
            )
            return rating_loss
    return CombinedModel()