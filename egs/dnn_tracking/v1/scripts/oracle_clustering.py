#!/usr/bin/env python3
# Copyright 2020 Carlos Castillo
#
# Apache 2.0.

import argparse, os, sys
from models import Segment, sort_segments_by_file_id, get_segments_explicit_overlap
import numpy as np
import itertools

def get_args():
  parser = argparse.ArgumentParser(description = '')
  parser.add_argument('ref_rttm', type = str, help = '')
  parser.add_argument('segments', type = str, help = '')
  args = parser.parse_args()
  return args

def main():
  args = get_args()
  if not os.path.isfile(args.ref_rttm):
    sys.exit(args.ref_rttm + ' not found')
  if not os.path.isfile(args.segments):
    sys.exit(args.segments + ' not found')

  ref_rttm = []
  with open(args.ref_rttm) as f:
    for line in f:
      try:
        ref_rttm.append(Segment(line))
      except:
        pass
      if 'str' in line:
        break

  recordings_segments = {}
  with open(args.segments) as f:
    for line in f:
      try:
        utterance_id, recording_id, begin, end = line.rstrip().split()
        begin = np.float32(begin)
        end = np.float32(end)
        if recording_id not in recordings_segments:
          recordings_segments[recording_id] = []
        recordings_segments[recording_id].append({ 'utterance_id': utterance_id, 'begin': begin, 'end': end })
      except:
        pass
      if 'str' in line:
        break

  recordings_ref_rttm = sort_segments_by_file_id(ref_rttm)
  for recording_id in sorted(recordings_ref_rttm.keys()):
    recording_rttm = get_segments_explicit_overlap(recordings_ref_rttm[recording_id])
    recording_segments = recordings_segments[recording_id]
    for segment in recording_segments:
      utterance_id = segment['utterance_id']
      begin = segment['begin']
      end = segment['end']
      #print(utterance_id, begin, end)
      segment_rttm = filter(lambda rttm: rttm.has_timestamps_overlap(begin, end), recording_rttm)
      normalized_rttm = []
      for rttm in segment_rttm:
        new_rttm = Segment(rttm)
        if new_rttm.get_turn_onset() < begin:
          new_rttm.set_turn_onset(begin)
        if new_rttm.get_turn_end() > end:
          new_rttm.set_turn_end(end)
        normalized_rttm.append(new_rttm)
      for rttm in normalized_rttm:
        print(rttm.get_rttm(), end = '')

if __name__ == '__main__':
  main()

