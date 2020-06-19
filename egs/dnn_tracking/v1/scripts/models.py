#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.
 
import numpy
import functools
import itertools
import re

def reduce_segments_by_file_id(output, segment):
  if segment.get_file_id() not in output:
    output[segment.get_file_id()] = []
  output[segment.get_file_id()].append(segment)
  return output

def sort_segments_by_file_id(segments):
  return functools.reduce(reduce_segments_by_file_id, segments, {})

def reduce_segments_by_speakers(output, segment):
  speakers_names = ','.join(sorted(map(lambda speaker: speaker.get_name(), segment.get_speakers())))
  if speakers_names not in output:
    output[speakers_names] = []
  output[speakers_names].append(segment)
  return output

def sort_segments_by_speakers(segments):
  return functools.reduce(reduce_segments_by_speakers, segments, {})

def filter_by_speakers_length(speakers_segments, length):
  new_speakers_segments = {}
  for speakers_names in speakers_segments:
    if len(speakers_names.split(',')) == length:
      new_speakers_segments[speakers_names] = speakers_segments[speakers_names]
  return new_speakers_segments

def get_segments_explicit_overlap(files_segments, min_length = 0.0005):
  new_files_segments = {}
  for file_id in sorted(files_segments.keys()):
    new_files_segments[file_id] = []
    file_segments = files_segments[file_id]
    new_file_segments = new_files_segments[file_id]
    timestamps = sorted(set(itertools.chain.from_iterable([[segment.get_turn_onset(), segment.get_turn_end()] for segment in file_segments])))
    timestamps_pairs = [(timestamps[i], timestamps[i + 1]) for i, _ in enumerate(timestamps[:-1])]
    for onset, end in timestamps_pairs:
      timestamps_segments = list(filter(lambda segment: segment.is_within_timestamps(onset, end), file_segments))
      if len(timestamps_segments) > 0:
        new_segment = Segment(timestamps_segments[0])
        new_segment.add_speakers(list(itertools.chain.from_iterable([segment.get_speakers() for segment in timestamps_segments[1:]])))
        new_segment.update_within_timestamps(onset, end)
        if new_segment.get_turn_duration() > min_length:
          new_file_segments.append(new_segment)
  return new_files_segments

def reduce_scps_by_file_id(output, scp):
  if scp.get_file_id() not in output:
    output[scp.get_file_id()] = scp
  return output

def sort_scps_by_file_id(scps):
  return functools.reduce(reduce_scps_by_file_id, scps, {})

class Scp:
  def __init__(self, data):
    if isinstance(data, str):
      self.data = data.split()
      self.filepath_index = [re.match(r'(\/.*?\.[\w:]+)', string) is not None for string in self.data].index(True)
      self.file_id = self.data[0]
      self.filepath = self.data[self.filepath_index]
      self.format = self.filepath.split('.')[-1]
  def get_file_id(self):
    return self.file_id
  def get_filepath(self):
    return self.filepath
  def get_format(self):
    return self.format
  def get_template(self, filepath):
    new_data = [item for item in self.data]
    new_data[self.filepath_index] = filepath
    return ' '.join(new_data) + '\n'
  def __str__(self):
    return str(self.__class__) + ": " + str(self.__dict__)

class Speaker:
  def __init__(self, data):
    if isinstance(data, list):
      self.channel_id = data[0]
      self.turn_onset = data[1]
      self.turn_duration = data[2]
      self.type = data[3]
      self.name = data[4]
    elif isinstance(data, Speaker):
      self.channel_id = data.get_channel_id()
      self.turn_onset = data.get_turn_onset()
      self.turn_duration = data.get_turn_duration()
      self.type = data.get_type()
      self.name = data.get_name()
  def get_channel_id(self):
    return self.channel_id
  def get_turn_onset(self):
    return self.turn_onset
  def set_turn_onset(self, turn_onset):
    self.turn_onset = turn_onset
  def add_turn_onset(self, seconds):
    self.turn_onset += seconds
  def update_turn_onset(self, onset):
    self.turn_onset = onset
  def get_turn_duration(self):
    return self.turn_duration
  def set_turn_duration(self, turn_duration):
    self.turn_duration = turn_duration
  def get_turn_end(self):
    return self.turn_onset + self.turn_duration
  def set_turn_end(self, turn_end):
    self.turn_duration = turn_end - self.get_turn_onset()
  def update_turn_end(self, turn_end):
    self.turn_duration = turn_end - self.get_turn_onset()
  def get_type(self):
    return self.type
  def get_name(self):
    return self.name
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
      self.turn_onset            = numpy.float32(data[3])
      self.turn_duration         = numpy.float32(data[4])
      self.orthography_field     = data[5]
      self.speakers              = [Speaker([data[2], self.turn_onset, self.turn_duration, data[6], data[7]])]
      self.confidence_score      = data[8]
      self.signal_lookahead_time = data[9]
    elif isinstance(data, Segment):
      self.type                  = data.get_type()
      self.file_id               = data.get_file_id()
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
  def get_turn_onset(self):
    return self.turn_onset
  def set_turn_onset(self, turn_onset):
    self.turn_onset = turn_onset
  def add_turn_onset(self, seconds):
    self.turn_onset += seconds
    for speaker in self.get_speakers():
      speaker.add_turn_onset(seconds)
  def update_turn_onset(self, turn_onset):
    self.turn_onset = turn_onset
    for speaker in self.get_speakers():
      speaker.update_turn_onset(turn_onset)
  def get_turn_duration(self):
    return self.turn_duration
  def set_turn_duration(self, turn_duration):
    self.turn_duration = turn_duration
  def get_turn_end(self):
    return self.turn_onset + self.turn_duration
  def set_turn_end(self, turn_end):
    self.turn_duration = turn_end - self.get_turn_onset()
  def update_turn_end(self, turn_end):
    self.turn_duration = turn_end - self.get_turn_onset()
    for speaker in self.get_speakers():
      speaker.update_turn_end(turn_end)
  def get_orthography_field(self):
    return self.orthography_field
  def get_speakers(self):
    return self.speakers
  def set_speakers(self, speakers):
    self.speakers = speakers
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
      output = self.get_type() + ' ' + self.get_file_id() + ' ' + speaker.get_channel_id() + ' ' + \
      str(round(speaker.get_turn_onset(), 3)) + ' ' + str(round(speaker.get_turn_duration(), 3)) + ' ' + \
      self.get_orthography_field() + ' ' + speaker.get_type() + ' ' + speaker.get_name() + \
      ' ' + self.get_confidence_score() + ' ' + self.get_signal_lookahead_time()
      print(output)
  def get_rttm(self):
    output = ''
    for speaker in self.get_speakers():
      output += self.get_type() + ' ' + self.get_file_id() + ' ' + speaker.get_channel_id() + ' ' + \
      str(round(speaker.get_turn_onset(), 3)) + ' ' + str(round(speaker.get_turn_duration(), 3)) + ' ' + \
      self.get_orthography_field() + ' ' + speaker.get_type() + ' ' + speaker.get_name() + \
      ' ' + self.get_confidence_score() + ' ' + self.get_signal_lookahead_time() + '\n'
    return output
  def __str__(self):
    return str(self.__class__) + ": " + str(self.__dict__)
