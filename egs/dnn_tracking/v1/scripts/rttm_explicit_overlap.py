#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import sys
import functools
import itertools

from models import Segment, sort_segments_by_file_id, get_segments_explicit_overlap

def get_stdin():
  return sys.stdin

def main():
  stdin = get_stdin()
  segments = [Segment(line) for line in stdin]
  files_segments = sort_segments_by_file_id(segments)
  files_segments = get_segments_explicit_overlap(files_segments)
  for file_id in files_segments:
    file_segments = files_segments[file_id]
    for segment in file_segments:
      segment.print_rttm()

if __name__ == '__main__':
  main()
