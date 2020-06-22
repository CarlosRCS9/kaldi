#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import numpy
import functools
import itertools

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
  def add_speakers(self, speakers):
    self.speakers += [Speaker(speaker) for speaker in speakers if not self.has_speaker(speaker)]
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
  def has_timestamps_overlap(self, turn_onset, turn_end):
    return not (turn_end <= self.get_turn_onset() or self.get_turn_end() <= turn_onset)

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