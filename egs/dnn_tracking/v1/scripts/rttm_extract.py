#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

from models import Segment, sort_segments_by_file_id

def get_stdin():
  return sys.stdin

def main():
  stdin = get_stdin()
  segments = [Segment(line) for line in stdin]
  for segment in segments:
    print(segment.get_rttm(), end = '')

if __name__ == '__main__':
  main()
