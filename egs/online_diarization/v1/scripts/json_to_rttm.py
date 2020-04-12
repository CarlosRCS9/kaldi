#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import argparse
import sys
import json

from models import Segment_complex

# is_valid_segment [VALIDATED]
# validates if a segment meets a maximum number of speakers,
# and that all the speakers in the segment belong to a list.
def is_valid_segment(segment_complex, maximum_speakers_length = 2, valid_speakers_ids = ['A', 'B']):
    speakers_ids = [speaker.speaker_id for speaker in segment_complex.speakers]
    speakers_ids = list(set(speakers_ids))
    return len(speakers_ids) <= maximum_speakers_length and \
        all(speaker_id in valid_speakers_ids for speaker_id in speakers_ids)

def get_args():
  parser = argparse.ArgumentParser(description='')
  parser.add_argument('--overlap-speaker', type=str, default='true', help='If true multiple-speakers segments get the "Z" speaker id in the output.')
  args = parser.parse_args()
  return args

def get_stdin():
  return sys.stdin

def main():
  args = get_args()
  args.overlap_speaker = args.overlap_speaker.lower() == 'true'
  stdin = get_stdin()
  segments = [Segment_complex(json.loads(line)) for line in stdin]
  segments = filter(is_valid_segment, segments)
  for segment in segments:
    print(segment.get_rttm(args.overlap_speaker))

if __name__ == '__main__':
  main()
