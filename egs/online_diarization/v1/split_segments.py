#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import argparse
import sys
import os
import json
import subprocess

def get_args():
  parser = argparse.ArgumentParser(description='This script cuts the segments data to a given length and overlap.')
  parser.add_argument('input_mode', type=str, help='json or rttm.')
  parser.add_argument('output_dir', type=str, help='The output directory.')
  parser.add_argument('--segment-length', type=float, default=0.0, help='Max segment length.')
  parser.add_argument('--segment-overlap', type=float, default=0.0, help='Overlap length between segments.')
  args = parser.parse_args()
  return args

def get_stdin():
  return sys.stdin

def main():
  args = get_args()
  stdin = get_stdin()
  output_dir = args.output_dir

  try:
    os.makedirs(output_dir, exist_ok = True)
  except OSError:
    exit(OSError)

  if args.input_mode == 'json':
    jsons = [json.loads(line) for line in stdin]
    if len(jsons) == 1:
      file_segments = ''
      file_utt2spk = ''
      file_spk2utt = ''
      file_wav_scp = ''
      recordings = jsons[0]
      recordings_ids = [recording['recording_id'] for recording in recordings]
      for recording in recordings:
        count = 0
        file_spk2utt += recording['recording_id']
        for segment in recording['segments']:
          id = ''.join([recording['recording_id'], '_', str(count).zfill(3)])
          file_segments += ' '.join([id, recording['recording_id'], str(segment['begining']), str(segment['ending'])]) + '\n'
          file_utt2spk += ' '.join([id, recording['recording_id']]) + '\n'
          file_spk2utt += ' ' + id
          count += 1
        file_spk2utt += '\n'
      f = open(output_dir + '/segments', 'w')
      f.write(file_segments)
      f.close()
      f = open(output_dir + '/utt2spk', 'w')
      f.write(file_utt2spk)
      f.close()
      f = open(output_dir + '/spk2utt', 'w')
      f.write(file_spk2utt)
      f.close()
      f = open(output_dir + '/wav.scp', 'r')
      for line in f.readlines():
        if line.split(' ')[0] in recordings_ids:
          file_wav_scp += line
      f.close()
      f = open(output_dir + '/wav.scp', 'w')
      f.write(file_wav_scp)
      f.close()
    else:
      exit('Too many jsons.' if len(stdin) > 0 else 'Missing input json.')
  else:
    exit('Unknown input mode.')

if __name__ == '__main__':
  main()

