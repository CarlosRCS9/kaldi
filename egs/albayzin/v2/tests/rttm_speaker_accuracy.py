#!/usr/bin/env python3
# Copyright 2020 Carlos Castillo
#
# Apache 2.0.

import argparse, os, sys, itertools
from models import Segment, sort_segments_by_file_id, get_segments_explicit_overlap

def get_args():
  parser = argparse.ArgumentParser(description = '')
  parser.add_argument('reference_rttm', type = str, help = '')
  parser.add_argument('test_rttm', type = str, help = '')
  args = parser.parse_args()
  return args

def main():
  args = get_args()
  if not os.path.isfile(args.reference_rttm):
    sys.exit(args.reference_rttm + ' not found')
  if not os.path.isfile(args.test_rttm):
    sys.exit(args.test_rttm + ' not found')

  reference_segments = []
  with open(args.reference_rttm) as f:
    for line in f:
      try:
        reference_segments.append(Segment(line))
      except Exception as e:
        print(e)
        print(line)
        pass
  test_segments = []
  with open(args.test_rttm) as f:
    for line in f:
      try:
        test_segments.append(Segment(line))
      except Exception as e:
        print(e)
        print(line)        
        pass
  reference_recordings_segments = sort_segments_by_file_id(reference_segments)
  test_recordings_segments = sort_segments_by_file_id(test_segments)

  total_error = 0
  total_count = 0
  print(len(reference_recordings_segments.keys()))
  print(len(test_recordings_segments.keys()))
  for recording_id in sorted(reference_recordings_segments.keys()):
    reference_segments = reference_recordings_segments[recording_id]
    test_segments = test_recordings_segments[recording_id]
    reference_speakers = list(set(itertools.chain(*[[speaker.get_name() for speaker in segment.get_speakers()] for segment in reference_segments])))
    test_speakers = list(set(itertools.chain(*[[speaker.get_name() for speaker in segment.get_speakers()] for segment in test_segments])))
    reference_speakers_len = len(reference_speakers)
    test_speakers_len = len(test_speakers)
    #error = (((reference_speakers_len - test_speakers_len) ** 2) ** (1 / 2)) / reference_speakers_len
    error = (test_speakers_len - reference_speakers_len) / reference_speakers_len
    print(recording_id)
    print('reference_speakers:', len(reference_speakers))
    print('result_speakers:', len(test_speakers))
    print('error:', error)
    total_error += error
    total_count += 1
  print('total error:', total_error / total_count)

if __name__ == '__main__':
  main()


