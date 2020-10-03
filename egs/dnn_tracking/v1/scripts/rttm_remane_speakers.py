#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import sys

from models import Speaker, Segment, sort_segments_by_file_id, get_segments_explicit_overlap

def get_stdin():
  return sys.stdin

def main():
  stdin = get_stdin()
  segments = []
  for line in stdin:
    try:
      segments.append(Segment(line))
    except:
      pass
  speakers_count = 0
  speakers_map = {}
  files_segments = sort_segments_by_file_id(segments)
  for file_id in sorted(files_segments.keys()):
    file_segments = files_segments[file_id]
    new_file_segments = get_segments_explicit_overlap(file_segments)
    for segment in new_file_segments:
      speaker_real = ''.join([speaker for speaker in sorted([speaker.get_name() for speaker in segment.get_speakers()])])
      if speaker_real not in speakers_map:
        speakers_map[speaker_real] = 'speaker' + str(speakers_count).zfill(5)
        speakers_count += 1
      speaker = Speaker(segment.get_speakers()[0])
      speaker.set_name(speakers_map[speaker_real])
      segment.set_speakers([speaker])
      '''for speaker in segment.get_speakers():
        if speaker.get_name() not in speakers_map:
          speakers_map[speaker.get_name()] = 'speaker' + str(speakers_count).zfill(5)
          speakers_count += 1
        speaker.set_name(speakers_map[speaker.get_name()])'''
      print(segment.get_rttm(), end = '')

if __name__ == '__main__':
  main()
