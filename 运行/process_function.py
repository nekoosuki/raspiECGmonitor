# -*- coding: utf-8 -*-

import numpy as np
import heartpy as hp


def insert_avg_3(v: np.ndarray) -> np.ndarray:
    v = v.flatten()
    size = v.size
    ndata = np.zeros(3*size)
    for i in range(size):
        ndata[3*i] = v[i]
    for i in range(size-1):
        ndata[3*i+1] = v[i]+(v[i+1]-v[i])/3
        ndata[3*i+2] = v[i]+(v[i+1]-v[i])*2/3
    return ndata


def insert_avg_2(v: np.ndarray) -> np.ndarray:
    v = v.flatten()
    size = v.size
    ndata = np.zeros(2*size)
    for i in range(size):
        ndata[2*i] = v[i]
    for i in range(size-1):
        ndata[2*i+1] = (ndata[2*i]+ndata[2*(i+1)])/2
    return ndata


def normalize(v: np.ndarray) -> np.ndarray:
    return (v-v.min())/(v.max()-v.min())


def norm_filt(v: np.ndarray, fs: int) -> np.ndarray:
    v_rmbs = hp.filter_signal(v, 0.01, fs, filtertype='notch')
    v_norm = normalize(v_rmbs)
    v_filt = hp.filter_signal(v_norm, [0.18, 15], fs, filtertype='bandpass')
    return v_filt
