#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

def limit_speakers_number(data, length, log = False):
  if isinstance(data, dict):
    files_segments = {}
    original_length = 0
    new_length = 0
    for file_id, segments in data.items():
      new_segments = list(filter(lambda segment: len(segment.get_speakers()) <= length, segments))
      files_segments[file_id] = new_segments
      original_length += len(segments)
      new_length += len(new_segments)
    if log:
      print('Kept ' + str(new_length) + ' of ' + str(original_length) + ': ' + str(new_length / original_length))
    return files_segments
  else:
    new_segments = filter(lambda segment: len(segment.get_speakers()) <= length, data)
    if log:
      print('Kept ' + str(len(new_segments)) + ' of ' + str(len(data)) + ': ' + str(len(new_segments) / len(data)))
    return new_segments
