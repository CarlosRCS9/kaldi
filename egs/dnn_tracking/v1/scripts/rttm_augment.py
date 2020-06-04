#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import argparse
import sys

from models import Segment, sort_segments_by_file_id, get_segments_explicit_overlap, sort_segments_by_speakers, filter_by_speakers_length, Scp, sort_scps_by_file_id

def get_args():
  parser = argparse.ArgumentParser(description='')
  parser.add_argument('scp', type=str, help='')
  parser.add_argument('output_folder', type=str, help='')
  args = parser.parse_args()
  return args

def get_stdin():
  return sys.stdin

def read_scp(scp_filepath):
  f = open(scp_filepath, 'r')
  scps = [Scp(line) for line in f.readlines()]
  f.close()
  scps = sort_scps_by_file_id(scps)
  return scps

def sox_cut_and_stitch(scp, timestamps_pairs, output_filepath):
  trims = ['|sox ' + scp.get_filepath() + ' -t ' + scp.get_format() + ' - trim ' + str(onset) + ' ' + str(duration) for onset, duration in timestamps_pairs]
  command = ['sox'] + trims + [output_filepath]
  print(command)

def main():
  args = get_args()
  stdin = get_stdin()

  scps = read_scp(args.scp)
  output_folder = args.output_folder

  segments = [Segment(line) for line in stdin]
  files_segments = sort_segments_by_file_id(segments)
  files_segments = get_segments_explicit_overlap(files_segments)
  for file_id in sorted(files_segments.keys()):
    file_scp = scps[file_id]
    file_segments = files_segments[file_id]
    speakers_segments = sort_segments_by_speakers(file_segments)
    single_speakers_segments = filter_by_speakers_length(speakers_segments, 1)
    for speaker_name in single_speakers_segments.keys():
      speaker_filepath = output_folder + file_scp.get_file_id() + '_' + speaker_name + '.' + file_scp.get_format()
      segments = single_speakers_segments[speaker_name]
      timestamps_pairs = [(segment.get_turn_onset(), segment.get_turn_duration()) for segment in segments]
      sox_cut_and_stitch(file_scp, timestamps_pairs, speaker_filepath)
    break

if __name__ == '__main__':
  main()
