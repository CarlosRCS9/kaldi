#!/usr/bin/env python3
# Copyright 2020 Carlos Castillo
#
# Apache 2.0.

import argparse, os, sys
import numpy as np
from models import Segment, sort_segments_by_file_id, get_segments_explicit_overlap

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
  if not os.path.isfile(args.data_dir + '/ref.rttm'):
    sys.exit(args.data_dir + '/ref.rttm not found')
  if not os.path.isfile(args.data_dir + '/utt2num_frames'):
    sys.exit(args.data_dir + '/utt2num_frames not found')
  if not os.path.isfile(args.data_dir + '/utt2dur'):
    sys.exit(args.data_dir + '/utt2dur not found')

  ref_rttm = []
  f = open(args.data_dir + '/ref.rttm', 'r')
  for line in f.readlines():
    try:
      ref_rttm.append(Segment(line))
    except:
      pass
  f.close()

  utt2num_frames = {}
  f = open(args.data_dir + '/utt2num_frames')
  for line in f.readlines():
    try:
      utterance_id, num_frames = line.rstrip().split()
      utt2num_frames[utterance_id] = int(num_frames)
    except:
      pass
  f.close()

  utt2dur = {}
  f = open(args.data_dir + '/utt2dur', 'r')
  for line in f.readlines():
    try:
      utterance_id, duration = line.rstrip().split()
      utt2dur[utterance_id] = float(duration)
    except:
      pass
  f.close()

  recordings_ref_rttm = sort_segments_by_file_id(ref_rttm)
  recordings_vad = {}
  for recording_id in sorted(recordings_ref_rttm.keys()):
    number_of_frames = utt2num_frames[recording_id]
    duration = utt2dur[recording_id]
    frames_per_second = np.round(number_of_frames / duration).astype(int)
    frame_duration = 1 / frames_per_second

    recording_ref_rttm =recordings_ref_rttm[recording_id]
    vad = np.zeros(number_of_frames)
    for segment in recording_ref_rttm:
      begin_frame = np.floor(segment.get_turn_onset() * frames_per_second).astype(int)
      end_frame = np.ceil(segment.get_turn_end() * frames_per_second).astype(int)
      ones = np.concatenate([np.zeros(begin_frame), np.ones(end_frame - begin_frame), np.zeros(number_of_frames - end_frame)])
      vad += ones
    vad = (vad > 0).astype(int)
    recordings_vad[recording_id] = { 'value': vad, 'string': recording_id + '  [ ' + ' '.join([str(value) for value in vad]) + ' ]' }

  os.makedirs(args.output_dir + '/data', exist_ok = True)
  f_vad_scp = open(args.output_dir + '/vad.scp', 'w')
  recordings_count = 0
  for recording_id in sorted(recordings_vad.keys()):
    #ark_filepath = args.output_dir + '/data/ark.' + str(recordings_count) + '.ark'
    ark_filepath = args.output_dir + '/data/' + recording_id + '.sad'
    f_vad_scp.write(recording_id + ' ' + os.path.abspath(ark_filepath) + ':' + str(len(recording_id) + 2) + '\n')
    f = open(ark_filepath, 'w')
    f.write(recordings_vad[recording_id]['string'] + '\n')
    f.close()
    recordings_count += 1
  f_vad_scp.close()

if __name__ == '__main__':
  main()

