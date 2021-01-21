#!/usr/bin/env python3
#
# Copyright 2020 Carlos Castillo
# Apache 2.0.

import argparse
import sys

from models import Segment, sort_segments_by_file_id, get_segments_explicit_overlap
from notebook import get_first_speakers

def get_args():
  parser = argparse.ArgumentParser(description='')
  parser.add_argument('length', type=float, help='')
  parser.add_argument('overlap', type=float, help='')
  parser.add_argument('--min-length', type=float, default=0.0, help='')
  parser.add_argument('--max-file-speakers', type=int, default=2, help='')
  parser.add_argument('--max-segment-speakers', type=int, default=1, help='')
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
    new_file_segments = get_segments_explicit_overlap(file_segments)
    speakers = get_first_speakers(new_file_segments, args.max_file_speakers)
    for segment in new_file_segments:
      turn_onset = segment.get_turn_onset()
      while True:
        turn_end = turn_onset + args.length if turn_onset + args.length < segment.get_turn_end() else segment.get_turn_end()
        new_segment = Segment(segment)
        new_segment.set_turn_onset(turn_onset)
        new_segment.set_turn_end(turn_end)
        if new_segment.get_turn_duration() >= args.min_length and \
          len(new_segment.get_speakers()) <= args.max_segment_speakers and \
          all([speaker.get_name() in speakers for speaker in new_segment.get_speakers()]):
          print(new_segment.get_rttm(), end = '')
        if turn_end >= segment.get_turn_end():
          break
        turn_onset = turn_end - args.overlap

if __name__ == '__main__':
  main()

