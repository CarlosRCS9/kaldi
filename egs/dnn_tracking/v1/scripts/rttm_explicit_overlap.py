#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import sys
from functools import reduce

from models import Segment

def get_file_segments(acc, segment):
  if segment.file_id not in acc:
    acc[segment.file_id] = []
  acc[segment.file_id].append(segment)
  return acc

def get_stdin():
  return sys.stdin

def main():
  print('test')
  stdin = get_stdin()
  segments = [Segment(line) for line in stdin]
  file_segments = reduce(get_file_segments, segments, {})

if __name__ == '__main__':
  main()
