#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import argparse

from models import Segment, \
Ivector, \
sort_segments_by_file_id, \
Utterance_turn, \
sort_utterances_turns_by_file_id, \
get_segments_union

def get_args():
  parser = argparse.ArgumentParser(description='')
  parser.add_argument('rttm', type=str, help='')
  parser.add_argument('segments', type=str, help='')
  parser.add_argument('ivectors', type=str, help='')
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
      indexes = [index for index, utterance_turn in enumerate(file_utterances_turns) if\
      segment.get_turn_onset() == utterance_turn.get_turn_onset()]
      if len(indexes) == 1:
        utterance_turn = file_utterances_turns.pop(indexes[0])
        segment.set_ivectors([Ivector([args.ivectors, utterance_turn.get_utterance_id()])])
      else:
        print('WARNING: missing utterance_turn for segment.')

if __name__ == '__main__':
  main()
