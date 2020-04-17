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
def is_valid_segment(segment_complex, maximum_speakers_length = None, valid_speakers_ids = None):
    speakers_ids = [speaker.speaker_id for speaker in segment_complex.speakers]
    speakers_ids = list(set(speakers_ids))
    return (maximum_speakers_length is None or len(speakers_ids) <= maximum_speakers_length) and \
        (valid_speakers_ids is None or all(speaker_id in valid_speakers_ids for speaker_id in speakers_ids))

def get_args():
  parser = argparse.ArgumentParser(description='')
  parser.add_argument('--overlap-speaker', type=str, default='true', help='If true multiple-speakers segments get the "Z" speaker id in the output.')
  parser.add_argument('--maximum-speakers', type=str, default='None', help='The maximum number of speakers for each segment.')
  parser.add_argument('--valid-speakers', type=str, default='None', help='Comma separated valid speaker ids.')
  args = parser.parse_args()
  return args

def get_stdin():
  return sys.stdin

def main():
  args = get_args()
  args.overlap_speaker = args.overlap_speaker.lower() == 'true'
  args.maximum_speakers = None if args.maximum_speakers == 'None' else int(args.maximum_speakers)
  args.valid_speakers = None if args.valid_speakers == 'None' else args.valid_speakers.split(',')
  stdin = get_stdin()
  segments = [Segment_complex(json.loads(line)) for line in stdin]
  segments = filter(lambda segment: is_valid_segment(segment, args.maximum_speakers, args.valid_speakers), segments)
  for segment in segments:
    print(segment.get_rttm(args.overlap_speaker))

if __name__ == '__main__':
  main()
