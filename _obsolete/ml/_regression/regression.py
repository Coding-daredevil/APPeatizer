from gc import callbacks
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
np.set_printoptions(precision=3, suppress=True)
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.layers.experimental import preprocessing
import configparser
conf = configparser.ConfigParser()
conf.read("_conf/config.conf")

def filter_unwanted():
    """Filters unwated rows from the dataset"""
    regtest = pd.read_pickle(conf['main_datasets']['reg'], compression='gzip')
    f1 = regtest['RAW_CAL_OCC']==0
    f2 = abs(regtest['GOAL_CALS']) >= 200
    f3 = abs(regtest['GOAL_CARB']) != 0
    f4 = abs(regtest['GOAL_FAT']) != 0
    f5 = abs(regtest['GOAL_PROT']) != 0
    f6 = abs(regtest['GOAL_SOD']) != 0
    f7 = abs(regtest['GOAL_SUG']) != 0
    regtest = regtest.loc[f1&f2&f3&f4&f5&f6&f7].reset_index(drop=True).drop(['RAW_CAL_OCC'],axis=1)
    f2 = abs(regtest['DEFICIT_CALS']) <= 4000
    f3 = abs(regtest['DEFICIT_CARB']) <= 4000
    f4 = abs(regtest['DEFICIT_FAT']) <= 4000
    f5 = abs(regtest['DEFICIT_PROT']) <= 4000
    f6 = abs(regtest['DEFICIT_SOD']) <= 4000
    f7 = abs(regtest['DEFICIT_SUG']) <= 4000
    regtest = regtest.loc[f2&f3&f4&f5&f6&f7].reset_index(drop=True)
    return regtest

def plot_loss(history):
  """
      Args:
          history: the history of the model
  
      Returns:
          The loss plot
  """
  plt.plot(history.history['loss'], label='loss')
  plt.plot(history.history['val_loss'], label='val_loss')
  plt.xlabel('Epoch')
  plt.ylabel('Error [MPG]')
  plt.legend()
  plt.grid(True)
  plt.show()

def create_model():
    """  
      Returns:
          Creates and trains the model and returns the training history.
    """
    regtest = filter_unwanted()[['USER_ID','LOGS','DEFICIT_CALS','DEFICIT_CARB','DEFICIT_FAT','DEFICIT_PROT','DEFICIT_SOD','DEFICIT_SUG']]
    train_dataset = regtest.sample(frac=0.8, random_state=0)
    test_dataset = regtest.drop(train_dataset.index)
    train_features = train_dataset.copy()
    test_features = test_dataset.copy()
    train_labels = train_features.pop('DEFICIT_CALS')
    test_labels = test_features.pop('DEFICIT_CALS')
    normalizer = preprocessing.Normalization(axis=-1)
    normalizer.adapt(np.array(train_features))
    linear_model = tf.keras.Sequential([
        normalizer,
        layers.Dense(128, activation='relu'),
        layers.Dense(64, activation='relu'),
        layers.Dense(64, activation='relu'),
        layers.Dense(64, activation='relu'),
        layers.Dense(32, activation='relu'),
        layers.Dense(1)
    ])
    linear_model.predict(train_features[:10])
    linear_model.layers[1].kernel
    linear_model.compile(
        optimizer=tf.optimizers.Adam(learning_rate=0.001),
        loss='mean_absolute_error',
        metrics='mean_absolute_error')
    early_stop = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=3)
    print(linear_model.summary())
    history = linear_model.fit(
        train_features, train_labels, 
        batch_size=64, validation_batch_size=32,
        epochs=20, verbose=1,
        validation_split = 0.2,
        callbacks = [early_stop]
    )
    metrics = linear_model.evaluate(test_features, test_labels, return_dict=True)
    print(metrics)
    return history

history = create_model()
plot_loss(history)


##[Loss: 111, ValLoss: 112]