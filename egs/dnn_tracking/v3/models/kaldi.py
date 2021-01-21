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
  def get_filepath(self):
    return self.wav

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
  def __init__(self, data, rename_speakers = False):
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
      self.name = self.file + '_' + values[7] if rename_speakers else values[7]
      self.conf = values[8]
      self.slat = values[9]
  def get_file(self):
    return self.file
  def get_chnl(self):
    return self.chnl
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
    if isinstance(data, Speaker):
      speaker = data
      self.channel = speaker.get_channel()
      self.name = speaker.get_name()
    elif isinstance(data, Ref_rttm):
      ref_rttm = data
      self.channel = ref_rttm.get_chnl()
      self.name = ref_rttm.get_name()
  def get_channel(self):
    return self.channel
  def get_name(self):
    return self.name
  def is_same_speaker(self, data):
    if isinstance(data, Speaker):
      speaker = data
      return self.channel == speaker.get_channel() and self.name == speaker.get_name()
    elif isinstance(data, Ref_rttm):
      ref_rttm = data
      return self.channel == ref_rttm.get_chnl() and self.name == ref_rttm.get_name()

class Segment:
  def __init__(self, data):
    if isinstance(data, Recording):
      recording = data
      self.recording_id = recording.get_recording_id()
      self.begin_time = 0
      self.duration_time = 0
      self.speakers = []
      self.frame_shift = recording.get_frame_shift()
      self.features = {}
    elif isinstance(data, Segment):
      segment = data
      self.recording_id = segment.get_recording_id()
      self.begin_time = segment.get_begin_time()
      self.duration_time = segment.get_duration_time()
      self.speakers = [Speaker(speaker) for speaker in segment.get_speakers()]
      self.frame_shift = segment.get_frame_shift()
      self.features = {}
    elif isinstance(data, Ref_rttm):
      ref_rttm = data
      self.recording_id = ref_rttm.get_file()
      self.begin_time = ref_rttm.get_begin_time()
      self.duration_time = ref_rttm.get_duration_time()
      self.speakers = [Speaker(ref_rttm)]
      self.frame_shift = 0.01
      self.features = {}
  def get_recording_id(self):
    return self.recording_id
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
  def get_speakers(self):
    return self.speakers
  def has_speaker(self, data):
    if isinstance(data, Speaker):
      speaker = data
      return any([self_speaker.is_same_speaker(speaker) for self_speaker in self.speakers])
    elif isinstance(data, Ref_rttm):
      ref_rttm = data
      return any([speaker.is_same_speaker(ref_rttm) for speaker in self.speakers])
  def add_speaker(self, data):
    if isinstance(data, Speaker):
      speaker = data
      if not self.has_speaker(speaker):
        self.speakers.append(Speaker(speaker)) 
    elif isinstance(data, Ref_rttm):
      ref_rttm = data
      if not self.has_speaker(ref_rttm):
        self.speakers.append(Speaker(ref_rttm))
  def delete_speakers(self):
    self.speakers = []
  def get_frame_shift(self):
    return self.frame_shift
  def get_feature(self, key):
    if key in self.features:
      return self.features[key]
  def set_feature(self, key, value):
    self.features[key] = value
  def overlap_timestamps(self, begin_time, end_time):
    return begin_time < self.get_end_time() and self.get_begin_time() < end_time
  def frame_shift_to_decimal_places(self):
    return len(str(float(self.frame_shift)).split('.')[1])
  def get_utterance_id(self, index):
    return self.recording_id + '_' + str(index).zfill(8) + \
    '-' + str(round(self.get_begin_time() * 10 ** self.frame_shift_to_decimal_places())).zfill(8) + \
    '-' + str(round(self.get_end_time() * 10 ** self.frame_shift_to_decimal_places())).zfill(8)
  def get_segments_string(self, index):
    return self.get_utterance_id(index) + ' ' + self.recording_id + \
    ' ' + str(round(self.get_begin_time(), self.frame_shift_to_decimal_places())) + \
    ' ' + str(round(self.get_end_time(), self.frame_shift_to_decimal_places())) + \
    '\n'
  def get_utt2spk_string(self, index):
    return self.get_utterance_id(index) + \
    ' ' + ','.join(sorted([speaker.get_name() for speaker in self.get_speakers()])) + \
    '\n'
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
    if isinstance(data, Recording):
      recording = data
      self.recording_id = recording.get_recording_id()
      self.segments = [Segment(segment) for segment in recording.get_segments()]
      self.frame_shift = 0.01
    elif isinstance(data, list) and len(data) > 0:
      if isinstance(data[0], Ref_rttm):
        self.recording_id = data[0].get_file()
        self.segments = []
        self.frame_shift = 0.01
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
  def get_segments(self):
    return self.segments
  def add_segment(self, segment):
    self.segments.append(Segment(segment))
  def delete_segments(self):
    self.segments = []
  def get_frame_shift(self):
    return self.frame_shift
  def get_timestamps_speakers(self, begin_time, end_time, begin_index = 0):
    speakers = []
    for index, segment in enumerate(self.segments[begin_index:]):
      segment_index = index + begin_index
      if segment.get_end_time() <= begin_time:
        continue
      if end_time <= segment.get_begin_time():
        return speakers, segment_index - 1
      speakers = speakers + segment.get_speakers()
    return speakers, segment_index - 1
  def frame_shift_to_decimal_places(self):
    return len(str(float(self.frame_shift)).split('.')[1])
  def get_rttm(self):
    output = ''
    for segment in self.segments:
      for speaker in segment.get_speakers():
        output += 'SPEAKER ' + self.recording_id + ' ' + speaker.get_channel() + \
        ' ' + str(round(segment.get_begin_time(), self.frame_shift_to_decimal_places())) + \
        ' ' + str(round(segment.get_duration_time(), self.frame_shift_to_decimal_places())) + \
        ' <NA> <NA> ' + speaker.get_name() + ' <NA> <NA>\n' 
    return output
  def __str__(self):
    output = 'recording:'
    output += '\n  name: ' + self.get_recording_id() + '\n'
    for segment in self.segments:
      for line in segment.__str__().split('\n'):
        output += '  ' + line + '\n'
    return output