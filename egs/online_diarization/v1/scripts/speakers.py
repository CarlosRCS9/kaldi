#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import argparse
import sys

def get_args():
  parser = argparse.ArgumentParser(description='')
  args = parser.parse_args()
  return args

def get_stdin():
  return sys.stdin

speakers_map = {}
def main():
  args = get_args()
  stdin = get_stdin()
  for line in stdin:
    line_data = line.split(' ')
    recording_id = line_data[1]
    speaker_id = line_data[7]
    if speaker_id not in speakers_map:
      speakers_map[speaker_id] = []
    if recording_id not in speakers_map[speaker_id]:
      speakers_map[speaker_id].append(recording_id)
  for speaker_id in speakers_map:
    print(speaker_id, len(speakers_map[speaker_id]))

if __name__ == '__main__':
  main()
