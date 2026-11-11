"""Offline signal-quality features; NOT emotion/memory/identity decoding. EDF optional MNE dependency."""
from __future__ import annotations
import numpy as np
from scipy.signal import welch

def spectral_quality(x, fs):
  v=np.asarray(x,dtype=float)
  if v.ndim!=1 or not 100<=len(v) or fs<40 or not np.all(np.isfinite(v)):
    raise ValueError('invalid mono sensor window')
  f,p=welch(v,fs,nperseg=min(len(v),int(fs*2)))
  def area(a,b):
    m=(f>=a)&(f<b)
    if np.sum(m)==0:return 0.0
    return float(np.trapezoid(p[m],f[m]))
  alpha=area(8,13);beta=area(13,30)
  peak=float(f[np.argmax(p[(f>=4)&(f<35)])+np.where(f>=4)[0][0]])
  clipping=float(np.mean(np.abs(v)>=.999*np.max(np.abs(v)))) if np.max(np.abs(v)) else 1.0
  return {'alpha_power':alpha,'beta_power':beta,'peak_hz':peak,'clipping_proxy':clipping,'emotion_label':None,'belief_label':None}

def read_edf_features(edf_path):
  import mne
  raw=mne.io.read_raw_edf(edf_path,preload=False,verbose=False)
  x=raw.get_data(picks='eeg',start=0,stop=min(raw.n_times,int(raw.info['sfreq']*4)))
  if x.size==0:raise ValueError('no EEG channel')
  return spectral_quality(np.mean(x,axis=0),raw.info['sfreq'])
