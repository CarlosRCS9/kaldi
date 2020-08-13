#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import sys

from models import Segment, sort_segments_by_file_id
from notebook import get_best_speakers

def get_stdin():
  return sys.stdin

def main():
  stdin = get_stdin()

  segments = [Segment(line) for line in stdin]
  files_segments = sort_segments_by_file_id(segments)
  for file_id in sorted(files_segments.keys()):
    segments = files_segments[file_id]
    speakers = get_best_speakers(segments, 1000)
    print(file_id, len(speakers))

if __name__ == '__main__':
  main()
