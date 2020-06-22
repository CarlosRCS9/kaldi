#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import argparse
import sys
import itertools

from models import read_wav_scp, \
Segment, \
sort_segments_by_file_id, \
get_segments_explicit_overlap, \
sort_segments_by_speakers, \
filter_by_speakers_length, \
get_segments_explicit_overlap

from sox import cut_and_stitch, mix_files

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
    #print(index + 1, '/', len(files_segments.keys()), file_id, end = '\r')
    file_scp = wav_scp[file_id]
    file_segments = files_segments[file_id]
    file_segments = get_segments_explicit_overlap(file_segments, 0.1)
    speakers_segments = sort_segments_by_speakers(file_segments)
    single_speakers_segments = filter_by_speakers_length(speakers_segments, 1)
    single_speakers_files = {}
    for speaker_name in single_speakers_segments:
      filepath = output_folder + file_scp.get_file_id() + '_' + speaker_name + '.' + file_scp.get_format()
      speaker_segments = single_speakers_segments[speaker_name]
      timestamps_pairs = [(segment.get_turn_onset(), segment.get_turn_duration()) for segment in speaker_segments]
      filepath, duration = cut_and_stitch(file_scp, timestamps_pairs, filepath)
      turn_onset = 0
      new_speaker_segments = []
      for segment in speaker_segments:
        new_segment = Segment(segment)
        if len(new_speaker_segments) > 0 and new_speaker_segments[-1].has_same_speakers(new_segment):
          new_speaker_segments[-1].set_turn_duration(new_speaker_segments[-1].get_turn_duration() + new_segment.get_turn_duration())
        else:
          new_segment.set_turn_onset(turn_onset)
          new_speaker_segments.append(new_segment)
        turn_onset = new_speaker_segments[-1].get_turn_end()
      single_speakers_files[speaker_name] = { 'filepath': filepath, 'duration': duration, 'segments': new_speaker_segments }

    combination_files = {}
    for combination in [sorted(combination) for combination in list(itertools.combinations([speaker_name for speaker_name in single_speakers_files], 2))]:
      filepaths = [single_speakers_files[speaker_name]['filepath'] for speaker_name in combination]
      durations = [single_speakers_files[speaker_name]['duration'] for speaker_name in combination]
      min_duration = min(durations)
      '''segments = list(itertools.chain(*[list(filter(lambda segment: segment.get_turn_onset() < min_duration, single_speakers_files[speaker_name]['segments'])) for speaker_name in combination]))
      for segment in list(filter(lambda segment: segment.get_turn_end() > min_duration, segments)):
        segment.set_turn_end(min_duration)
      segments = get_segments_explicit_overlap(segments)'''
      filepath = output_folder + file_scp.get_file_id() + '_'.join([''] + combination) + '.' + file_scp.get_format()
      filepath, duration = mix_files(filepaths, min_duration, filepath)
      print(filepath, duration)

      #segments = list(itertools.chain(*[single_speakers_files[speaker_name]['segments'] for speaker_name in combination]))

if __name__ == '__main__':
  main()