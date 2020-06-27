#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import sys

def get_stdin():
  return sys.stdin

def main():
  stdin = get_stdin()
  last_recording_id = ''
  speaker_id_map = {}
  speaker_id_count = 0
  for line in stdin:
    values = line.split(' ')
    recording_id = values[1]
    speaker_id = values[7]
    if last_recording_id != recording_id:
      last_recording_id = recording_id
      speaker_id_map = {}
      speaker_id_count = 0
    if speaker_id not in  speaker_id_map:
      speaker_id_map[speaker_id] = speaker_id_count
      speaker_id_count += 1
    values[7] = chr(65 + speaker_id_map[speaker_id])
    print(' '.join(values), end = '')

if __name__ == '__main__':
  main()

