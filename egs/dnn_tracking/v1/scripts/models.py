#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.
 
import numpy as np

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
      self.speaker_type          = data[6]
      self.spekaer_name          = data[7]
      self.confidence_score      = data[8]
      self.signal_lookahead_time = data[9]
  def __str__(self):
    return str(self.__class__) + ": " + str(self.__dict__)
