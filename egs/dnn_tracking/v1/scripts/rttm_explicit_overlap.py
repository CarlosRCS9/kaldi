#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import sys

from models import Segment, sort_segments_by_file_id, get_segments_explicit_overlap

def get_stdin():
  return sys.stdin

def main():
  stdin = get_stdin()
  segments = [Segment(line) for line in stdin]
  files_segments = sort_segments_by_file_id(segments)
  for file_id in sorted(files_segments.keys()):
    file_segments = files_segments[file_id]
    new_file_segments = get_segments_explicit_overlap(file_segments)
    for segment in new_file_segments:
      print(segment.get_rttm(), end = '')

if __name__ == '__main__':
  main()
