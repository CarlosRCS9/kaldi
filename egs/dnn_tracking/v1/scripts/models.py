#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import numpy

class Speaker:
  def __init__(self, data):
    if isinstance(data, list):
      self.channel_id = data[0]
      self.type       = data[1]
      self.name       = data[2]
  def get_channel_id(self):
    return self.channel_id
  def get_type(self):
    return self.type
  def get_name(self):
    return self.name

class Segment:
  def __init__(self, data):
    if isinstance(data, str):
      data = data.split()
      self.type                  = data[0]
      self.file_id               = data[1]
      self.turn_onset            = numpy.float32(data[3])
      self.turn_duration         = numpy.float32(data[4])
      self.orthography_field     = data[5]
      self.speakers              = [Speaker([data[2], data[6], data[7]])]
      self.confidence_score      = data[8]
      self.signal_lookahead_time = data[9]
  def get_type(self):
    return self.type
  def get_file_id(self):
    return self.file_id
  def get_turn_onset(self):
    return self.turn_onset
  def get_turn_duration(self):
    return self.turn_duration
  def get_orthography_field(self):
    return self.orthography_field
  def get_speakers(self):
    return self.speakers
  def get_confidence_score(self):
    return self.confidence_score
  def get_signal_lookahead_time(self):
    return self.signal_lookahead_time
  def get_rttm(self):
    output = ''
    for speaker in self.get_speakers():
      output += self.get_type() + ' ' + \
      self.get_file_id() + ' ' + \
      speaker.get_channel_id() + ' ' + \
      str(round(self.get_turn_onset(), 3)) + ' ' + \
      str(round(self.get_turn_duration(), 3)) + ' ' + \
      self.get_orthography_field() + ' ' + \
      speaker.get_type() + ' ' + \
      speaker.get_name() + ' ' + \
      self.get_confidence_score() + ' ' + \
      self.get_signal_lookahead_time() + '\n'
    return output
