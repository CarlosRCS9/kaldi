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
    self.ending = data['begining'] + data['duration']
    self.ortho = data['ortho']
    self.stype = data['stype']
    self.speaker_id = data['speaker_id']
    self.conf = data['conf']
    self.slat = data['slat']
  def overlap(self, begining, ending):
    return not (ending <= self.begining or self.ending <= begining)
  def __str__(self):
    return str(self.__class__) + ": " + str(self.__dict__)

class Speaker:
  def __init__(self, segment_complex, segment):
    self.speaker_id = segment.speaker_id
    self.begining = segment.begining if segment.begining > segment_complex.begining else segment_complex.begining
    self.ending = segment.ending if segment.ending < segment_complex.ending else segment_complex.ending
    self.duration = self.ending - self.begining
  def mix_speaker(self, speaker):
    if self.speaker_id != speaker.speaker_id:
      exit('speaker_ids doesnt match.')
    self.begining = self.begining if self.begining < speaker.begining else speaker.begining
    self.ending = self.ending if self.ending > speaker.ending else speaker.ending
    self.duration = self.ending - self.begining
  def __str__(self):
    return str(self.__class__) + ": " + str(self.__dict__)

class Segment_complex:
  def __init__(self, segment, begining = None, ending = None):
    self.type = segment.type
    self.recording_id = segment.recording_id
    self.channel = segment.channel
    self.begining = segment.begining if begining is None else begining
    self.ending = segment.ending if ending is None else ending
    self.duration = self.ending - self.begining
    self.ortho = segment.ortho
    self.stype = segment.stype
    self.speakers = [Speaker(self, segment)]
    self.conf = segment.conf
    self.slat = segment.slat
  def add_segment(self, segment):
    self.speakers.append(Speaker(self, segment))
  def same_speakers(self, segment_complex):
    self_speakers_ids = sorted([speaker.speaker_id for speaker in self.speakers])
    target_speakers_ids = sorted([speaker.speaker_id for speaker in segment_complex.speakers])
    return np.array_equal(self_speakers_ids, target_speakers_ids)
  def mix_segment_complex(self, segment_complex):
    self.begining = self.begining if self.begining < segment_complex.begining else segment_complex.begining
    self.ending = self.ending if self.ending > segment_complex.ending else segment_complex.ending
    self.duration = self.ending - self.begining
    self.speakers.sort(key = lambda speaker: speaker.speaker_id)
    segment_complex.speakers.sort(key = lambda speaker: speaker.speaker_id)
    for index in range(len(self.speakers)):
      self.speakers[index].mix_speaker(segment_complex.speakers[index])
  def get_rttm(self, overlap_speaker = False):
    rttm = ''
    if overlap_speaker:
      rttm += ' '.join([self.type, self.recording_id, self.channel, str(round(self.begining, 2)), str(round(self.duration, 2)), self.ortho, self.stype, self.speakers[0].speaker_id if len(self.speakers) == 1 else 'Z', self.conf, self.slat]) + '\n'
    else:
      for speaker in self.speakers:
        rttm += ' '.join([self.type, self.recording_id, self.channel, str(round(self.begining, 2)), str(round(self.duration, 2)), self.ortho, self.stype, speaker.speaker_id, self.conf, self.slat]) + '\n'
    return rttm    
  def __str__(self):
    return str(self.__class__) + ": " + str(self.__dict__)