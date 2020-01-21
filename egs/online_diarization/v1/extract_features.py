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
  parser.add_argument('data_dir', type=str, help='The output data directory.')
  parser.add_argument('output_dir', type=str, help='The output features directory.')
  parser.add_argument('--segment-length', type=float, default=0.0, help='Max segment length.')
  parser.add_argument('--segment-overlap', type=float, default=0.0, help='Overlap length between segments.')
  args = parser.parse_args()
  return args

def get_stdin():
  return sys.stdin

def grep(word, filepath):
  bin = 'grep'
  p = subprocess.Popen([bin, word, filepath], stdout=subprocess.PIPE)
  output, err = p.communicate()
  rc = p.returncode
  if rc == 0:
    return output.decode("utf-8").split('\n')[:-1]
  else:
    exit('grep fail.')

def main():
  args = get_args()
  stdin = get_stdin()
  data_dir = args.data_dir
  output_dir = args.output_dir

  try:
    os.makedirs(data_dir, exist_ok = True)
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
          segment['segment_id'] = id
          count += 1
        file_spk2utt += '\n'
      # ----- Write files ----- #
      f = open(data_dir + '/segments', 'w')
      f.write(file_segments)
      f.close()
      f = open(data_dir + '/utt2spk', 'w')
      f.write(file_utt2spk)
      f.close()
      f = open(data_dir + '/spk2utt', 'w')
      f.write(file_spk2utt)
      f.close()
      f = open(data_dir + '/wav.scp', 'r')
      for line in f.readlines():
        if line.split(' ')[0] in recordings_ids:
          file_wav_scp += line
      f.close()
      f = open(data_dir + '/wav.scp', 'w')
      f.write(file_wav_scp)
      f.close()
      # ----- Extract features ----- #
      subprocess.run(['./extract_features.sh', data_dir, output_dir])
      # ----- Insert features ----- #
      '''f = open(output_dir + '/make_ivectors/ivector.txt')
      ivectors = [line for line in f.readlines()]
      f.close()
      f = open(output_dir + '/make_xvectors/xvector.txt')
      xvectors = [line for line in f.readlines()]
      f.close()
      print(len(ivectors))
      print(len(xvectors))'''
      recording_count = 0
      for recording in recordings:
        recording_id = recording['recording_id']
        ivectors = grep(recording_id, output_dir + '/make_ivectors/ivector.txt')
        xvectors = grep(recording_id, output_dir + '/make_xvectors/xvector.txt')
        for segment in recording['segments']:
          segment['ivectors'] = [{ 'ivector_id': ivector.split('  ')[0], 'value': [float(value) for value in ivector.split('  ')[1].split(' ')[1:-1]] } for ivector in ivectors if segment['segment_id'] in ivector]
          segment['xvectors'] = [{ 'xvector_id': xvector.split('  ')[0], 'value': [float(value) for value in xvector.split('  ')[1].split(' ')[1:-1]] } for xvector in xvectors if segment['segment_id'] in xvector]
        # ----- Writing files ----- #
        f = open(output_dir + '/' + recording_id + '.json', 'w')
        f.write(json.dumps(recording))
        f.close()
        # ----- Printing progress ----- #
        recording_count += 1
        sys.stdout.write('\r')
        sys.stdout.write(str(recording_count / len(recordings)))
        sys.stdout.flush()
    else:
      exit('Too many jsons.' if len(stdin) > 0 else 'Missing input json.')
  else:
    exit('Unknown input mode.')

if __name__ == '__main__':
  main()

