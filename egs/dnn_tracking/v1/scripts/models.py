#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import numpy
import functools
import itertools
import re

class Speaker:
  def __init__(self, data):
    if isinstance(data, list):
      self.channel_id = data[0]
      self.type       = data[1]
      self.name       = data[2]
    elif isinstance(data, Speaker):
      self.channel_id = data.get_channel_id()
      self.type       = data.get_type()
      self.name       = data.get_name()
  def get_channel_id(self):
    return self.channel_id
  def get_type(self):
    return self.type
  def get_name(self):
    return self.name
  def equals(self, speaker):
    return self.get_name() == speaker.get_name() and \
    self.get_channel_id() == speaker.get_channel_id() and \
    self.get_type() == speaker.get_type()
  def __str__(self):
    return str(self.__class__) + ": " + str(self.__dict__)

class Ivector:
  def __init__(self, data):
    if isinstance(data, str):
      data = data.split('  [ ')
      self.utterance_id = data[0].split('-')[0]
      self.value        = numpy.array(data[1][:-3].split(' ')).astype(numpy.float32)
    elif isinstance(data, Ivector):
      self.utterance_id = data.get_utterance_id()
      self.value        = data.get_value().copy()
    elif isinstance(data, numpy.ndarray):
      self.utterance_id = None
      self.value        = data
    else:
      print('Ivector: unknown data type.')
      self.utterance_id = None
      self.value        = None
  def get_utterance_id(self):
    return self.utterance_id
  def get_value(self):
    return self.value
  def set_value(self, value):
    self.value = value

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
      self.ivectors              = []
    elif isinstance(data, Segment):
      self.type                  = data.get_type()
      self.file_id               = data.get_file_id()
      self.turn_onset            = data.get_turn_onset()
      self.turn_duration         = data.get_turn_duration()
      self.orthography_field     = data.get_orthography_field()
      self.speakers              = [Speaker(speaker) for speaker in data.get_speakers()]
      self.confidence_score      = data.get_confidence_score()
      self.signal_lookahead_time = data.get_signal_lookahead_time()
      self.ivectors              = [Ivector(ivector) for ivector in data.get_ivectors()]
  def get_type(self):
    return self.type
  def get_file_id(self):
    return self.file_id
  def get_turn_onset(self):
    return self.turn_onset
  def set_turn_onset(self, turn_onset):
    self.turn_onset = turn_onset
  def get_turn_duration(self):
    return self.turn_duration
  def set_turn_duration(self, turn_duration):
    self.turn_duration = turn_duration
  def get_turn_end(self):
    return self.get_turn_onset() + self.get_turn_duration()
  def set_turn_end(self, turn_end):
    self.set_turn_duration(turn_end - self.get_turn_onset())
  def get_orthography_field(self):
    return self.orthography_field
  def get_speakers(self):
    return self.speakers
  def has_speaker(self, speaker):
    return any([self_speaker.equals(speaker) for self_speaker in self.get_speakers()])
  def has_same_speakers(self, segment):
    return len(self.get_speakers()) == len(segment.get_speakers()) and all([self.has_speaker(speaker) for speaker in segment.get_speakers()])
  def add_speakers(self, speakers):
    self.speakers += [Speaker(speaker) for speaker in speakers if not self.has_speaker(speaker)]
  def get_confidence_score(self):
    return self.confidence_score
  def get_signal_lookahead_time(self):
    return self.signal_lookahead_time
  def get_ivectors(self):
    return self.ivectors;
  def set_ivectors(self, ivectors):
    self.ivectors = ivectors
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
  def has_timestamps_overlap(self, turn_onset, turn_end):
    return not (turn_end <= self.get_turn_onset() or self.get_turn_end() <= turn_onset)
  def __str__(self):
    return str(self.__class__) + ": " + str(self.__dict__)

class Scp_file:
  def __init__(self, data):
    if isinstance(data, str):
      self.data           = data.split()
      self.filepath_index = [re.match(r'(\/.*?\.[\w:]+)', string) is not None for string in self.data].index(True)
      self.file_id        = self.data[0]
      self.filepath       = self.data[self.filepath_index]
      self.format         = self.filepath.split('.')[-1]
    elif isinstance(data, Scp_file):
      self.data           = data.get_data().copy()
      self.filepath_index = data.get_filepath_index()
      self.file_id        = data.get_file_id()
      self.filepath       = data.get_filepath()
      self.format         = data.get_format()
  def get_data(self):
    return self.data
  def get_filepath_index(self):
    return self.filepath_index
  def get_file_id(self):
    return self.file_id
  def get_filepath(self):
    return self.filepath
  def set_filepath(self, filepath):
    self.filepath = filepath
    self.get_data()[self.get_filepath_index()] = self.get_filepath()
  def get_format(self):
    return self.format
  def get_string(self):
    return ' '.join(self.data) + '\n'
  def __str__(self):
    return str(self.__class__) + ": " + str(self.__dict__)

class Utterance_turn:
  def __init__(self, data):
    if isinstance(data, str):
      data = data.split()
      self.utterance_id = data[0]
      self.file_id = data[1]
      self.turn_onset = numpy.float32(data[2])
      self.turn_end = numpy.float32(data[3])
  def get_utterance_id(self):
    return self.utterance_id
  def get_file_id(self):
    return self.file_id
  def get_turn_onset(self):
    return self.turn_onset
  def get_turn_end(self):
    return self.turn_end
  def __str__(self):
    return str(self.__class__) + ": " + str(self.__dict__)

def reduce_segments_by_file_id(accumulator, segment):
  if segment.get_file_id() not in accumulator:
    accumulator[segment.get_file_id()] = []
  accumulator[segment.get_file_id()].append(segment)
  return accumulator

def sort_segments_by_file_id(segments):
  return functools.reduce(reduce_segments_by_file_id, segments, {})

def get_segments_explicit_overlap(segments, min_length = 0.0005):
  new_segments = []
  timestamps = sorted(set(itertools.chain(*[[segment.get_turn_onset(), segment.get_turn_end()] for segment in segments])))
  timestamps_pairs = [(timestamps[i], timestamps[i + 1]) for i, _ in enumerate(timestamps[:-1])]
  for turn_onset, turn_end in timestamps_pairs:
    timestamps_segments = list(filter(lambda segment: segment.has_timestamps_overlap(turn_onset, turn_end), segments))
    if len(timestamps_segments) > 0:
      new_segment = Segment(timestamps_segments[0])
      new_segment.add_speakers(list(itertools.chain(*[segment.get_speakers() for segment in timestamps_segments[1:]])))
      new_segment.set_turn_onset(turn_onset)
      new_segment.set_turn_end(turn_end)
      if new_segment.get_turn_duration() > min_length:
        new_segments.append(new_segment)
  return new_segments

def get_segments_union(segments, min_length = 0.0005):
  original_segments = segments.copy()
  new_segments = []
  while len(original_segments) > 0:
    segment = original_segments.pop(0)
    if segment.get_turn_duration() > min_length:
      new_segment = Segment(segment)
      indexes = [index for index, segment in enumerate(original_segments) if \
      new_segment.get_turn_onset() == segment.get_turn_onset() and \
      segment.get_turn_duration() == segment.get_turn_duration()]
      indexes = [value - index for index, value in enumerate(indexes)]
      for index in indexes:
        segment = original_segments.pop(index)
        new_segment.add_speakers(segment.get_speakers())
      new_segments.append(new_segment)
  return new_segments

def reduce_scp_by_file_id(accumulator, scp_file):
  if scp_file.get_file_id() not in accumulator:
    accumulator[scp_file.get_file_id()] = scp_file
  return accumulator

def sort_scp_by_file_id(scp):
  return functools.reduce(reduce_scp_by_file_id, scp, {})

def read_wav_scp(filepath):
  f = open(filepath, 'r')
  scp = [Scp_file(line) for line in f.readlines()]
  f.close()
  scp = sort_scp_by_file_id(scp)
  return scp

def reduce_segments_by_speakers(accumulator, segment):
  speakers_names = ','.join(sorted(map(lambda speaker: speaker.get_name(), segment.get_speakers())))
  if speakers_names not in accumulator:
    accumulator[speakers_names] = []
  accumulator[speakers_names].append(segment)
  return accumulator

def sort_segments_by_speakers(segments):
  return functools.reduce(reduce_segments_by_speakers, segments, {})

def filter_by_speakers_length(speakers_segments, length):
  new_speakers_segments = {}
  for speakers_names in speakers_segments:
    if len(speakers_names.split(',')) == length:
      new_speakers_segments[speakers_names] = speakers_segments[speakers_names]
  return new_speakers_segments

def get_rttm_segments_features(rttm_filepath, segments_filepath, ivectors_filepath):
  f = open(rttm_filepath, 'r')
  segments = [Segment(line) for line in f.readlines()]
  f.close()
  files_segments = sort_segments_by_file_id(segments)

  utterances_turns_dict = {}
  f = open(segments_filepath, 'r')
  for line in f.readlines():
    utterance_turn = Utterance_turn(line)
    if utterance_turn.get_file_id() not in utterances_turns_dict:
      utterances_turns_dict[utterance_turn.get_file_id()] = {}
    utterances_turns_dict[utterance_turn.get_file_id()][utterance_turn.get_turn_onset()] = utterance_turn.get_utterance_id()
  f.close()

  ivectors_dict = {}
  f = open(ivectors_filepath, 'r')
  for line in f.readlines():
    ivector = Ivector(line)
    ivectors_dict[ivector.get_utterance_id()] = ivector
  f.close()

  for file_id, segments in files_segments.items():
    segments = get_segments_union(segments)
    for segment in segments:
      ivector = ivectors_dict[utterances_turns_dict[file_id][segment.get_turn_onset()]]
      segment.set_ivectors([ivector])
    files_segments[file_id] = segments

  return files_segments
