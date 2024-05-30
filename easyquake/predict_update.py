#! /bin/env python
# Automatic picking of seismic waves using Generalized Phase Detection 
# See http://scedc.caltech.edu/research-tools/deeplearning.html for more info
#
# Ross et al. (2018), Generalized Seismic Phase Detection with Deep Learning,
#                     Bull. Seismol. Soc. Am., doi:10.1785/0120180080
#                                              
# Author: Zachary E. Ross (2018)                
# Contact: zross@gps.caltech.edu                        
# Website: http://www.seismolab.caltech.edu/ross_z.html         
from obspy.signal.trigger import trigger_onset
import argparse as ap
#import sys
import os
import numpy as np
import obspy.core as oc
#import keras
#from keras.models import Sequential
#from keras.layers import Dense, Dropout, Activation, Flatten
#from keras.layers import Conv1D, MaxPooling1D
#from keras import losses
from keras.models import model_from_json
import tensorflow as tf
#import tensorflow.keras.backend as K
#import matplotlib as mpl
#import pylab as plt
#mpl.rcParams['pdf.fonttype'] = 42

from numpy.random import random_integers as ranID
import datetime

#####################
# Hyperparameters
min_proba = 0.95 # Minimum softmax probability for phase detection
freq_min = 3.0
freq_max = 20.0
filter_data = True
decimate_data = True # If false, assumes data is already 100 Hz samprate
n_shift = 10 # Number of samples to shift the sliding window at a time
n_gpu = 1 # Number of GPUs to use (if any)
#####################
batch_size = 32*3

half_dur = 2.00
only_dt = 0.01
n_win = int(half_dur/only_dt)
n_feat = 2*n_win

IDCODE='echon'
#-------------------------------------------------------------

def sliding_window(data, size, stepsize=1, padded=False, axis=-1, copy=True):
    """
    Calculate a sliding window over a signal
    Parameters
    ----------
    data : numpy array
        The array to be slided over.
    size : int
        The sliding window size
    stepsize : int
        The sliding window stepsize. Defaults to 1.
    axis : int
        The axis to slide over. Defaults to the last axis.
    copy : bool
        Return strided array as copy to avoid sideffects when manipulating the
        output array.
    Returns
    -------
    data : numpy array
        A matrix where row in last dimension consists of one instance
        of the sliding window.
    Notes
    -----
    - Be wary of setting `copy` to `False` as undesired sideffects with the
      output values may occurr.
    Examples
    --------
    >>> a = numpy.array([1, 2, 3, 4, 5])
    >>> sliding_window(a, size=3)
    array([[1, 2, 3],
           [2, 3, 4],
           [3, 4, 5]])
    >>> sliding_window(a, size=3, stepsize=2)
    array([[1, 2, 3],
           [3, 4, 5]])
    See Also
    --------
    pieces : Calculate number of pieces available by sliding
    """
    if axis >= data.ndim:
        raise ValueError(
            "Axis value out of range"
        )

    if stepsize < 1:
        raise ValueError(
            "Stepsize may not be zero or negative"
        )

    if size > data.shape[axis]:
        raise ValueError(
            "Sliding window size may not exceed size of selected axis"
        )

    shape = list(data.shape)
    shape[axis] = np.floor(data.shape[axis] / stepsize - size / stepsize + 1).astype(int)
    shape.append(size)

    strides = list(data.strides)
    strides[axis] *= stepsize
    strides.append(data.strides[axis])

    strided = np.lib.stride_tricks.as_strided(
        data, shape=shape, strides=strides
    )

    if copy:
        return strided.copy()
    else:
        return strided

if __name__ == "__main__":
    parser = ap.ArgumentParser(
        prog='gpd_predict.py',
        description='Automatic picking of seismic waves using'
                    'Generalized Phase Detection')
    parser.add_argument(
        '-F',
        type=str,
        default=None,
        help='Input list of wave directories')
#    parser.add_argument(
#        '-I',
#        type=str,
#        default=None,
#        help='Input file')
#    parser.add_argument(
#        '-O',
#        type=str,
#        default=None,
#        help='Output file')
#    parser.add_argument(
#        '-P',
#        default=True,
#        action='store_false',
#        help='Suppress plotting output')
    parser.add_argument(
        '-V',
        default=False,
        action='store_true',
        help='verbose')
    args = parser.parse_args()

#    plot = args.P
    ffdir = []
    wdirf=os.path.join('/Users/echon/Desktop/python_scripts/neic_internship/data4')
    with open(args.F) as ff:
        for line in ff:
            tmpf = line.split()
            ffdir.append([tmpf[0]])
    ndir = len(ffdir)
    for ii in range(ndir):
        base_name = ffdir[ii][0]
        print ("%s" % base_name)
        print ("Current date/time: %s" % datetime.datetime.now()) 
        inDir = os.path.join(wdirf,base_name)
#            if not os.path.isfile(inDir):
#                print("%s doesn't exist, skipping" % ffdir[ii][0])
#                continue
        inName = base_name + '.input'
        inFile = os.path.join(inDir,inName)
        if not os.path.isfile(inFile):
            print("%s doesn't exist, skipping" % inFile)
            continue
        outName = base_name + '.output'
        outFile = os.path.join(inDir,outName)
        # Reading in input file
        fdir = []
        evid = []
        staid = []
        with open(inFile) as f:
            for line in f:
                tmp = line.split()
                full1 = os.path.join(inDir,tmp[0])
                full2 = os.path.join(inDir,tmp[1])
                full3 = os.path.join(inDir,tmp[2])
                #fdir.append([tmp[0], tmp[1], tmp[2]])
                fdir.append([full1, full2, full3])
        nsta = len(fdir)
#            config=tf.ConfigProto( intra_op_parallelism_threads=15,inter_op_parallelism_threads=15)
#            config.gpu_options.allow_growth = True
#            config.gpu_options.per_process_gpu_memory_fraction = 0.95
#            config.gpu_options.visible_device_list= '0'
#            config = tf.ConfigProto(device_count={'GPU':1, 'CPU':4})
#            with tf.Session(config=config) as sess:
#            K.set_session(sess)
        # load json and create model
        json_file = open('model_pol.json', 'r')
        loaded_model_json = json_file.read()
        json_file.close()
        model = model_from_json(loaded_model_json, custom_objects={'tf':tf})
        #model = model_from_json(loaded_model_json)
    
        # load weights into new model
        model.load_weights("model_pol_best.hdf5")
        print("Loaded model from disk")
    
#        if n_gpu > 1:
#            from keras.utils import multi_gpu_model
#            model = multi_gpu_model(model, gpus=n_gpu)
    
        ofile = open(outFile, 'w')
        st = []
        for i in range(nsta):
            del st
            fname = fdir[i][0].split("/")
            if not os.path.isfile(fdir[i][0]):
                print("%s doesn't exist, skipping" % fdir[i][0])
                continue
            if not os.path.isfile(fdir[i][1]):
                print("%s doesn't exist, skipping" % fdir[i][1])
                continue
            if not os.path.isfile(fdir[i][2]):
                print("%s doesn't exist, skipping" % fdir[i][2])
                continue
            st = oc.Stream()
            st += oc.read(fdir[i][0])
            st += oc.read(fdir[i][1])
            st += oc.read(fdir[i][2])
            latest_start = np.max([x.stats.starttime for x in st])
            earliest_stop = np.min([x.stats.endtime for x in st])
            if latest_start > earliest_stop:
                print("%s: startime is larger than endtime, skipping" % st[0].stats.station)
                continue
            st.trim(latest_start, earliest_stop)
            sr_0 = st[0].stats.sampling_rate
    
            st.detrend(type='linear')
            if filter_data:
                st.filter(type='bandpass', freqmin=freq_min, freqmax=freq_max)
            if decimate_data:
                st.interpolate(100.0)
            sr = st[0].stats.sampling_rate
            dt = st[0].stats.delta
            net = st[0].stats.network
            sta = st[0].stats.station
            chan = st[0].stats.channel
            loc = st[0].stats.location
            if loc=="":
                loc="__"
            if args.V:
                print("Reshaping data matrix for sliding window")
            tt = (np.arange(0, st[0].data.size, n_shift) + n_win) * dt
            tt_i = np.arange(0, st[0].data.size, n_shift) + n_feat
            #tr_win = np.zeros((tt.size, n_feat, 3))
            try:
                sliding_N = sliding_window(st[0].data, n_feat, stepsize=n_shift)
            except (ValueError):
                print("ValueError raised, skipping")
                continue
            try:
                sliding_E = sliding_window(st[1].data, n_feat, stepsize=n_shift)
            except (ValueError):
                print("ValueError raised, skipping")
                continue
            try:
                sliding_Z = sliding_window(st[2].data, n_feat, stepsize=n_shift)
            except (ValueError):
                print("ValueError raised, skipping")
                continue
            tr_win = np.zeros((sliding_N.shape[0], n_feat, 3))
            tr_win[:,:,0] = sliding_N
            tr_win[:,:,1] = sliding_E
            tr_win[:,:,2] = sliding_Z
            tr_win = tr_win / np.max(np.abs(tr_win), axis=(1,2))[:,None,None]
            tt = tt[:tr_win.shape[0]]
            tt_i = tt_i[:tr_win.shape[0]]
    
            if args.V:
                ts = model.predict(tr_win, verbose=True, batch_size=batch_size)
            else:
                ts = model.predict(tr_win, verbose=False, batch_size=batch_size)
            prob_S = ts[:,1]
            prob_P = ts[:,0]
            prob_N = ts[:,2]
    
#            from obspy.signal.trigger import trigger_onset
            trigs = trigger_onset(prob_P, min_proba, 0.1)
            p_picks = []
            s_picks = []
            for trig in trigs:
                if trig[1] == trig[0]:
                    continue
                pick = np.argmax(ts[trig[0]:trig[1], 0])+trig[0]
                stamp_pick = st[0].stats.starttime + tt[pick]
                
                pickProbP=prob_P[pick]
                pickProbS=prob_S[pick]
                pickProbN=prob_N[pick]
                
                rid = ranID(low=999999999999999,high=None,size=None)
                rid = IDCODE+str(rid)
                
                p_picks.append(stamp_pick)
                ofile.write("%s %s %s %s %d P %s %f %f %f %s\n" \
                            % (net, sta, chan, loc, sr_0, stamp_pick.isoformat(), \
                               pickProbP, pickProbS, pickProbN, rid))
    
            trigs = trigger_onset(prob_S, min_proba, 0.1)
            for trig in trigs:
                if trig[1] == trig[0]:
                    continue
                pick = np.argmax(ts[trig[0]:trig[1], 1])+trig[0]
                stamp_pick = st[0].stats.starttime + tt[pick]
                
                pickProbP=prob_P[pick]
                pickProbS=prob_S[pick]
                pickProbN=prob_N[pick]
                
                rid = ranID(low=999999999999999,high=None,size=None)
                rid = IDCODE+str(rid)
                
                s_picks.append(stamp_pick)
                ofile.write("%s %s %s %s %d S %s %f %f %f %s\n" \
                            % (net, sta, chan, loc, sr_0, stamp_pick.isoformat(), \
                               pickProbP, pickProbS, pickProbN, rid))
    
#            if plot:
#                fig = plt.figure(figsize=(8, 8))
#                ax = []
#                ax.append(fig.add_subplot(4,1,1))
#                ax.append(fig.add_subplot(4,1,2,sharex=ax[0],sharey=ax[0]))
#                ax.append(fig.add_subplot(4,1,3,sharex=ax[0],sharey=ax[0]))
#                ax.append(fig.add_subplot(4,1,4,sharex=ax[0]))
#                for i in range(3):
#                    ax[i].plot(np.arange(st[i].data.size)*dt, st[i].data, c='k', \
#                               lw=0.5)
#                ax[3].plot(tt, ts[:,0], c='r', lw=0.5)
#                ax[3].plot(tt, ts[:,1], c='b', lw=0.5)
#                for p_pick in p_picks:
#                    for i in range(3):
#                        ax[i].axvline(p_pick-st[0].stats.starttime, c='r', lw=0.5)
#                for s_pick in s_picks:
#                    for i in range(3):
#                        ax[i].axvline(s_pick-st[0].stats.starttime, c='b', lw=0.5)
#                plt.tight_layout()
#                plt.show()
#                #file_name = str(st[0].stats.station)
#                #tmp=str(file_name+'.pickle')
#                #dill.dump(plt, open(tmp,'w'),protocol=None)
        ofile.close()
