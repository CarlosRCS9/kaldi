#!/usr/bin/env python3
# Copyright 2021 Carlos Castillo
#
# Apache 2.0

import numpy as np

class Rttm_line:
  def __init__ (self, data):
    if isinstance(data, str):
      data = data.strip().split()
      if len(data) != 10:
        raise ValueError('invalid input string')
      self.type  = data[0]
      self.file  = data[1]
      self.chnl  = data[2]
      self.tbeg  = np.float32(data[3])
      self.tdur  = np.float32(data[4])
      self.ortho = data[5]
      self.stype = data[6]
      self.name  = data[7]
      self.conf  = data[8]
      self.slat  = data[9]
      return
    raise ValueError('invalid input data type')
  def __str__ (self):
    return f"{self.type} {self.file} {self.chnl} {self.tbeg:.2f} {self.tdur:.2f} {self.ortho} {self.stype} {self.name} {self.conf} {self.slat}"

class Recording_rttm:
  def __init__ (self, data):
    self.recording_id = Rttm_line(data[0]).file
    self.rttm_lines = []
    for entry in data:
      rttm_line = Rttm_line(entry)
      if rttm_line.file != self.recording_id:
        raise ValueError(f"invalid input data {rttm_line.file} != {self.recording_id}")
      self.rttm_lines.append(rttm_line)
  def set_duration (self, duration):
    self.duration = duration
  def set_number_of_frames (self, number_of_frames):
    self.number_of_frames = number_of_frames
  def __str__ (self):
    output = ''
    for rttm_line in self.rttm_lines:
      output += rttm_line.__str__() + '\n'
    return output[:-1]

class Rttm:
  def __init__ (self, data):
    recording_rttm_lines = {}
    for entry in data:
      rttm_line = Rttm_line(entry)
      if rttm_line.file not in recording_rttm_lines:
        recording_rttm_lines[rttm_line.file] = []
      recording_rttm_lines[rttm_line.file].append(entry)
    self.recording_rttms = {}
    for recording_id in recording_rttm_lines:
      self.recording_rttms[recording_id] = Recording_rttm(recording_rttm_lines[recording_id])
  def load_durations (self, data):
    for recording_id in data:
      print(f"{recording_id} {data[recording_id]}")
  def load_utt2dur (self, utt2dur):
    for recording_id in self.recording_rttms:
      if recording_id not in utt2dur:
        raise ValueError(f"{recording_id} missing from utt2dur")
      self.recording_rttms[recording_id].set_duration(utt2dur[recording_id])
  def load_utt2num_frames (self, utt2num_frames):
    for recording_id in self.recording_rttms:
      if recording_id not in utt2num_frames:
        raise ValueError(f"{recording_id} missing from utt2num_frames")
      self.recording_rttms[recording_id].set_number_of_frames(utt2num_frames[recording_id])
  def __str__ (self):
    output = ''
    for recording_id in self.recording_rttms:
      recording_rttm = self.recording_rttms[recording_id]
      output += recording_rttm.__str__() + '\n'
    return output[:-1]
