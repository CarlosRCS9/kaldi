#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.
 
import numpy as np

class Speaker:
  def __init__(self, type, name):
    self.type = type
    self.name = name

class Segment:
  def __init__(self, data):
    if isinstance(data, str):
      data = data.split()
      self.type                  = data[0]
      self.file_id               = data[1]
      self.channel_id            = data[2]
      self.turn_onset            = np.float32(data[3])
      self.turn_duration         = np.float32(data[4])
      self.orthography_field     = data[5]
      self.speakers              = [Speaker(data[6], data[7])]
      self.confidence_score      = data[8]
      self.signal_lookahead_time = data[9]
    elif isinstance(data, Segment):
  def get_type(self):
    return self.type
  def get_file_id(self):
    return self.file_id
  def get_channel_id(self):
    return self.channel_id
  def get_turn_onset(self):
    return self.turn_onset
  def get_turn_duration(self):
    return self.turn_duration
  def get_turn_end(self):
    return self.turn_onset + self.turn_duration
  def get_orthography_field(self):
    return self.orthography_field
  def get_speakers(self):
    return self.speakers
  def get_confidence_score(self):
    return self.confidence_score
  def get_signal_lookahead_time(self):
    return self.signal_lookahead_time
  def is_within_timestamps(self, onset, end):
    return not (end <= self.get_onset() or self.get_end() <= onset)
  def __str__(self):
    return str(self.__class__) + ": " + str(self.__dict__)
