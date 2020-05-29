#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import sys
import functools
import itertools

from models import Segment

def get_file_segments(acc, segment):
  if segment.get_file_id() not in acc:
    acc[segment.get_file_id()] = []
  acc[segment.get_file_id()].append(segment)
  return acc

def get_stdin():
  return sys.stdin

def main():
  stdin = get_stdin()
  segments = [Segment(line) for line in stdin]
  files_segments = functools.reduce(get_file_segments, segments, {})
  new_segments = []
  for file_id in sorted(files_segments.keys()):
    file_segments = files_segments[file_id];
    timestamps = sorted(set(itertools.chain.from_iterable([[segment.get_turn_onset(), segment.get_turn_end()] for segment in file_segments])))
    timestamps_pairs = [(timestamps[i], timestamps[i + 1]) for i, _ in enumerate(timestamps[:-1])]
    for onset, end in timestamps_pairs:
      timestamps_segments = filter(lambda segment: segment.is_within_timestamps(onset, end), file_segments)
      if len(timestamps_segments) > 0:
        new_segment = Segment(timestamps_segments[0])
        new_segment.add_speakers(list(itertools.chain.from_iterable([segment.get_speakers() for segment in timestamps_segments[1:]])))
        new_segment.update_within_timestamps(onset, end)
        new_segments.append(new_segment)
  for segment in new_segments:
    segment.print_rttm()

if __name__ == '__main__':
  main()
