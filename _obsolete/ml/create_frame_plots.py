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

def validate_parameters(query, logt, deflap):
    """Set Parameters

        Args:
         query: Days/Weeks
         logt: LogT parameter value
         deflap: deficit/lapse

        Returns:
         makes sure the variables are in proper condition (''=>default) and returns them
    """
    if query=='': query='days'
    if logt=='': logt='all'
    if deflap=='': deflap='0'
    logt=int(logt) if logt!='all' else logt
    deflap=int(deflap)
    return query, logt, deflap

def get_load_paths(query, logt, deflap):
    """Get Load Paths

        Args:
         query: whether we are dealing in days or weeks
         logt: threshold of holds
         deflap: deficit/lapse

        Returns:
         the load paths to be later utilized in retrieving the histograms and metrics.
    """
    main_path = conf['_obsolete_ml_savepath']['d4d_mn'] if query=='days' else conf['_obsolete_ml_savepath']['w4w_mn']
    main_path = main_path+'_def/' if not deflap else main_path+'_lap/'
    load_path_hist, load_path_metr, load_path_acc = main_path+'/hist*', main_path+'/metr*', main_path+'/acc*'
    load_path_hist = load_path_hist + 'threshold' + str(logt) + '*' if logt!='all' else load_path_hist
    load_path_metr = load_path_metr + 'threshold' + str(logt) + '*' if logt!='all' else load_path_metr
    load_path_acc = load_path_acc + 'threshold' + str(logt) + '*' if logt!='all' else load_path_acc
    load_path_hist = glob.glob(load_path_hist)
    load_path_metr = glob.glob(load_path_metr)
    load_path_acc = glob.glob(load_path_acc)
    load_path_hist.sort(key=natural_keys)
    load_path_metr.sort(key=natural_keys)
    load_path_acc.sort(key=natural_keys)
    return load_path_hist, load_path_metr, load_path_acc

def get_dicts(query='days', logt='all', deflap=0):
    """Get Dicts

        Args:
         query: whether we are dealing in days or weeks
         logt: threshold of holds
         deflap: deficit/lapse

        Returns:
         returns the dictionaries with the training history and testing metrics
    """
    if query=='days':
        hist_dict, metr_dict, acc_dict = dict.fromkeys(['jump','keep']), dict.fromkeys(['jump','keep']), dict.fromkeys(['jump','keep'])
        hist_dict['jump'], hist_dict['keep'] = dict.fromkeys([1,2,3,4,5,6,7,8,9,10,11]), dict.fromkeys([1,2,3,4,5,6,7,8,9,10,11])
        metr_dict['jump'], metr_dict['keep'] = dict.fromkeys([1,2,3,4,5,6,7,8,9,10,11]), dict.fromkeys([1,2,3,4,5,6,7,8,9,10,11])
        acc_dict['jump'], acc_dict['keep'] = dict.fromkeys([1,2,3,4,5,6,7,8,9,10,11]), dict.fromkeys([1,2,3,4,5,6,7,8,9,10,11])
        for x in hist_dict['jump'].keys():
            hist_dict['jump'][x], hist_dict['keep'][x] = dict.fromkeys([1,2,3,4,5,6,7]), dict.fromkeys([1,2,3,4,5,6,7])
            metr_dict['jump'][x], metr_dict['keep'][x] = dict.fromkeys([1,2,3,4,5,6,7]), dict.fromkeys([1,2,3,4,5,6,7])
            acc_dict['jump'][x], acc_dict['keep'][x] = dict.fromkeys([1,2,3,4,5,6,7]), dict.fromkeys([1,2,3,4,5,6,7])
    else:
        hist_dict, metr_dict, acc_dict = dict.fromkeys(['keep']), dict.fromkeys(['keep']), dict.fromkeys(['keep'])
        hist_dict['keep'], metr_dict['keep'], acc_dict['keep'] = dict.fromkeys([x for x in range(1,29)]), dict.fromkeys([x for x in range(1,29)]), dict.fromkeys([x for x in range(1,29)])
        for x in hist_dict['keep'].keys():
            hist_dict['keep'][x], metr_dict['keep'][x], acc_dict['keep'][x] = dict.fromkeys([x for x in range(1,8)]), dict.fromkeys([x for x in range(1,8)]), dict.fromkeys([x for x in range(1,8)])
    load_path_hist, load_path_metr, load_path_acc = get_load_paths(query, logt, deflap)
    for file in load_path_hist:
        with open(file, 'rb') as f:
            txt = file.split('/')[-1:][0].split('\\')[-1:][0].split('.')[0].split('_')
            k1 = 'keep' if 'keep' in txt[1] else 'jump'
            k2 = int(txt[1].split(k1)[1])
            k3 = int(txt[2].split('threshold')[1])
            if k2!=24:
                hist_dict[k1][k2][k3] = pickle.load(f)
    for file in load_path_metr:
        with open(file, 'rb') as f:
            txt = file.split('/')[-1:][0].split('\\')[-1:][0].split('.')[0].split('_')
            k1 = 'keep' if 'keep' in txt[1] else 'jump'
            k2 = int(txt[1].split(k1)[1])
            k3 = int(txt[2].split('threshold')[1])
            if k2!=24:
                metr_dict[k1][k2][k3] = pickle.load(f)
    for file in load_path_acc:
        with open(file, 'rb') as f:
            txt = file.split('/')[-1:][0].split('\\')[-1:][0].split('.')[0].split('_')
            k1 = 'keep' if 'keep' in txt[1] else 'jump'
            k2 = int(txt[1].split(k1)[1])
            k3 = int(txt[2].split('threshold')[1])
            if k2!=24:
                acc_dict[k1][k2][k3] = pickle.load(f)
    return stripper(hist_dict), stripper(metr_dict), stripper(acc_dict)

def get_loss_names(hist_dict, query='days'):
    """Get Loss Name

        Args:
         hist_dict: the dict to check whether we have RMSE or binary accuracy
         query: whether days/weeks

        Returns:
         returns the loss name (long and short form) to be used when plotting.
    """
    if logt=='all':
        keys = hist_dict['jump'][1][1].keys() if query=='days' else hist_dict['keep'][7][1].keys()
    else:
        keys = hist_dict['jump'][1][logt].keys() if query=='days' else hist_dict['keep'][7][logt].keys()
    loss_name = 'root_mean_squared_error' if 'root_mean_squared_error' in keys else 'binary_accuracy'
    val_loss_name = 'val_'+loss_name
    loss_name_shrt = 'RMSE' if 'root_mean_squared_error' in keys else 'Acc'
    val_loss_name_shrt = 'val_RMSE' if 'root_mean_squared_error' in keys else 'val_Acc'
    return loss_name, val_loss_name, loss_name_shrt, val_loss_name_shrt

def plot_loss(hlist, title, txt, label_name):
    """Plot Loss

        Args:
            hlist: the list of 'histories' to plot
            title: the title of the plot
            txt: the xlabel
            label_name: RMSE/Accuracy

        Returns:
            The plot on screen
    """
    for hist in hlist:
        plt.plot(range(1, len(hist[0]) + 1), hist[0], label=hist[1]+' - '+label_name)
    plt.title(title)
    plt.xlabel(txt)
    plt.legend()
    plt.grid(True)
    plt.show()

def create_last_measure_plot_hist(query, dct, logt, loss_name, label_name):
    """Create Last Measurement Plot (History)

        Args:
         query: whether we are dealing in days or weeks
         dct: The dictionary
         logt: threshold of logs (1-7 or all)
         loss_name: Loss Name
         label_name: RMSE/Accuracy

        Returns:
         Creates a plot taking into account the last measurement.
    """
    title = 'TIC Days' if query=='days' else 'TIC Weeks'
    char = 'Training' if 'val' not in label_name else 'Validation'
    var_lst = ['keep','jump'] if query=='days' else ['keep']
    keep_history, jump_history, hlist = [], [], []
    if logt!='all':
        for var in var_lst:
            for key in dct[var].keys():
                if var=='keep': keep_history.append(dct[var][key][logt][loss_name][-1:])
                else: jump_history.append(dct['jump'][key][logt][loss_name][-1:])
        hlist.append([keep_history, 'Keep'])
        if query=='days': hlist.append([jump_history, 'Jump'])
        plot_loss(hlist, char + ' Results (Keep/Jump)', title, label_name)
    else:
        for var in var_lst:
            for key in dct[var].keys():
                tmp=[]
                for lg in dct[var][key].keys():
                    tmp.append(dct[var][key][lg][loss_name][-1:])
                if var=='keep': keep_history.append(tmp)
                else: jump_history.append(tmp)
            if var=='keep':
                for i in range(0, len(keep_history)):
                    hlist.append([keep_history[i],'Keep-'+str(i+1)])
                plot_loss(hlist, char + ' Results (Keep/Threshold)', 'Log Threshold', label_name)
                hlist=[]
            else:
                for i in range(0, len(jump_history)):
                    hlist.append([jump_history[i],'Jump-'+str(i+1)])
                plot_loss(hlist, char + ' Results (Jump/Threshold)', 'Log Threshold', label_name)
            ###################################################################
            keep_history, jump_history, hlist = [], [], []
            for lg in range(1,8):
                tmp=[]
                for key in dct[var].keys():
                    tmp.append(dct[var][key][lg][loss_name][-1:])
                if var=='keep': keep_history.append(tmp)
                else: jump_history.append(tmp)
            if var=='keep':
                for i in range(0, len(keep_history)):
                    hlist.append([keep_history[i],'Keep-'+str(i+1)])
                plot_loss(hlist, char + ' Results (Keep/TIC)', title, label_name)
                hlist=[]
            else:
                for i in range(0, len(jump_history)):
                    hlist.append([jump_history[i],'Jump-'+str(i+1)])
                plot_loss(hlist, char + ' Results (Jump/TIC)', title, label_name)

def create_last_measure_plot_metr(query, dct, logt, label_name):
    """Create Last Measurement Plot (Metrics)

        Args:
         query: whether we are dealing in days or weeks
         dct: The dictionary
         logt: threshold of logs (1-7 or all)
         label_name: RMSE/Accuracy

        Returns:
         Creates a plot taking into account the last measurement.
    """
    title = 'TIC Days' if query=='days' else 'TIC Weeks'
    var_lst = ['keep','jump'] if query=='days' else ['keep']
    keep_metrics, jump_metrics, hlist = [], [], []
    if logt!='all':
        for var in var_lst:
            for key in dct[var].keys():
                if var=='keep': keep_metrics.append(dct[var][key][logt][loss_name])
                else: jump_metrics.append(dct['jump'][key][logt][loss_name])
        hlist.append([keep_metrics, 'Keep'])
        if query=='days': hlist.append([jump_metrics, 'Jump'])
        plot_loss(hlist, 'Testing Results (Keep/Jump)', title, label_name)
    else:
        for var in var_lst:
            for key in dct[var].keys():
                tmp=[]
                for lg in dct[var][key].keys():
                    tmp.append(dct[var][key][lg][loss_name])
                if var=='keep': keep_metrics.append(tmp)
                else: jump_metrics.append(tmp)
            if var=='keep':
                for i in range(0, len(keep_metrics)):
                    hlist.append([keep_metrics[i],'Keep-'+str(i+1)])
                plot_loss(hlist, 'Testing Results (Keep/Threshold)', 'Log Threshold', label_name)
                hlist=[]
            else:
                for i in range(0, len(jump_metrics)):
                    hlist.append([jump_metrics[i],'Jump-'+str(i+1)])
                plot_loss(hlist, 'Testing Results (Jump/Threshold)', 'Log Threshold', label_name)
            ###################################################################
            keep_metrics, jump_metrics, hlist = [], [], []
            for lg in range(1,8):
                tmp=[]
                for key in dct[var].keys():
                    tmp.append(dct[var][key][lg][loss_name])
                if var=='keep': keep_metrics.append(tmp)
                else: jump_metrics.append(tmp)
            if var=='keep':
                for i in range(0, len(keep_metrics)):
                    hlist.append([keep_metrics[i],'Keep-'+str(i+1)])
                plot_loss(hlist, 'Testing Results (Keep/TIC)', title, label_name)
                hlist=[]
            else:
                for i in range(0, len(jump_metrics)):
                    hlist.append([jump_metrics[i],'Jump-'+str(i+1)])
                plot_loss(hlist, 'Testing Results (Jump/TIC)', title, label_name)

def create_size_plots(r, names, title):
    """Create Size Plots

        Args:
         r: the DataFrames to plot in list form
         names: the labels to name the above
         title: the title indicating DataFrame Size or DataFrame User Size

        Returns:
         Creates plots concerning DataFrame Size and DataFrame User Size
    """
    labels = names
    width = 0.142
    size = [x.shape[0] for x in r]
    size_0, size_1, size_2, size_3, size_4, size_5, size_6 = [], [], [], [], [], [], []
    for i in range(1, len(size)+1):
        if i%7==1: size_0.append(size[i-1])
        elif i%7==2: size_1.append(size[i-1])
        elif i%7==3: size_2.append(size[i-1])
        elif i%7==4: size_3.append(size[i-1])
        elif i%7==5: size_4.append(size[i-1])
        elif i%7==6: size_5.append(size[i-1])
        elif i%7==0: size_6.append(size[i-1])
    fig, ax = plt.subplots()
    x = np.arange(len(labels))  # the label locations
    ax.bar(x - 3*width, size_0, width, label='T1')
    ax.bar(x - 2*width, size_1, width, label='T2')
    ax.bar(x - 1*width, size_2, width, label='T3')
    ax.bar(x + 0*width, size_3, width, label='T4')
    ax.bar(x + 1*width, size_4, width, label='T5')
    ax.bar(x + 2*width, size_5, width, label='T6')
    ax.bar(x + 3*width, size_6, width, label='T7')
    ax.set_ylabel("DataFrame Size (Rows)")
    ax.set_xlabel("TIC Days + LogT")
    ax.set_title("Sizes of "+title+" DataFrames")
    ax.set_xticks(x, labels)
    ax.legend()
    #ax.bar_label(rects0, padding=3) #ax.bar_label(rects1, padding=3) #ax.bar_label(rects2, padding=3) #ax.bar_label(rects3, padding=3) #ax.bar_label(rects4, padding=3) #ax.bar_label(rects5, padding=3) #ax.bar_label(rects6, padding=3) 
    fig.tight_layout()
    plt.show()
    ####
    size = [x.USER_ID.nunique() for x in r]
    size_0, size_1, size_2, size_3, size_4, size_5, size_6 = [], [], [], [], [], [], []
    for i in range(1, len(size)+1):
        if i%7==1: size_0.append(size[i-1])
        elif i%7==2: size_1.append(size[i-1])
        elif i%7==3: size_2.append(size[i-1])
        elif i%7==4: size_3.append(size[i-1])
        elif i%7==5: size_4.append(size[i-1])
        elif i%7==6: size_5.append(size[i-1])
        elif i%7==0: size_6.append(size[i-1])
    fig, ax = plt.subplots()
    x = np.arange(len(labels))  # the label locations
    ax.bar(x - 3*width, size_0, width, label='T1')
    ax.bar(x - 2*width, size_1, width, label='T2')
    ax.bar(x - 1*width, size_2, width, label='T3')
    ax.bar(x + 0*width, size_3, width, label='T4')
    ax.bar(x + 1*width, size_4, width, label='T5')
    ax.bar(x + 2*width, size_5, width, label='T6')
    ax.bar(x + 3*width, size_6, width, label='T7')
    ax.set_ylabel("User Size (Rows)")
    ax.set_xlabel("TIC Days + LogT")
    ax.set_title("User Sizes of "+title+" DataFrames")
    ax.set_xticks(x, labels)
    ax.legend()
    #ax.bar_label(rects0, padding=3) #ax.bar_label(rects1, padding=3) #ax.bar_label(rects2, padding=3) #ax.bar_label(rects3, padding=3) #ax.bar_label(rects4, padding=3) #ax.bar_label(rects5, padding=3) #ax.bar_label(rects6, padding=3) 
    fig.tight_layout()
    plt.show()

def create_days_dataset_size_plots(query='days'):
    """Create Dataset Size Plots Days

        Returns:
         Creates plots of datasets on days->day variation
    """
    main_path = '_obsolete/ml/data/automated_dataframes_for_invrec/' if query=='days' else '_obsolete/ml/data/automated_dataframes_for_weekly_invrec/'
    load_path = main_path+'/*_reg' if query=='days' else main_path+'/weekly_regtest*'
    load_path = glob.glob(load_path)
    load_path.sort(key=natural_keys)
    keep_files = [x for x in load_path if 'keep' in x.split('\\')[1].split('_')[0]] if query=='days' else [x for x in load_path]
    rk = [pd.read_pickle(x, compression='gzip') for x in keep_files]
    labels = ['D1','D2','D3','D4','D5','D6','D7','D8','D9','D10','D11'] if query=='days' else ['W1','W2','W3','W4']
    create_size_plots(rk, labels, 'Keep')
    if query=='days': 
        jump_files = [x for x in load_path if 'jump' in x.split('\\')[1].split('_')[0]]
        rj = [pd.read_pickle(x, compression='gzip') for x in jump_files]
        create_size_plots(rj, labels, 'Jump')

def create_accuracy_plots(query, dct, logt, mbd='', label_name='RMSE'):
    """Create Accuracy Plots

        Args:
         query: whether we are dealing in days or weeks
         dct: The dictionary
         logt: threshold of logs (1-7 or all)
         label_name: RMSE/Accuracy

        Returns:
         Creates a plot taking into account the last measurement.
    """
    while mbd=='':
        try:
            mbd = str(input('[Model, Baseline, Difference] Which type would you like to see?: '))
            if mbd!='Model' and mbd!='Baseline' and mbd!='Difference': raise ValueError 
            break
        except ValueError:
            print("Wrong input, please try again...")  
            continue
    title = 'TIC Days' if query=='days' else 'TIC Weeks'
    var_lst = ['keep','jump'] if query=='days' else ['keep']
    keep_accuracy, jump_accuracy, hlist = [], [], []
    if logt!='all':
        for var in var_lst:
            for key in dct[var].keys():
                if var=='keep': keep_accuracy.append(dct[var][key][logt][mbd])
                else: jump_accuracy.append(dct['jump'][key][logt][mbd])
        hlist.append([keep_accuracy, 'Keep'])
        if query=='days': hlist.append([jump_accuracy, 'Keep'])
        plot_loss(hlist, 'Accuracy (Keep/Jump)', title, label_name)
    else:
        for var in var_lst:
            for key in dct[var].keys():
                tmp=[]
                for lg in dct[var][key].keys():
                    tmp.append(dct[var][key][lg][mbd])
                if var=='keep': keep_accuracy.append(tmp)
                else: jump_accuracy.append(tmp)
            if var=='keep':
                for i in range(0, len(keep_accuracy)):
                    hlist.append([keep_accuracy[i],'Keep-'+str(i+1)])
                plot_loss(hlist, 'Accuracy (Keep/Threshold)', 'Log Threshold', label_name)
                hlist=[]
            else:
                for i in range(0, len(jump_accuracy)):
                    hlist.append([jump_accuracy[i],'Jump-'+str(i+1)])
                plot_loss(hlist, 'Accuracy (Jump/Threshold)', 'Log Threshold', label_name)
            ###################################################################
            keep_accuracy, jump_accuracy, hlist = [], [], []
            for lg in range(1,8):
                tmp=[]
                for key in dct[var].keys():
                    tmp.append(dct[var][key][lg][mbd])
                if var=='keep': keep_accuracy.append(tmp)
                else: jump_accuracy.append(tmp)
            if var=='keep':
                for i in range(0, len(keep_accuracy)):
                    hlist.append([keep_accuracy[i],'Keep-'+str(i+1)])
                plot_loss(hlist, 'Accuracy (Keep/TIC)', title, label_name)
                hlist=[]
            else:
                for i in range(0, len(jump_accuracy)):
                    hlist.append([jump_accuracy[i],'Jump-'+str(i+1)])
                plot_loss(hlist, 'Accuracy (Jump/TIC)', title, label_name)

def create_all_plots_by(query, dct, logt, loss_name='root_mean_squared_error', label_name='RMSE'):
    """Create All Plots (Training)

        Args:
         query: whether we are dealing in days or weeks
         dct: The dictionary
         logt: threshold of logs (1-7 or all)
         loss_name: Loss Name
         label_name: RMSE/Accuracy

        Returns:
         Creates all plots
    """
    title = 'TIC Days' if query=='days' else 'TIC Weeks'
    char = 'Training' if 'val' not in label_name else 'Validation'
    var_lst = ['keep','jump'] if query=='days' else ['keep']
    query_range = range(1,12) if query=='days' else range(7,29,7)
    keep_history, jump_history, hlist = [], [], []
    if logt!='all':
        for k1 in query_range:
            for var in var_lst:
                for i in range(1, len(dct[var][k1][logt][loss_name])):
                    if var=='keep': keep_history.append(dct[var][k1][logt][loss_name][i])
                    else: jump_history.append(dct[var][k1][logt][loss_name][i])
            hlist.append([keep_history, 'Keep'])
            if query=='days': hlist.append([jump_history, 'Jump'])
            plot_loss(hlist, char + ' Results Days='+str(k1)+' ,LogT='+str(logt), 'Epochs', label_name)
            keep_history, jump_history, hlist = [], [], []
    else:
        for k1 in query_range:
            for var in var_lst:
                tmp=[]
                for lg in dct[var][k1].keys():
                    tmp.append(dct[var][k1][lg][loss_name][1:])
                if var=='keep': keep_history.append(tmp)
                else: jump_history.append(tmp)
        for i in range(0, len(keep_history)):
            hlist=[]
            for j in range(0, len(keep_history[i])):
                hlist.append([keep_history[i][j], 'LogT-'+str(j+1)])
            plot_loss(hlist, char + ' Results Keep-'+str(i+1)+'/Epochs', 'Epochs', label_name)
        if query=='days':
            for i in range(0, len(jump_history)):
                hlist=[]
                for j in range(0, len(jump_history[i])):
                    hlist.append([jump_history[i][j], 'LogT-'+str(j+1)])
                plot_loss(hlist, char + ' Results Jump-'+str(i+1)+'/Epochs', 'Epochs', label_name)

def create_val_on_train_plots_by(query, dct, logt):
    """Create All Plots (Training)

        Args:
         query: whether we are dealing in days or weeks
         dct: The dictionary
         logt: threshold of logs (1-7 or all)

        Returns:
         Creates all plots
    """
    title = 'TIC Days' if query=='days' else 'TIC Weeks'
    var_lst = ['keep','jump'] if query=='days' else ['keep']
    query_range = range(1,12) if query=='days' else range(7,29,7)
    keep_history, jump_history, vkeep_history, vjump_history, hlist = [], [], [], [], []
    if logt!='all':
        for k1 in query_range:
            for var in var_lst:
                for i in range(1, len(dct[var][k1][logt][loss_name])):
                    if var=='keep': 
                        keep_history.append(dct[var][k1][logt][loss_name][i])
                        vkeep_history.append(dct[var][k1][logt][val_loss_name][i])
                    else: 
                        jump_history.append(dct[var][k1][logt][loss_name][i])
                        vjump_history.append(dct[var][k1][logt][val_loss_name][i])
            hlist.append([keep_history, 'KeepT'])
            hlist.append([vkeep_history, 'KeepV'])
            if query=='days': 
                hlist.append([jump_history, 'JumpT'])
                hlist.append([vjump_history, 'JumpV'])
            plot_loss(hlist, 'Training Results Days='+str(k1)+' ,LogT='+str(logt), 'Epochs', loss_name_shrt)
            keep_history, jump_history, vkeep_history, vjump_history, hlist = [], [], [], [], []
    else:
        for k1 in query_range:
            for var in var_lst:
                tmp,vtmp=[],[]
                for lg in dct[var][k1].keys():
                    tmp.append(dct[var][k1][lg][loss_name][1:])
                    vtmp.append(dct[var][k1][lg][val_loss_name][1:])
                if var=='keep': 
                    keep_history.append(tmp)
                    vkeep_history.append(vtmp)
                else: 
                    jump_history.append(tmp)
                    vjump_history.append(vtmp)
        for i in range(0, len(keep_history)):
            hlist=[]
            for j in range(0, len(keep_history[i])):
                hlist.append([keep_history[i][j], 'Train - LogT-'+str(j+1)])
                hlist.append([vkeep_history[i][j], 'Val - LogT-'+str(j+1)])
            plot_loss(hlist, 'Train/Val Results Keep-'+str(i+1)+'/Epochs', 'Epochs', loss_name_shrt)
        if query=='days':
            for i in range(0, len(jump_history)):
                hlist=[]
                for j in range(0, len(jump_history[i])):
                    hlist.append([jump_history[i][j], 'Train - LogT-'+str(j+1)])
                    hlist.append([vjump_history[i][j], 'Val - LogT-'+str(j+1)])
                plot_loss(hlist, 'Train/Val Results Jump-'+str(i+1)+'/Epochs', 'Epochs', loss_name_shrt)

def print_testing_results(query, dct, logt, label_name):
    """Print Testing Results

        Args:
         query: whether we are dealing in days or weeks
         dct: The dictionary
         logt: threshold of logs (1-7 or all)
         label_name: Label Name

        Returns:
         Prints results of testing
    """
    var_lst = ['keep','jump'] if query=='days' else ['keep']
    if logt!='all':
        for var in var_lst:
            ind = 'K' if var=='keep' else 'J'
            for k1 in dct[var].keys():
                print('Testing '+label_name+' for '+ind+('-')+str(k1)+' & LogT-'+str(logt)+':', round(dct[var][k1][logt][loss_name],3))
    else:
        print('Testing '+label_name+' for:')
        pr=[]
        for var in var_lst:
            for k1 in dct[var].keys():
                for lg in dct[var][k1].keys():
                    ind = 'K' if var=='keep' else 'J'
                    pr.append(ind+str(k1)+'L'+str(lg)+': ' + (str(round(dct[var][k1][lg][loss_name],2))+'0')[:4])
        print(*pr, sep=' ')

def print_regularization_loss_results(query, dct, logt, label_name):
    """Print Regularization Loss

        Args:
         query: whether we are dealing in days or weeks
         dct: The dictionary
         logt: threshold of logs (1-7 or all)
         label_name: Label Name

        Returns:
         Prints results of testing
    """
    var_lst = ['keep','jump'] if query=='days' else ['keep']
    if logt!='all':
        for var in var_lst:
            ind = 'K' if var=='keep' else 'J'
            for k1 in dct[var].keys():
                print(ind+str(k1)+'L'+str(logt)+':')
                print('  Loss:', round(dct[var][k1][logt]['loss'][-1],3))
                print('  Reg.Loss:', round(dct[var][k1][logt]['regularization_loss'][-1],3))
                print('    Perc. (%):', 100*round(dct[var][k1][logt]['regularization_loss'][-1]/dct[var][k1][logt]['loss'][-1], 4))
    else:
        while True:
            try:
                th = int(input('  [0, x] Print Percentages Below Threshold?: '))
                if th<0: raise ValueError 
                break
            except ValueError:
                print("  Wrong input, please try again...")  
                continue
        print('Regularization over Training Loss Percentage (%) - '+label_name+':')
        if th==0: th=10000
        pr=[]
        for var in var_lst:
            for k1 in dct[var].keys():
                for lg in dct[var][k1].keys():
                    ind = 'K' if var=='keep' else 'J'
                    perdiff= 100*(dct[var][k1][lg]['regularization_loss'][-1]/dct[var][k1][lg]['loss'][-1])
                    if perdiff<=th: pr.append(ind+str(k1)+'L'+str(lg)+': ' + (str(round(perdiff,2))+'0')[:4])
        print(*pr, sep=' ')

while True:
  try:
    query = str(input('[days, weeks] Which type would you like to see?: '))
    if query!='days' and query!='weeks' and query!='': raise ValueError 
    break
  except ValueError:
      print("Wrong input, please try again...")  
      continue
while True:
  try:
    logt = str(input('[all, 1-7] Desired Log Threshold?: '))
    if logt!='all' and logt!='' and (int(logt)<1 or int(logt)>7): raise ValueError 
    break
  except ValueError:
      print("Wrong input, please try again...")  
      continue
while True:
  try:
    deflap = str(input('[0, 1] Deficit/Lapse sets?: '))
    if deflap!='0' and deflap!='1' and deflap!='': raise ValueError 
    break
  except ValueError:
      print("Wrong input, please try again...")  
      continue
print('Setting Parameters and preparing Dictionaries')
query, logt, deflap = validate_parameters(query, logt, deflap)
hist_dict, metr_dict, acc_dict = get_dicts(query, logt, deflap)
loss_name, val_loss_name, loss_name_shrt, val_loss_name_shrt = get_loss_names(hist_dict, query)
print("[1] Last Measurement Plot\n[2] Accuracy Plots\n[3] DataFrame Size plots\n[4] Validation on Training Plots\n[5] All Training Plots\n[6] Testing Results\n[7] Regularization Results\n[0] Quit")
while True:
  try:
    ch = int(input('[0-7] Enter your choice: '))
    if ch>7 or ch<0: raise ValueError 
  except ValueError:
      print("Wrong input, please try again...")  
      continue
  if ch==1: 
    while True:
        try:
            lsn = int(input('  [0, 1, 2] Training/Validation/Test Loss?: '))
            if lsn!=1 and lsn!=0 and lsn!=2: raise ValueError 
            break
        except ValueError:
            print("  Wrong input, please try again...")  
            continue
    create_last_measure_plot_hist(query, hist_dict, logt, loss_name, loss_name_shrt) if lsn==0 else create_last_measure_plot_hist(query, hist_dict, logt, val_loss_name, val_loss_name_shrt) if lsn==1 else create_last_measure_plot_metr(query, metr_dict, logt, loss_name_shrt)
  elif ch==2: create_accuracy_plots(query, acc_dict, logt, '', loss_name_shrt)
  elif ch==3: create_days_dataset_size_plots(query)
  elif ch==4: create_val_on_train_plots_by(query, hist_dict, logt)
  elif ch==5: 
    while True:
        try:
            lsn = int(input('  [0, 1] Training/Validation Loss?: '))
            if lsn!=1 and lsn!=0: raise ValueError 
            break
        except ValueError:
            print("  Wrong input, please try again...")  
            continue
    create_all_plots_by(query, hist_dict, logt, loss_name, loss_name_shrt) if lsn==0 else create_all_plots_by(query, hist_dict, logt, val_loss_name, val_loss_name_shrt)
  elif ch==6: print_testing_results(query, metr_dict, logt, loss_name_shrt)
  elif ch==7: print_regularization_loss_results(query, hist_dict, logt, loss_name_shrt)
  else: break