#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import argparse, sys
from models import Segment, sort_segments_by_file_id

def get_args():
  parser = argparse.ArgumentParser(description = '')
  parser.add_argument('name', type = str, help = '')
  args = parser.parse_args()
  return args

def get_stdin():
  return sys.stdin

def main():
  args = get_args()
  stdin = get_stdin()
  segments = []
  for line in stdin:
    try:
      segments.append(Segment(line))
    except:
      pass
  files_count = 0
  files_map = {}
  files_segments = sort_segments_by_file_id(segments)
  for file_id in sorted(files_segments.keys()):
    if file_id not in files_map:
      files_map[file_id] = args.name + '-' + str(files_count).zfill(5)
      files_count += 1
    #print(file_id, file_id.replace('-', '_'))
    print(file_id, files_map[file_id])

if __name__ == '__main__':
  main()

