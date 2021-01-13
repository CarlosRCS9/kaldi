#!/usr/bin/env python3
# Copyright 2021 Carlos Castillo
#
# Apache 2.0

import numpy as np

class Wav_scp:
  def __init__(self, data):
    if isinstance(data, str):
      line = data.strip()
      recording_id, wav = line.split(' ', 1)
      self.recording_id = recording_id
      self.wav = wav

class Utt2dur:
  def __init__(self, data):
    if isinstance(data, str):
      line = data.strip()
      utterance, duration = line.split(' ')
      duration = np.float32(duration)
      self.utterance = utterance
      self.duration = duration
  def get_duration_time(self):
    return self.duration

class Ref_rttm:
  def __init__(self, data):
    if isinstance(data, str):
      line = data.strip()
      values = line.split(' ')
      self.type = values[0]
      self.file = values[1]
      self.chnl = values[2]
      self.tbeg = np.float32(values[3])
      self.tdur = np.float32(values[4])
      self.ortho = values[5]
      self.stype = values[6]
      self.name = values[7]
      self.conf = values[8]
      self.slat = values[9]
  def get_begin_time(self):
    return self.tbeg
  def set_begin_time(self, begin_time):
    self.tbeg = begin_time
  def get_duration_time(self):
    return self.tdur
  def set_duration_time(self, duration_time):
    self.tdur = duration_time
  def get_end_time(self):
    return self.tbeg + self.tdur
  def set_end_time(self, end_time):
    self.tdur = end_time - self.tbeg
  def __str__(self):
    return ' '.join([self.type, self.file, self.chnl, str(self.tbeg), str(self.tdur), self.ortho, self.stype, self.name, self.conf, self.slat])
