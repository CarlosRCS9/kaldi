#!/usr/bin/env python3
# Copyright 2021 Carlos Castillo
#
# Apache 2.0

import argparse, os, sys
sys.path.insert(0, './models')
from kaldi import Wav_scp, Utt2dur, Ref_rttm
import numpy as np

def get_args():
  parser = argparse.ArgumentParser(description = '')
  parser.add_argument('data_dir', type = str, help = '')
  args = parser.parse_args()
  return args

def main():
  args = get_args()
  if not os.path.isdir(args.data_dir):
    sys.exit(args.data_dir + ' must be a directory')
  if not os.path.isfile(args.data_dir + '/frame_shift'):
    sys.exit(args.data_dir + '/frame_shift not found')
  if not os.path.isfile(args.data_dir + '/wav.scp'):
    sys.exit(args.data_dir + '/wav.scp not found')
  if not os.path.isfile(args.data_dir + '/utt2dur'):
    sys.exit(args.data_dir + '/utt2dur not found')
  if not os.path.isfile(args.data_dir + '/ref.rttm'):
    sys.exit(args.data_dir + '/ref.rttm not found')

  f = open(args.data_dir + '/frame_shift', 'r')
  for line in f.readlines():
    frame_shift = np.float32(line.strip())
  f.close()

  recordings_wav_scp = {}
  f = open(args.data_dir + '/wav.scp', 'r')
  for line in f.readlines():
    wav_scp = Wav_scp(line)
    recordings_wav_scp[wav_scp.recording_id] = wav_scp
  f.close()

  recordings_utt2dur = {}
  f = open(args.data_dir + '/utt2dur', 'r')
  for line in f.readlines():
    utt2dur = Utt2dur(line)
    if utt2dur.utterance in recordings_wav_scp:
      recordings_utt2dur[utt2dur.utterance] = utt2dur
    else:
      print('ERROR: wav.scp mismatch with utt2dur')
      sys.exit()
  f.close()

  recordings_ref_rttm = {}
  f = open(args.data_dir + '/ref.rttm', 'r')
  for line in f.readlines():
    ref_rttm = Ref_rttm(line)
    if ref_rttm.file in recordings_utt2dur:
      if ref_rttm.file not in recordings_ref_rttm:
        recordings_ref_rttm[ref_rttm.file] = []
      if ref_rttm.get_end_time() - recordings_utt2dur[ref_rttm.file].get_duration_time() >= frame_shift:
        ref_rttm.set_end_time(recordings_utt2dur[ref_rttm.file].get_duration_time())
      recordings_ref_rttm[ref_rttm.file].append(ref_rttm)
  f.close()

  f = open(args.data_dir + '/ref.rttm', 'w')
  for recording_id in sorted(recordings_ref_rttm.keys()):
    ref_rttm_array = recordings_ref_rttm[recording_id]
    for ref_rttm in ref_rttm_array:
      f.write(ref_rttm.__str__() + '\n')
  f.close()
  
if __name__ == '__main__':
  main()
