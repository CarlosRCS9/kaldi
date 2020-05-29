#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.
 
import numpy as np

class Speaker:
  def __init__(self, data):
    if isinstance(data, list):
      self.type = data[0]
      self.name = data[1]
      self.turn_onset = data[2]
      self.turn_duration = data[3]
    elif isinstance(data, Speaker):
      self.type = data.get_type()
      self.name = data.get_name()
      self.turn_onset = data.get_turn_onset()
      self.turn_duration = data.get_turn_duration()
  def get_type(self):
    return self.type
  def get_name(self):
    return self.name
  def get_turn_onset(self):
    return self.turn_onset
  def set_turn_onset(self, turn_onset):
    self.turn_onset = turn_onset
  def get_turn_duration(self):
    return self.turn_duration
  def set_turn_duration(self, turn_duration):
    self.turn_duration = turn_duration
  def get_turn_end(self):
    return self.turn_onset + self.turn_duration
  def set_turn_end(self, turn_end):
    self.turn_duration = turn_end - self.get_turn_onset()
  def update_within_timestamps(self, onset, end):
    if onset < end:
      if self.get_turn_onset() < onset:
        self.set_turn_onset(onset)
      if self.get_turn_end() > end:
        self.set_turn_end(end)
    else:
      print('WARNING: turn onset ' + str(onset) + ' is not less than end ' + str(end) + '.')
  def __str__(self):
    return str(self.__class__) + ": " + str(self.__dict__)

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
      self.speakers              = [Speaker([data[6], data[7], self.turn_onset, self.turn_duration])]
      self.confidence_score      = data[8]
      self.signal_lookahead_time = data[9]
    elif isinstance(data, Segment):
      self.type                  = data.get_type()
      self.file_id               = data.get_file_id()
      self.channel_id            = data.get_channel_id()
      self.turn_onset            = data.get_turn_onset()
      self.turn_duration         = data.get_turn_duration()
      self.orthography_field     = data.get_orthography_field()
      self.speakers              = [Speaker(speaker) for speaker in data.get_speakers()]
      self.confidence_score      = data.get_confidence_score()
      self.signal_lookahead_time = data.get_signal_lookahead_time()
  def get_type(self):
    return self.type
  def get_file_id(self):
    return self.file_id
  def get_channel_id(self):
    return self.channel_id
  def get_turn_onset(self):
    return self.turn_onset
  def set_turn_onset(self, turn_onset):
    self.turn_onset = turn_onset
  def get_turn_duration(self):
    return self.turn_duration
  def set_turn_duration(self, turn_duration):
    self.turn_duration = turn_duration
  def get_turn_end(self):
    return self.turn_onset + self.turn_duration
  def set_turn_end(self, turn_end):
    self.turn_duration = turn_end - self.get_turn_onset()
  def get_orthography_field(self):
    return self.orthography_field
  def get_speakers(self):
    return self.speakers
  def add_speakers(self, speakers):
    self.speakers = [Speaker(speaker) for speaker in self.get_speakers() + speakers]
  def get_confidence_score(self):
    return self.confidence_score
  def get_signal_lookahead_time(self):
    return self.signal_lookahead_time
  def is_within_timestamps(self, onset, end):
    return not (end <= self.get_turn_onset() or self.get_turn_end() <= onset)
  def update_within_timestamps(self, onset, end):
    if onset < end:
      if self.get_turn_onset() < onset:
        self.set_turn_onset(onset)
      if self.get_turn_end() > end:
        self.set_turn_end(end)
      for speaker in self.get_speakers():
        speaker.update_within_timestamps(self.get_turn_onset(), self.get_turn_end())
    else:
      print('WARNING: turn onset ' + str(onset) + ' is not less than end ' + str(end) + '.')
  def print_rttm(self):
    for speaker in self.get_speakers():
      output = self.get_type() + ' ' + self.get_file_id() + ' ' + self.get_channel_id() + ' ' + \
      str(speaker.get_turn_onset()) + ' ' + str(speaker.get_turn_duration()) + ' ' + self.get_orthography_field() + \
      ' ' + speaker.get_type() + ' ' + speaker.get_name() + ' ' + self.get_confidence_score() + ' ' + self.get_signal_lookahead_time()
      print(output)
  def __str__(self):
    return str(self.__class__) + ": " + str(self.__dict__)
