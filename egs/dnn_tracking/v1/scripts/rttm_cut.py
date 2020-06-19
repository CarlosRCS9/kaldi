#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import argparse
import sys

from models import Segment, sort_segments_by_file_id

def get_args():
  parser = argparse.ArgumentParser(description='')
  parser.add_argument('length', type=float, help='')
  parser.add_argument('overlap', type=float, help='')
  parser.add_argument('--min-length', type=float, default=0.0, help='')
  args = parser.parse_args()
  return args

def get_stdin():
  return sys.stdin

def main():
  args = get_args()
  stdin = get_stdin()

  segments = [Segment(line) for line in stdin]
  files_segments = sort_segments_by_file_id(segments)
  for file_id in sorted(files_segments.keys()):
    file_segments = files_segments[file_id]
    for segment in file_segments:
      turn_onset = segment.get_turn_onset()
      print(turn_onset)

if __name__ == '__main__':
  main()
