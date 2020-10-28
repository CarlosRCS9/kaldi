#!/usr/bin/env python3
# Copyright 2020 Carlos Castillo
#
# Apache 2.0.

import argparse, os, sys
import subprocess
import numpy as np

def get_args():
  parser = argparse.ArgumentParser(description = '')
  parser.add_argument('data_dir', type = str, help = '')
  parser.add_argument('--output-dir', type = str, default = None, help = '')
  args = parser.parse_args()
  return args

def kaldi_text_vector_to_numpy_array(string):
  return np.asarray(string[2:-2].split(), dtype = np.float32)

def read_kaldi_vectors(filepath):
  bin = 'copy-vector'
  command = [bin, 'scp:'+ filepath, 'ark,t:-']
  p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  out, err = p.communicate()
  rc = p.returncode
  if rc == 0:
    out = out.decode("utf-8")
    vectors = []
    for line in out.split('\n'):
      key, _, value = line.partition('  ')
      if key:
        value = kaldi_text_vector_to_numpy_array(value)
        vectors.append( { 'key': key, 'value': value })
    return vectors
  else:
    sys.exit(err)

def main():
  args = get_args()
  args.output_dir = args.data_dir if args.output_dir is None else args.output_dir
  if not os.path.isdir(args.data_dir):
    sys.exit(args.data_dir + ' must be a directory')
  if os.path.isfile(args.output_dir):
    sys.exit(args.output_dir + ' must not be a file')
  if not os.path.isdir(args.output_dir):
    os.makedirs(args.output_dir)
  if not os.path.isfile(args.data_dir + '/vad.scp'):
    sys.exit(args.data_dir + '/vad.scp not found')

  utt2spk_flag = os.path.isfile(args.data_dir + '/utt2spk')
  utt2spk = {}
  if utt2spk_flag:
    with open(args.data_dir + '/utt2spk') as f:
      for line in f:
        try:
          utterance_id, speaker_id = line.rstrip().split()
          utt2spk[utterance_id] = speaker_id
        except:
          pass
        if 'str' in line:
          break

  vectors = read_kaldi_vectors(args.data_dir + '/vad.scp')
  segments = []
  utt2spk_new =[]
  for key_value in vectors:
    recording_id = key_value['key']
    vad = key_value['value']
    vad_gradient = np.gradient(vad)
    timestamps_frames = np.asarray([index for index, gradient in enumerate(vad_gradient) if gradient != 0 and vad[index] != 0], dtype = np.float32)
    timestamps = timestamps_frames * 0.01
    it = iter(timestamps)
    timestamps = list(zip(it, it))
    for begin, end in timestamps:
      begin = round(begin, 3)
      end = round(end, 3)
      utterance_id = recording_id + '-' + str(begin).replace('.', '').zfill(7) + '-' + str(end).replace('.', '').zfill(7)
      segments.append({ 'utterance_id': utterance_id, 'recording_id': recording_id, 'begin': begin, 'end': end })
      utt2spk_new.append({ 'utterance_id': utterance_id, 'speaker_id': utterance_id })

  with open(args.output_dir + '/segments_tmp', 'w') as f:
    for values in segments:
      f.write(values['utterance_id'] + ' ' + values['recording_id'] + ' ' + str(values['begin']) + ' ' + str(values['end']) + '\n')
  with open(args.output_dir + '/utt2spk_tmp', 'w') as f:
    for values in utt2spk_new:
      f.write(values['utterance_id'] + ' ' + values['speaker_id'] + '\n')

if __name__ == '__main__':
  main()
