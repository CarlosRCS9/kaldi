#!/usr/bin/env python3
# Copyright 2021 Carlos Castillo
#
# Apache 2.0

import argparse, os, sys
sys.path.insert(0, './models')
from kaldi import Wav_scp, Utt2dur, Ref_rttm, Recording
import numpy as np

def get_args():
  parser = argparse.ArgumentParser(description = '')
  parser.add_argument('data_dir', type = str, help = '')
  parser.add_argument('output_dir', type = str, help = '')
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
  if os.path.isfile(args.output_dir):
    sys.exit(args.output_dir + ' must not be a regular file')
  if not os.path.isdir(args.output_dir):
    os.makedirs(args.output_dir)

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
    utt2dur = Utt2dur(line, frame_shift)
    recordings_utt2dur[utt2dur.utterance] = utt2dur
  f.close()

  recordings_ref_rttm = {}
  f = open(args.data_dir + '/ref.rttm', 'r')
  for line in f.readlines():
    ref_rttm = Ref_rttm(line)
    if ref_rttm.file not in recordings_ref_rttm:
      recordings_ref_rttm[ref_rttm.file] = []
    recordings_ref_rttm[ref_rttm.file].append(ref_rttm)
  f.close()

  recordings = {}
  for recording_id, ref_rttm_list in recordings_ref_rttm.items():
    recordings[recording_id] = Recording(ref_rttm_list)
    print(recordings[recording_id])
    break


  '''for recording_id, wav_scp in recordings_wav_scp.items():
    utt2dur = recordings_utt2dur[recording_id]
    ref_rttm = recordings_ref_rttm[recording_id]'''

if __name__ == '__main__':
  main()
