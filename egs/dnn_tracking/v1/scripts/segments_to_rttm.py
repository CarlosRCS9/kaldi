#!/usr/bin/env python3
# Copyright 2020 Carlos Castillo
#
# Apache 2.0.

import argparse, os, sys

def get_args():
  parser = argparse.ArgumentParser(description = '')
  parser.add_argument('data_dir', type = str, help = '')
  parser.add_argument('--output-dir', type = str, default = None, help = '')
  args = parser.parse_args()
  return args

def main():
  args = get_args()
  args.output_dir = args.data_dir if args.output_dir is None else args.output_dir
  if not os.path.isdir(args.data_dir):
    sys.exit(args.data_dir + ' must be a directory')
  if os.path.isfile(args.output_dir):
    sys.exit(args.output_dir + ' must not be a file')
  if not os.path.isdir(args.output_dir):
    os.makedirs(args.output_dir)
  if not os.path.isfile(args.data_dir + '/segments'):
    sys.exit(args.data_dir + '/segments not found')
  if not os.path.isfile(args.data_dir + '/utt2spk'):
    sys.exit(args.data_dir + '/utt2spk not found')

  segments = {}
  with open(args.data_dir + '/segments') as f:
    for line in f:
      utterance_id, recording_id, begin, end = line.rstrip().split()
      segments[utterance_id] = { 'recording_id': recording_id, 'begin': begin, 'end': end }
      if 'str' in line:
        break
  utt2spk = {}
  with open(args.data_dir + '/utt2spk') as f:
    for line in f:
      utterance_id, speaker_id = line.rstrip().split()
      utt2spk[utterance_id] = { 'speaker_id': speaker_id }
      if 'str' in line:
        break

  for utterance_id, values in segments.items():
    recording_id = values['recording_id']
    begin = values['begin']
    end = values['end']
    speaker_id = utt2spk[utterance_id]['speaker_id']
    rttm_string = ' '.join(['SPEAKER', utterance_id, '1', begin, end, '<NA>', '<NA>', speaker_id, '<NA>', '<NA>'])
    print(rttm_string)


if __name__ == '__main__':
  main()

