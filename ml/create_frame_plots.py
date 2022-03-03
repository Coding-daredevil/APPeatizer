from tqdm import tqdm
import os
from os import path 
from typing import Dict, Text
import copy
import numpy as np
import pandas as pd
import pickle
import re
import glob
import matplotlib.pyplot as plt
import configparser
conf = configparser.ConfigParser()
conf.read("_conf/config.conf")

def find_deficit_percentage(goal, deficit):
    """Simple Deficit Percentage Calculation. Meant to be used in vectorization"""
    return round(100*deficit/goal,3) if goal!=0 else 101

def stripper(data):
    """Dict Stripper

        Args:
         data: The dictionary to strip

        Returns:
         the dictionary with all empty keys removed
    """
    new_data = {}
    for k, v in data.items():
        if isinstance(v, dict):
            v = stripper(v)
        if not v in (u'', None, {}):
            new_data[k] = v
    return new_data

def atoi(text):
    """Returns integer if text is a number, otherwise the text"""
    return int(text) if text.isdigit() else text

def natural_keys(text):
    """Function that 'naturally' orders a given list as a human would based on text. Naturally means 1->13 and not 1, 10, 11, 12, 13, 2, 3, etc."""
    return [ atoi(c) for c in re.split(r'(\d+)', text) ]

def validate_parameters(query):
    """Set Parameters

        Args:
         query: Days/Weeks

        Returns:
         makes sure the variables are in proper condition (''=>default) and returns them
    """
    if query=='': query='days'
    return query

def get_load_paths(query):
    """Get Load Paths

        Args:
         query: whether we are dealing in days or weeks

        Returns:
         the load paths to be later utilized in retrieving the histograms and metrics.
    """
    main_path = conf['ml_savepath']['d4d_mn'] if query=='days' else conf['ml_savepath']['w4w_mn']
    load_path_hist, load_path_metr, load_path_acc = main_path+'/hist*', main_path+'/metr*', main_path+'/acc*'
    load_path_hist, load_path_metr, load_path_acc = glob.glob(load_path_hist), glob.glob(load_path_metr), glob.glob(load_path_acc)
    load_path_hist.sort(key=natural_keys)
    load_path_metr.sort(key=natural_keys)
    load_path_acc.sort(key=natural_keys)
    return load_path_hist, load_path_metr, load_path_acc

def get_dicts(query='days'):
    """Get Dicts

        Args:
         query: whether we are dealing in days or weeks

        Returns:
         returns the dictionaries with the training history and testing metrics
    """
    hist_dict, metr_dict, acc_dict = {}, {}, {}
    load_path_hist, load_path_metr, load_path_acc = get_load_paths(query)
    for file in load_path_hist:
        with open(file, 'rb') as f:
            hist_dict = pickle.load(f)
    for file in load_path_metr:
        with open(file, 'rb') as f:
            metr_dict = pickle.load(f)
    for file in load_path_acc:
        with open(file, 'rb') as f:
            acc_dict = pickle.load(f)
    label = 'binary_accuracy' if 'binary_accuracy' in hist_dict.keys() else 'root_mean_squared_error'
    return hist_dict, metr_dict, acc_dict, label

def plot_loss(hlist, title, txt):
    """Plot Loss

        Args:
            hlist: the list of 'histories' to plot
            title: the title of the plot
            txt: the xlabel

        Returns:
            The plot on screen
    """
    for hist in hlist:
        plt.plot(range(1, len(hist[0]) + 1), hist[0], label=hist[1]+' - RMSE')
    plt.title(title)
    plt.xlabel(txt)
    plt.legend()
    plt.grid(True)
    plt.show()

def display_accuracy(query, dct):
    """Create Accuracy Plots

        Args:
         query: whether we are dealing in days or weeks
         dct: The dictionary

        Returns:
         Creates a plot taking into account the last measurement.
    """
    title = 'Days Model' if query=='days' else 'Weeks Model'
    print(title,'\n', 'Model:      ', round(dct['Model'],3), '\n','Baseline:   ', round(dct['Baseline'],3), '\n', 'Difference: ', round(dct['Difference'],3), '\n')

def create_plot(query, dct, label):
    """Create All Plots (Training)

        Args:
         query: whether we are dealing in days or weeks
         dct: The dictionary
         label: deficit/lapse

        Returns:
         Creates all plots
    """
    title = 'Days Model' if query=='days' else 'Weeks Model'
    label_name = 'RMSE' if label=='root_mean_squared_error' else 'ACC'
    hlist = [[dct[label], label_name]]
    hlist.append([dct['val_'+label], 'VAL_'+label_name])
    plot_loss(hlist, title+', Training Results'+'/Epochs', 'Epochs')

def print_testing_results(query, dct, label):
    """Print Testing Results

        Args:
         query: whether we are dealing in days or weeks
         dct: The dictionary
         label: deficit/lapse

        Returns:
         Prints results (RMSE) of testing
    """
    case = 'RMSE: ' if label=='root_mean_squared_error' else 'Accuracy: '
    print('Testing '+case, dct[label])


while True:
  try:
    query = str(input('[days, weeks] Which type would you like to see?: '))
    if query!='days' and query!='weeks' and query!='': raise ValueError 
    break
  except ValueError:
      print("Wrong input, please try again...")  
      continue
print('Setting Parameters and preparing Dictionaries')
query = validate_parameters(query)
hist_dict, metr_dict, acc_dict, label = get_dicts(query)
print("[1] Display Accuracies\n[2] Create Training + Validation Plot\n[3] Display Testing Results")
while True:
  try:
    ch = int(input('[0-3] Enter your choice: '))
    if ch>3 or ch<0: raise ValueError 
  except ValueError:
      print("Wrong input, please try again...")  
      continue
  if ch==1: display_accuracy(query, acc_dict)
  elif ch==2: create_plot(query, hist_dict, label)
  elif ch==3: print_testing_results(query, metr_dict, label)
  else: break