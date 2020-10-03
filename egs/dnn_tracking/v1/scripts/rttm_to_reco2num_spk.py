#!/usr/bin/env python3
#
# Copyright 2020 Carlos Castillo
# Apache 2.0.

import sys
from models import Segment, sort_segments_by_file_id

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
    segments = files_segments[file_id]
    segments_speakers = []
    for segment in segments:
      for speaker in segment.get_speakers():
        if speaker.get_name() not in segments_speakers:
          segments_speakers.append(speaker.get_name())
    print(file_id, len(segments_speakers))

if __name__ == '__main__':
  main()

