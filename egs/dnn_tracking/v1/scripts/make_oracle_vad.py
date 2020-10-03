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

  segments = []
  f = open(args.data_dir + '/ref.rttm', 'r')
  for line in f.readlines():
    try:
      segments.append(Segment(line))
    except:
      pass
  f.close()
  utterance_num_frames = {}
  f = open(args.data_dir + '/utt2num_frames')
  for line in f.readlines():
    try:
      utterance_id, num_frames = line.rstrip().split()
      utterance_num_frames[utterance_id] = int(num_frames)
    except:
      pass
  f.close()
  utterance_duration = {}
  f = open(args.data_dir + '/utt2dur', 'r')
  for line in f.readlines():
    try:
      utterance_id, duration = line.rstrip().split()
      utterance_duration[utterance_id] = float(duration)
    except:
      pass
  f.close()

  utterance_vad = {}
  utterance_vad_string = {}
  files_segments = sort_segments_by_file_id(segments)
  for file_id in sorted(files_segments.keys()):
    num_frames = utterance_num_frames[file_id]
    duration = utterance_duration[file_id] # seconds

    frames_per_second = np.round(num_frames / duration).astype(int)
    frame_duration = 1 / frames_per_second
    vad = np.zeros(num_frames)
    segments = get_segments_explicit_overlap(files_segments[file_id])
    for segment in segments:
      onset = segment.get_turn_onset()
      end = segment.get_turn_end()
      onset_frame = np.round(onset * frames_per_second).astype(int)
      end_frame = np.round(end * frames_per_second).astype(int)
      ones = np.concatenate([np.zeros(onset_frame), np.ones(end_frame - onset_frame), np.zeros(vad.size - end_frame)])
      vad += ones
    vad_string = file_id + '  [ ' + ' '.join([str(number) for number in vad.astype(int)]) + ' ]'
    utterance_vad[file_id] = vad
    utterance_vad_string[file_id] = vad_string

  os.makedirs(args.output_dir + '/data', exist_ok = True)
  f_scp = open(args.output_dir + '/vad.scp', 'w')
  utterance_count = 0
  for file_id in sorted(utterance_vad_string.keys()):
    ark_filepath = args.output_dir + '/data/vad.' + str(utterance_count) + '.ark'
    f_scp.write(file_id + ' ' + os.path.abspath(ark_filepath) + ':' + str(len(file_id) + 2) + '\n')
    f = open(ark_filepath, 'w')
    f.write(utterance_vad_string[file_id] + '\n')
    f.close()
    utterance_count += 1
  f_scp.close()

if __name__ == '__main__':
  main()

