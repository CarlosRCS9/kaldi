#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import numpy as np

class Segment:
  def __init__(self, data):
    if isinstance(data, str):
      data = data.split()
      data = {
        "type": data[0],
        "recording_id": data[1],
        "channel": data[2],
        "begining": np.float32(data[3]),
        "duration": np.float32(data[4]),
        "ending": np.float32(data[3]) + np.float32(data[4]),
        "ortho": data[5],
        "stype": data[6],
        "speaker_id": data[7],
        "conf": data[8],
        "slat": data[9],
      }
    self.type = data['type']
    self.recording_id = data['recording_id']
    self.channel = data['channel']
    self.begining = data['begining']
    self.duration = data['duration']
    self.ending = data['ending']
    self.ortho = data['ortho']
    self.stype = data['stype']
    self.speaker_id = data['speaker_id']
    self.conf = data['conf']
    self.slat = data['slat']
  def timestamps_overlap(self, begining, ending):
    return not (ending <= self.begining or self.ending <= begining)
  def __str__(self):
    return str(self.__class__) + ": " + str(self.__dict__)