#!/usr/bin/env python3
# Copyright 2021 Carlos Castillo
#
# Apache 2.0

from models import Rttm
import argparse, os
import numpy as np

def get_args():
  parser = argparse.ArgumentParser()
  parser.add_argument('data_dir', type = str)
  args = parser.parse_args()
  return args

def main ():
  args = get_args()
  if not os.path.isdir(args.data_dir):
    raise ValueError(f"{args.data_dir} must be a directory")
  if not os.path.isfile(args.data_dir + '/ref.rttm'):
    raise ValueError(f"{args.data_dir}/ref.rttm not found")
  if not os.path.isfile(args.data_dir + '/utt2dur'):
    raise ValueError(f"{args.data_dir}/utt2dur not found")
  if not os.path.isfile(args.data_dir + '/utt2num_frames'):
    raise ValueError(f"{args.data_dir}/utt2num_frames not found")
  with open(args.data_dir + '/ref.rttm', 'r') as f:
    lines = f.readlines()
    rttm = Rttm(lines)
  utt2dur = {}
  with open(args.data_dir + '/utt2dur', 'r') as f:
    lines = f.readlines()
    for line in lines:
      recording_id, duration = line.strip().split()
      utt2dur[recording_id] = np.float32(duration)
  utt2num_frames = {}
  with open(args.data_dir + '/utt2num_frames', 'r') as f:
    lines = f.readlines()
    for line in lines:
      recording_id, duration = line.strip().split()
      utt2num_frames[recording_id] = np.int32(duration)
  rttm.load_utt2dur(utt2dur)
  rttm.load_utt2num_frames(utt2num_frames)
  print(rttm)

if __name__ == '__main__':
  main()
