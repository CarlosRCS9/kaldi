#!/usr/bin/env python3
# Copyright 2020 Carlos Castillo
#
# Apache 2.0.

import argparse, os, sys, itertools
import numpy as np
from models import Segment, sort_segments_by_file_id, get_segments_explicit_overlap

def get_args():
  parser = argparse.ArgumentParser(description = '')
  parser.add_argument('reference_rttm', type = str, help = '')
  args = parser.parse_args()
  return args

def main():
  args = get_args()
  if not os.path.isfile(args.reference_rttm):
    sys.exit(args.reference_rttm + ' not found')

  reference_segments = []
  with open(args.reference_rttm) as f:
    for line in f:
      try:
        reference_segments.append(Segment(line))
      except:
        pass
  reference_recordings_segments = sort_segments_by_file_id(reference_segments)

  speaker_map = {}
  for recording_id in sorted(reference_recordings_segments.keys()):
    reference_segments = get_segments_explicit_overlap(reference_recordings_segments[recording_id])
    for segment in reference_segments:
        for speaker_name in [speaker.get_name() for speaker in segment.get_speakers()]:
            if speaker_name not in speaker_map:
                speaker_map[speaker_name] = 0
            speaker_map[speaker_name] += segment.get_turn_duration()
  print(speaker_map)
  speaker_map_values = list(speaker_map.values())
  mean, std = np.mean(speaker_map_values), np.std(speaker_map_values)
  print('mean', mean, 'std', std)


if __name__ == '__main__':
  main()


