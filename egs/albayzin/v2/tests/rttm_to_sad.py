#!/usr/bin/env python3
# Copyright 2020 Carlos Castillo
#
# Apache 2.0.

import sys

from models import Segment, sort_segments_by_file_id, get_segments_explicit_overlap

def get_stdin():
  return sys.stdin

def main():
  stdin = get_stdin()
  segments = []
  for line in stdin:
    try:
      segments.append(Segment(line))
    except:
      pass
  files_segments = sort_segments_by_file_id(segments)
  for file_id in sorted(files_segments.keys()):
    file_segments = files_segments[file_id]
    new_file_segments = get_segments_explicit_overlap(file_segments)
    for index, segment in enumerate(new_file_segments):
      if segment.get_turn_duration() >= 0.01:
        #print(segment.get_rttm())
        print(segment.get_turn_onset(), segment.get_turn_end(), 'speech')

if __name__ == '__main__':
  main()

