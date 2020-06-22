#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import argparse
import sys

from models import read_wav_scp, \
Segment, \
sort_segments_by_file_id, \
get_segments_explicit_overlap, \
sort_segments_by_speakers, \
filter_by_speakers_length
from sox import cut_and_stitch

def get_args():
  parser = argparse.ArgumentParser(description='')
  parser.add_argument('wav_scp', type=str, help='')
  parser.add_argument('output_folder', type=str, help='')
  args = parser.parse_args()
  return args

def get_stdin():
  return sys.stdin

def main():
  args = get_args()
  stdin = get_stdin()

  wav_scp = read_wav_scp(args.wav_scp)
  output_folder = args.output_folder

  segments = [Segment(line) for line in stdin]
  files_segments = sort_segments_by_file_id(segments)
  for index, file_id in enumerate(sorted(files_segments.keys())):
    print(index + 1, '/', len(files_segments.keys()), file_id, end = '\r')
    file_scp = wav_scp[file_id]
    file_segments = files_segments[file_id]
    file_segments = get_segments_explicit_overlap(file_segments, 0.1)
    speakers_segments = sort_segments_by_speakers(file_segments)
    single_speakers_segments = filter_by_speakers_length(speakers_segments, 1)
    single_speakers_files = {}
    for speaker_name in single_speakers_segments:
      speaker_filepath = output_folder + file_scp.get_file_id() + '_' + speaker_name + '.' + file_scp.get_format()
      speaker_segments = single_speakers_segments[speaker_name]
      timestamps_pairs = [(segment.get_turn_onset(), segment.get_turn_duration()) for segment in speaker_segments]
      speaker_filepath, speaker_filepath_duration = cut_and_stitch(file_scp, timestamps_pairs, speaker_filepath)
      turn_onset = 0
      new_speaker_segments = []
      for segment in speaker_segments:
        new_segment = Segment(segment)
        new_segment.set_turn_onset(turn_onset)
        new_speaker_segments.append(new_segment)
        turn_onset = new_segment.get_turn_end()
      single_speakers_files[speaker_name] = { 'filepath': speaker_filepath, 'duration': speaker_filepath_duration, 'segments': new_speaker_segments }

if __name__ == '__main__':
  main()
