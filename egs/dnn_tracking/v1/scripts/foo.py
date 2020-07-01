#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import argparse

from models import Segment, \
sort_segments_by_file_id, \
Utterance_turn, \
sort_utterances_turns_by_file_id, \
get_segments_union

def get_args():
  parser = argparse.ArgumentParser(description='')
  parser.add_argument('rttm', type=str, help='')
  parser.add_argument('segments', type=str, help='')
  args = parser.parse_args()
  return args

def main():
  args = get_args()

  f = open(args.rttm, 'r')
  segments = [Segment(line) for line in f.readlines()]
  f.close()
  files_segments = sort_segments_by_file_id(segments)

  f = open(args.segments, 'r')
  utterances_turns = [Utterance_turn(line) for line in f.readlines()]
  f.close()
  files_utterances_turns = sort_utterances_turns_by_file_id(utterances_turns)

  for file_id in sorted(files_segments.keys()):
    file_segments = get_segments_union(files_segments[file_id])
    file_utterances_turns = files_utterances_turns[file_id]
    for segment in file_segments:
      segment_utterances_turns = list(filter(lambda utterance_turn: segment.get_turn_onset() == utterance_turn.get_turn_onset(), file_utterances_turns))
      print(segment.get_rttm(), end = '')
      for utterance_turn in segment_utterances_turns:
        print(utterance_turn)

if __name__ == '__main__':
  main()
