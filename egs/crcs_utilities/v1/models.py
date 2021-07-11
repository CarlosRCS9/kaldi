#!/usr/bin/env python3
# Copyright 2021 Carlos Castillo
#
# Apache 2.0

import numpy as np

class Rttm_line:
  def __init__ (self, data):
    if isinstance(data, str):
      data = data.strip().split()
      if (len(data) != 10):
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

class Rttm:
  def __init__ (self, data):
    self.rttm_lines = [Rttm_line(entry) for entry in data]
  def __str__ (self):
    output = ''
    for rttm_line in self.rttm_lines:
      output += rttm_line.__str__() + '\n'
    return output[:-1]
