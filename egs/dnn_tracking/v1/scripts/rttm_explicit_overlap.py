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
  for file_id in sorted(files_segments.keys()):
    file_segments = files_segments[file_id];
    timestamps = sorted(itertools.chain.from_iterable([[segment.get_onset(), segment.get_end()] for segment in file_segments]))
    timestamps_pairs = [(timestamps[i], timestamps[i + 1]) for i, _ in enumerate(timestamps[:-1])]

    for onset, end in timestamps_pairs:
      timestamps_segments = filter(lambda segment: segment.is_within_timestamps(onset, end), file_segments)
      if len(timestamps_segments) > 0:
        print(onset, end)
        for segment in timestamps_segments:
          print(segment)

if __name__ == '__main__':
  main()
