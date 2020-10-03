#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import argparse, sys
from models import Segment, sort_segments_by_file_id, get_segments_explicit_overlap

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
  speakers_count = 0
  speakers_map = {}
  files_segments = sort_segments_by_file_id(segments)
  for file_id in sorted(files_segments.keys()):
    segments = files_segments[file_id]
    new_segments = get_segments_explicit_overlap(segments)
    for segment in new_segments:
      speaker = '-'.join([speaker.get_name() for speaker in segment.get_speakers()])
      if speaker not in speakers_map:
        speakers_map[speaker] = args.name + str(speakers_count).zfill(3)
        speakers_count += 1
  for speaker, name in speakers_map.items():
    print(speaker, name)

if __name__ == '__main__':
  main()

