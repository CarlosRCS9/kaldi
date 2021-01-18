#!/usr/bin/env python3
# Copyright 2021 Carlos Castillo
#
# Apache 2.0

import numpy as np
import itertools


class Wav_scp:
  def __init__(self, data):
    if isinstance(data, str):
      line = data.strip()
      recording_id, wav = line.split(' ', 1)
      self.recording_id = recording_id
      self.wav = wav

class Utt2dur:
  def __init__(self, data, frame_shift = 0.01):
    if isinstance(data, str):
      line = data.strip()
      utterance, duration = line.split(' ')
      duration = np.float32(duration)
      frame_shift = np.float32(frame_shift)
      self.utterance = utterance
      self.duration = duration
      self.frame_shift = frame_shift
      self.frames = int(round(self.duration / self.frame_shift))
  def get_duration_time(self):
    return self.duration
  def get_duration_frames(self):
    return self.frames

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
  def get_file(self):
    return self.file
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
  def get_name(self):
    return self.name
  def overlaps_timestamps(self, begin_time, end_time):
    return begin_time < self.get_end_time() and self.get_begin_time() < end_time
  def __str__(self):
    return ' '.join([self.type, self.file, self.chnl, str(self.tbeg), str(self.tdur), self.ortho, self.stype, self.name, self.conf, self.slat])

class Speaker:
  def __init__(self, data):
    if isinstance(data, Ref_rttm):
      ref_rttm = data
      self.name = ref_rttm.get_name()
  def get_name(self):
    return self.name
  def is_same_speaker(self, data):
    if isinstance(data, Ref_rttm):
      ref_rttm = data
      return self.name == ref_rttm.get_name()

class Segment:
  def __init__(self, data):
    if isinstance(data, Ref_rttm):
      ref_rttm = data
      self.begin_time = ref_rttm.get_begin_time()
      self.duration_time = ref_rttm.get_duration_time()
      self.speakers = [Speaker(ref_rttm)]
  def get_begin_time(self):
    return self.begin_time
  def set_begin_time(self, begin_time):
    self.begin_time = begin_time
  def get_duration_time(self):
    return self.duration_time
  def set_duration_time(self, duration_time):
    self.duration_time = duration_time
  def get_end_time(self):
    return self.begin_time + self.duration_time
  def set_end_time(self, end_time):
    self.duration_time = end_time - self.begin_time
  def has_speaker(self, data):
    if isinstance(data, Ref_rttm):
      ref_rttm = data
      return any([speaker.is_same_speaker(ref_rttm) for speaker in self.speakers])
  def add_speaker(self, data):
    if isinstance(data, Ref_rttm):
      ref_rttm = data
      if not self.has_speaker(ref_rttm):
        self.speakers.append(Speaker(ref_rttm))
  def __str__(self):
    output = 'segment:' + \
    '\n  begin: ' + str(self.get_begin_time()) + \
    '\n  end: ' + str(self.get_end_time())
    if len(self.speakers) > 0:
      output += '\n  speakers:'
      for speaker in self.speakers:
        output += '\n    ' + speaker.get_name()
    return output

class Recording:
  def __init__(self, data):
    if isinstance(data, list) and len(data) > 0:
      if isinstance(data[0], Ref_rttm):
        self.recording_id = data[0].get_file()
        self.segments = []
        ref_rttm_list = sorted(data, key = lambda ref_rttm: ref_rttm.get_begin_time())
        timestamps = sorted(set(itertools.chain(*[[ref_rttm.get_begin_time(), ref_rttm.get_end_time()] for ref_rttm in ref_rttm_list])))
        timestamps_pairs = [[timestamps[index], timestamps[index + 1]] for index, _ in enumerate(timestamps[:-1])]
        for begin, end in timestamps_pairs:
          overlapping_timestamps = [ref_rttm for ref_rttm in ref_rttm_list if ref_rttm.overlaps_timestamps(begin, end)]
          if len(overlapping_timestamps) > 0:
            segment = Segment(overlapping_timestamps[0])
            segment.set_begin_time(begin)
            segment.set_end_time(end)
            for ref_rttm in overlapping_timestamps[1:]:
              segment.add_speaker(ref_rttm)
            self.segments.append(segment)
  def get_recording_id(self):
    return self.recording_id
  def __str__(self):
    output = 'recording:'
    output += '\n  name: ' + self.get_recording_id()
    return output