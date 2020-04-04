#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.
 
import argparse
import sys
from functools import reduce
from itertools import chain

from models import Segment, Segment_complex

def get_args():
  parser = argparse.ArgumentParser(description='This script is used to split a NIST RTTM file into \
                                                a series of non-overlapping pure single-speaker and \
                                                multiple-speakers segments.')
  parser.add_argument('--overlap-speaker', type=str, default='true', help='If true multiple-speakers segments get the "Z" speaker id in the output.')
  parser.add_argument('--min-segment', type=float, default=0.5, help='The minimal segment length required in the output.')
  args = parser.parse_args()
  return args

def get_stdin():
  return sys.stdin

def get_recordings_segments(acc, segment):
  if segment.recording_id not in acc:
    acc[segment.recording_id] = []
  acc[segment.recording_id].append(segment)
  return acc

def main():
  args = get_args()
  args.overlap_speaker = args.overlap_speaker.lower() == 'true'
  stdin = get_stdin()
  segments = [Segment(line) for line in stdin]
  recordings_segments = reduce(get_recordings_segments, segments, {})
  for recording_id  in recordings_segments:
    recording_segments = recordings_segments[recording_id]
    timestamps = sorted(chain(*[(segment.begining, segment.ending) for segment in recording_segments]))
    segments_complex = []
    for index in range(len(timestamps) - 1):
      overlap_segments = [segment for segment in recording_segments if segment.overlap(timestamps[index], timestamps[index + 1])]
      if len(overlap_segments) > 0:
        segment_complex = Segment_complex(overlap_segments[0], timestamps[index], timestamps[index + 1])
        for segment in overlap_segments[1:]:
          segment_complex.add_segment(segment)
        segments_complex.append(segment_complex)
    segments_complex_reduced = [segments_complex[0]]
    for index in range(1, len(segments_complex)):
      if segments_complex_reduced[-1].ending == segments_complex[index].begining and segments_complex_reduced[-1].same_speakers(segments_complex[index]):
        segments_complex_reduced[-1].mix_segment_complex(segments_complex[index])
      else:
        segments_complex_reduced.append(segments_complex[index])
    segments_complex_reduced = [segment for segment in segments_complex_reduced if segment.duration > args.min_segment]
    for segment in segments_complex_reduced:
      print(segment.get_rttm(args.overlap_speaker))

if __name__ == '__main__':
  main()
