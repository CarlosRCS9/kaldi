#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import argparse
import sys
from functools import reduce

from models import Segment

def get_args():
  parser = argparse.ArgumentParser(description='')
  args = parser.parse_args()
  return args

def get_stdin():
  return sys.stdin

def get_recordings_segments(acc, segment):
  if segment.recording_id not in acc:
    acc[segment.recording_id] = []
  acc[segment.recording_id].append(segment)
  return acc

def get_speakers_segments(acc, segment, valid_speakers = None):
  if valid_speakers is None or segment.speaker_id in valid_speakers:
    if segment.speaker_id not in acc:
      acc[segment.speaker_id] = []
    acc[segment.speaker_id].append(segment)
  return acc

def main():
  args = get_args()
  stdin = get_stdin()
  segments = [Segment(line) for line in stdin]
  recordings_segments = reduce(get_recordings_segments, segments, {})
  for recording_id in recordings_segments:
    recording_segments = recordings_segments[recording_id]
    speakers_segments = reduce(lambda acc, segment: get_speakers_segments(acc, segment, ['A', 'B']), recording_segments, {})
    print(recording_id)
    for speaker_id in speakers_segments:
      speaker_segments = speakers_segments[speaker_id]
      timestamps = [(round(segment.begining, 2), round(segment.ending, 2)) for segment in speaker_segments]
      print(speaker_id, timestamps)

if __name__ == '__main__':
  main()
