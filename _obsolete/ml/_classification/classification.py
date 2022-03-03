import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
np.set_printoptions(precision=3, suppress=True)
import tensorflow as tf
tf.get_logger().setLevel('ERROR')
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.layers.experimental import preprocessing
import configparser
conf = configparser.ConfigParser()
conf.read("_conf/config.conf")


def find_deficit_percentage(goal, deficit):
    """Simple Deficit Percentage Calculation. Meant to be used in vectorization"""
    return round(100*deficit/goal,3) if goal!=0 else 101


def classify_score(score):
    """Simple 7-way classification"""
    def score_calculator(score):
        """Returns between -3 and +3 depending on class"""
        return 0 if abs(score) < 10 else 1*np.sign(score) if abs(score) < 25 else 2*np.sign(score) if abs(score) < 50 else 3*np.sign(score)
    return 3 + score_calculator(score)

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

def get_preprocessing_results():
    """
        Returns:
         Train/Test Features/Labels, as well as the normalizer
    """
    regtest = filter_unwanted()
    regtest['DEFICIT_SCORE'] = np.vectorize(find_deficit_percentage)(regtest['GOAL_CALS'],regtest['DEFICIT_CALS'])
    regtest['DEFICIT_SCORE'] = np.vectorize(classify_score)(regtest['DEFICIT_SCORE'])
    regtest.drop(['GOAL_CALS','DEFICIT_CALS'],axis=1,inplace=True)
    train_dataset = regtest.sample(frac=0.8, random_state=0)
    test_dataset = regtest.drop(train_dataset.index)
    train_features = train_dataset.copy()
    test_features = test_dataset.copy()
    train_labels = train_features.pop('DEFICIT_SCORE')
    test_labels = test_features.pop('DEFICIT_SCORE')
    normalizer = preprocessing.Normalization(axis=-1)
    normalizer.adapt(np.array(train_features))
    return train_features, test_features, train_labels, test_labels, normalizer

def build_and_compile_model(norm):
    """
        Returns:
         A simple Model
    """
    model = tf.keras.Sequential([
        norm,
        layers.Dense(128, activation='relu'),
        layers.Dense(64, activation='relu'),
        layers.Dense(64, activation='relu'),
        layers.Dense(64, activation='relu'),
        layers.Dense(32, activation='relu'),
        layers.Dense(7, activation='softmax')
    ])
    model.compile(
        optimizer=tf.optimizers.Adam(learning_rate=0.001),
        loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=False),
        metrics=['accuracy'])
    return model

def train_model(dnn_model):
    """
        Args:
         dnn_model: the model to be trained

        Returns:
         History of training
    """
    dnn_model.summary()
    early_stop = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=5)
    history = dnn_model.fit(
        train_features, train_labels, 
        batch_size=64, validation_batch_size=32,
        epochs=20, verbose=1,
        validation_split = 0.2,
        callbacks = [early_stop])
    metrics = dnn_model.evaluate(test_features, test_labels, return_dict=True)
    print(metrics)
    return history

def plot_loss(history):
    """
        Args:
         history: the history of the model

        Returns:
         The loss plot
    """
    history_dict = history.history
    loss = history_dict['loss']
    acc = history_dict['accuracy']
    val_loss = history_dict['val_loss']
    val_acc = history_dict['val_accuracy']
    epochs = range(1, len(loss) + 1)
    plt.plot(epochs, loss, 'bo', label='Training loss')
    plt.plot(epochs, val_loss, 'b', label='Validation loss')
    plt.title('Training and validation loss')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.legend()
    plt.show()
    ###
    plt.plot(epochs, acc, 'bo', label='Training Accuracy')
    plt.plot(epochs, val_acc, 'b', label='Validation Accuracy')
    plt.title('Training and validation Accuracy')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.legend()
    plt.show()

def get_test_results(dnn_model):
    """
        Args:
         dnn_model: the model to be trained

        Returns:
         Testing Results
    """
    test_results = {}
    test_results['dnn_model'] = dnn_model.evaluate(test_features, test_labels, verbose=0)
    print(pd.DataFrame(test_results, index=['Mean absolute error [MPG]']).T)

train_features, test_features, train_labels, test_labels, normalizer = get_preprocessing_results()
dnn_model = build_and_compile_model(normalizer)
history = train_model(dnn_model)
plot_loss(history)










