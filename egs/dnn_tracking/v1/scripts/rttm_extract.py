#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import argparse
import sys
import pathlib
import shutil
import re

from models import Segment, sort_segments_by_file_id, get_segments_explicit_overlap

def get_args():
  parser = argparse.ArgumentParser(description='')
  parser.add_argument('wav_scp', type=str, help='')
  parser.add_argument('output_folder', type=str, help='')
  args = parser.parse_args()
  return args

def get_stdin():
  return sys.stdin

def main():
  args = get_args()
  stdin = get_stdin()

  segments = [Segment(line) for line in stdin]
  files_segments = sort_segments_by_file_id(segments)

  segments_data = ''
  utt2spk_data = ''
  spk2utt_data = ''
  for index, file_id in enumerate(sorted(files_segments.keys())):
    print(index + 1, '/', len(files_segments.keys()), file_id, end = '\r')
    file_segments = get_segments_explicit_overlap(files_segments[file_id])
    count = 0
    spk2utt_data += file_id
    for segment in file_segments:
      utt = file_id + '_' + str(count).zfill(5)
      segments_data += utt + ' ' + file_id + ' ' + \
      str(round(segment.get_turn_onset(), 3)) + ' ' + \
      str(round(segment.get_turn_end(), 3)) + '\n'
      utt2spk_data += utt + ' ' + file_id + '\n'
      spk2utt_data += ' ' + utt
      count += 1
    spk2utt_data += '\n'
    if index > 1:
      break


  names = re.findall("augmented_\d+", args.wav_scp)
  new_folder = args.output_folder + (names + '/' if len(names) > 0 else 'exp/')  
  pathlib.Path(new_folder).mkdir(parents = True, exist_ok = True)

  f = open(new_folder + 'segments', 'w')
  f.write(segments_data)
  f.close()
  f = open(new_folder + 'utt2spk', 'w')
  f.write(utt2spk_data)
  f.close()
  f = open(new_folder + 'spk2utt', 'w')
  f.write(spk2utt_data)
  f.close()
  shutil.copyfile(args.wav_scp, new_folder + 'wav.scp')

if __name__ == '__main__':
  main()
