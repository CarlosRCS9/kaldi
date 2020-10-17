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
        utterance_id, recording_id, onset, end = line.rstrip().split()
        onset = np.float32(onset)
        end = np.float32(end)
        if recording_id not in recordings_segments:
          recordings_segments[recording_id] = []
        recordings_segments[recording_id].append({ 'utterance_id': utterance_id, 'onset': onset, 'end': end })
      except:
        pass
      if 'str' in line:
        break

  recordings_rttm = sort_segments_by_file_id(ref_rttm)
  for recording_id in sorted(recordings_rttm.keys()):
    #rttm = get_segments_explicit_overlap(recordings_rttm[recording_id])
    rttm = recordings_rttm[recording_id]
    segments = recordings_segments[recording_id]
    for segment in segments:
      utterance_id = segment['utterance_id']
      onset = segment['onset']
      end = segment['end']
      #segment_rttm = list(filter(lambda rttm: end <= rttm.get_turn_onset() or rttm.get_turn_end() <= onset, rttm))
      segment_rttm = list(filter(lambda rttm: rttm.has_timestamps_overlap(onset, end), rttm))
      if len(segment_rttm) > 0:
        speaker_ids = set(itertools.chain(*[[speaker.get_name() for speaker in segment.get_speakers()] for segment in segment_rttm]))
        for speaker_id in speaker_ids:
          print(' '.join(['SPEAKER', recording_id, '1', str(onset), str(end - onset), '<NA>', '<NA>', speaker_id, '<NA>', '<NA>']))

if __name__ == '__main__':
  main()

