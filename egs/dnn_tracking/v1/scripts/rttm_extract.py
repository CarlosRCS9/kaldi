#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import sys

from models import Segment, sort_segments_by_file_id, get_segments_explicit_overlap

def get_stdin():
  return sys.stdin

def main():
  stdin = get_stdin()

  segments = [Segment(line) for line in stdin]
  files_segments = sort_segments_by_file_id(segments)

  segments_data = ''
  utt2spk_data = ''
  for index, file_id in enumerate(sorted(files_segments.keys())):
    print(index + 1, '/', len(files_segments.keys()), file_id, end = '\r')
    file_segments = get_segments_explicit_overlap(files_segments[file_id])
    count = 0
    for segment in file_segments:
      utt = segment.get_file_id() + '_' + str(count)
      segments_data += \
      utt + ' ' + \
      segment.get_file_id() + ' ' + \
      str(round(segment.get_turn_onset(), 3)) + ' ' + \
      str(round(segment.get_turn_end(), 3)) + '\n'
      utt2spk_data += utt + ' ' + segment.get_file_id() + '\n'
      count += 1
    break

  #print(segments_data, end = '')
  print(utt2spk_data, end = '')

if __name__ == '__main__':
  main()
