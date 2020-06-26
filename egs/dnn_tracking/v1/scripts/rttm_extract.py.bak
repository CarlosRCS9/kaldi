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
    file_segments = ''
    file_utt2spk = ''
    file_spk2utt = ''
    file_wav_scp = ''
    segments = [json.loads(line) for line in stdin]
    '''for recording in recordings:
      file_spk2utt += recording['recording_id']
      for segment in recording['segments']:
        file_spk2utt += ' ' + id
      file_spk2utt += '\n'''
    recordings_ids = {}
    for segment in segments:
      if segment['recording_id'] not in recordings_ids:
        recordings_ids[segment['recording_id']] = { 'count': 0, 'segments_ids': [] }
      segment_id = ''.join([segment['recording_id'], '_', str(recordings_ids[segment['recording_id']]['count']).zfill(5)])
      file_segments += ' '.join([segment_id, segment['recording_id'], str(segment['begining']), str(segment['ending'])]) + '\n'
      file_utt2spk += ' '.join([segment_id, segment['recording_id']]) + '\n'
      recordings_ids[segment['recording_id']]['segments_ids'].append(segment_id)
      segment['segment_id'] = segment_id
      recordings_ids[segment['recording_id']]['count'] += 1
    recordings_ids_keys = list(recordings_ids.keys())
    recordings_ids_keys.sort()
    for key in recordings_ids_keys:
      file_spk2utt += key + ' ' + ' '.join(recordings_ids[key]['segments_ids']) + '\n'
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
    segments_count = 0
    for key in recordings_ids_keys:
      ivectors = grep(key, output_dir + '/make_ivectors/ivector.txt')
      xvectors = grep(key, output_dir + '/make_xvectors/xvector.txt')
      f = open(output_dir + '/json/' + key + '.json', 'w')
      for segment in list(filter(lambda segment: segment['recording_id'] == key, segments)):
        segment['ivectors'] = [{ 'ivector_id': ivector.split('  ')[0], 'value': [float(value) for value in ivector.split('  ')[1].split(' ')[1:-1]] } for ivector in ivectors if segment['segment_id'] in ivector]
        segment['xvectors'] = [{ 'xvector_id': xvector.split('  ')[0], 'value': [float(value) for value in xvector.split('  ')[1].split(' ')[1:-1]] } for xvector in xvectors if segment['segment_id'] in xvector]
        # ----- Writing file ----- #
        f.write(json.dumps(segment) + '\n')
        # ----- Printing progress ----- #
        segments_count += 1
        sys.stdout.write('\r')
        sys.stdout.write(str(segments_count / len(segments)) + '          ')
        sys.stdout.flush()
      f.close()
  else:
    exit('Unknown input mode.')

if __name__ == '__main__':
  main()

