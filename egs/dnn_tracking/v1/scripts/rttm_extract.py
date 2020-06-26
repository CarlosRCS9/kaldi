#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import sys

from models import Segment, sort_segments_by_file_id

def get_stdin():
  return sys.stdin

def main():
  stdin = get_stdin()

  segments = [Segment(line) for line in stdin]
  files_segments = sort_segments_by_file_id(segments)

  segments_data = ''
  for file_id in sorted(files_segments.keys()):
    file_segments = files_segments[file_id]
    count = 0
    for segment in file_segments:
      segments_data += segment.get_file_id() + '_' + count + ' ' + \
      segment.get_file_id() + ' ' + \
      segment.get_turn_onset() + ' ' + \
      segment.get_turn_end() + '\n'
      count += 1

  print(segments_data)

if __name__ == '__main__':
  main()
