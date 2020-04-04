#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.
 
import argparse
import sys
from functools import reduce
from itertools import chain

from models import Segment

def get_args():
  parser = argparse.ArgumentParser(description='This script is used to split a NIST RTTM file into \
                                                a series of non-overlapping pure single-speaker and \
                                                multiple-speakers segments.')
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
  stdin = get_stdin()
  segments = [Segment(line) for line in stdin]
  recordings_segments = reduce(get_recordings_segments, segments, {})
  for recording_id  in recordings_segments:
    recording_segments = recordings_segments[recording_id]
    timestamps = sorted(chain(*[(segment.begining, segment.ending) for segment in recording_segments]))
    for index in range(len(timestamps) - 1):
      overlap_segments = [segment for segment in recording_segments if segment.timestamps_overlap(timestamps[index], timestamps[index + 1])]

if __name__ == '__main__':
  main()
