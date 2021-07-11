#!/usr/bin/env python3
# Copyright 2021 Carlos Castillo
#
# Apache 2.0

class Rttm_line:
  def __init__ (self, data):
    if isinstance(data, str):
      data = data.strip()
      print(data)
    else:
      raise ValueError('invalid input data type')
