#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import argparse
import sys
import pathlib
import re
import subprocess

from models import Segment, sort_segments_by_file_id, get_segments_union, read_wav_scp

def get_args():
  parser = argparse.ArgumentParser(description='')
  parser.add_argument('wav_scp', type=str, help='')
  parser.add_argument('output_folder', type=str, help='')
  parser.add_argument('mfcc_conf', type=str, help='')
  parser.add_argument('extractor_model', type=str, help='')
  parser.add_argument('--skip-extractor', type=bool, default=False, help='')
  args = parser.parse_args()
  return args

def get_stdin():
  return sys.stdin

def main():
  args = get_args()
  stdin = get_stdin()

  segments = [Segment(line) for line in stdin]
  files_segments = sort_segments_by_file_id(segments)
  wav_scp = read_wav_scp(args.wav_scp)

  segments_data = ''
  utt2spk_data = ''
  spk2utt_data = ''
  wav_scp_data = ''
  for index, file_id in enumerate(sorted(files_segments.keys())):
    print(index + 1, '/', len(files_segments.keys()), file_id, end = '\r')
    file_segments = get_segments_union(files_segments[file_id])
    file_scp = wav_scp[file_id]
    count = 0
    spk2utt_data += file_id
    for segment in file_segments:
      print(segment.get_turn_duration())
      utt = file_id + '_' + str(count).zfill(5)
      segments_data += utt + ' ' + file_id + ' ' + \
      str(round(segment.get_turn_onset(), 3)) + ' ' + \
      str(round(segment.get_turn_end(), 3)) + '\n'
      utt2spk_data += utt + ' ' + file_id + '\n'
      spk2utt_data += ' ' + utt
      count += 1
    spk2utt_data += '\n'
    wav_scp_data += file_scp.get_string()

  names = re.findall("augmented_\d+", args.wav_scp)
  data_folder = args.output_folder + (names[0] + '/' if len(names) > 0 else 'exp/')  
  pathlib.Path(data_folder).mkdir(parents = True, exist_ok = True)

  f = open(data_folder + 'segments', 'w')
  f.write(segments_data)
  f.close()
  f = open(data_folder + 'utt2spk', 'w')
  f.write(utt2spk_data)
  f.close()
  f = open(data_folder + 'spk2utt', 'w')
  f.write(spk2utt_data)
  f.close()
  f = open(data_folder + 'wav.scp', 'w')
  f.write(wav_scp_data)
  f.close()

  if not args.skip_extractor:
    subprocess.run(['./ivector_extract.sh', data_folder, args.mfcc_conf, args.extractor_model])

if __name__ == '__main__':
  main()
