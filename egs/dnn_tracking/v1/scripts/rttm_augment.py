#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import argparse
import sys
import os
import numpy
import subprocess
import itertools
import math
import random

random_seed = 0
random.seed(random_seed)

from models import Speaker, Segment, sort_segments_by_file_id, get_segments_explicit_overlap, sort_segments_by_speakers, filter_by_speakers_length, Scp, sort_scps_by_file_id

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
  if not os.path.exists(output_filepath):
    trims = ['|sox ' + scp.get_filepath() + ' -t ' + scp.get_format() + ' - trim ' + str(onset) + ' ' + str(duration) for onset, duration in timestamps_pairs]
    command = ['sox'] + trims + [output_filepath]
    p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = p.communicate()
    rc = p.returncode
    if rc != 0:
      print(err)
      exit(1)
  command = ['soxi', '-D', output_filepath]
  p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  output, err = p.communicate()
  rc = p.returncode
  if rc != 0:
    print(err)
    exit(1)
  else:
    duration = numpy.float32(output.decode("utf-8"))
    return (output_filepath, duration)

def sox_mix_files(input_filepaths, min_duration, output_filepath):
  if not os.path.exists(output_filepath):
    trims = ['|sox ' + filepath + ' -t ' + filepath.split('.')[-1] + ' - trim 0 ' + str(min_duration) for filepath in input_filepaths]
    command = ['sox', '-m'] + trims + [output_filepath]
    p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = p.communicate()
    rc = p.returncode
    if rc != 0:
      print(err)
      exit(1)
  command = ['soxi', '-D', output_filepath]
  p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  output, err = p.communicate()
  rc = p.returncode
  if rc != 0:
    print(err)
    exit(1)
  else:
    duration = numpy.float32(output.decode("utf-8"))
    return (output_filepath, duration)

def sox_stitch_trims(trims, output_filepath):
  #if not os.path.exists(output_filepath):
  if True:
    command = ['sox'] + trims + [output_filepath]
    p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = p.communicate()
    rc = p.returncode
    if rc != 0:
      print(err)
      exit(1)
  command = ['soxi', '-D', output_filepath]
  p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  output, err = p.communicate()
  rc = p.returncode
  if rc != 0:
    print(err)
    exit(1)
  else:
    duration = numpy.float32(output.decode("utf-8"))
    return (output_filepath, duration)

def segment_factory(data):
  rttm_line = 'SPEAKER a 0 0 0 <NA> <NA> a <NA> <NA>'
  file_id = data['file_id']
  onset = data['onset']
  duration = data['duration']
  speakers_names = data['speakers_names']
  data = rttm_line.split()
  data[1] = file_id
  data[3] = str(onset)
  data[4] = str(duration)
  line = ' '.join(data)
  segment = Segment(line)
  speakers = [Speaker(['<NA>', 'speaker_name', onset, duration]) for speaker_name in speakers_names]
  segment.set_speakers(speakers)
  return segment

def main():
  args = get_args()
  stdin = get_stdin()

  scps = read_scp(args.scp)
  output_folder = args.output_folder

  segments = [Segment(line) for line in stdin]
  files_segments = sort_segments_by_file_id(segments)
  files_segments = get_segments_explicit_overlap(files_segments)
  for index, file_id in enumerate(sorted(files_segments.keys())):
    file_scp = scps[file_id]
    file_segments = files_segments[file_id]
    speakers_segments = sort_segments_by_speakers(file_segments)
    single_speakers_segments = filter_by_speakers_length(speakers_segments, 1)
    single_speakers_files = {}
    for speaker_name in single_speakers_segments.keys():
      speaker_filepath = output_folder + file_scp.get_file_id() + '_' + speaker_name + '.' + file_scp.get_format()
      segments = single_speakers_segments[speaker_name]
      timestamps_pairs = [(segment.get_turn_onset(), segment.get_turn_duration()) for segment in segments]
      speaker_filepath, duration = sox_cut_and_stitch(file_scp, timestamps_pairs, speaker_filepath)
      single_speakers_files[speaker_name] = { 'filepath': speaker_filepath, 'duration': duration }

    combinations_files = {}
    for combination in [sorted(combination) for combination in list(itertools.combinations([speaker_name for speaker_name in single_speakers_files.keys()], 2))]:
      filepaths = [single_speakers_files[speaker_name]['filepath'] for speaker_name in combination]
      durations = [single_speakers_files[speaker_name]['duration'] for speaker_name in combination]
      min_duration = min(durations)
      combination_filepath = output_folder + file_scp.get_file_id() + '_'.join([''] + combination) + '.' + file_scp.get_format()
      combination_filepath, duration = sox_mix_files(filepaths, min_duration, combination_filepath)

      left_duration = min_duration
      cut_durations = []
      while left_duration > 1.5:
        cut_duration = math.floor(math.sqrt(left_duration) * 100.0) / 100.0
        cut_durations.append(cut_duration)
        left_duration -= cut_duration
      cut_durations.append(left_duration)
      cut_onsets = [sum(cut_durations[:index]) for index, cut_duration in enumerate(cut_durations)]
      timestamps_pairs = list(zip(cut_onsets, cut_durations))

      combinations_files[','.join(combination)] = { 'speakers_names': combination, 'filepath': combination_filepath, 'duration': duration, 'timestamps_pairs': timestamps_pairs }

    combinations_timestamps = []
    for _, combination in combinations_files.items():
      for onset, duration in combination['timestamps_pairs']:
        combinations_timestamps.append({ 'file_id': file_id, 'speakers_names': combination['speakers_names'], 'filepath': combination['filepath'], 'onset': onset, 'duration': duration })

    # DONE
    trims = []
    new_file_segments = []
    options = [file_segments, combinations_timestamps]
    options_lengths = [len(option) for option in options]
    # ----------

    original_file_pointer = 0
    while sum(options_lengths) > 0:
      # DONE -----
      options_indexes = list(itertools.chain(*[[index] * len(option) for index, option in enumerate(options)]))
      option_index = random.choice(options_indexes)
      option = options[option_index].pop(0)
      # ----------
      if option_index == 0:
        original_segment = option
        if original_segment.get_turn_onset() != original_file_pointer:
          print('WARNING: silence before segment.')
          print('original_segment.get_turn_onset()', original_segment.get_turn_onset(), 'original_file_pointer', original_file_pointer)
        original_file_pointer = original_segment.get_turn_end()
        updated_segment = original_segment
        new_file_segments.append(updated_segment)
        '''original_segment = option
        trims.append('|sox ' + file_scp.get_filepath() + ' -t ' + file_scp.get_format() + ' - trim ' + str(original_file_pointer) + ' ' + str(original_segment.get_turn_end() - original_file_pointer))
        original_file_pointer = options[option_index][0].get_turn_onset() if len(options[option_index]) > 0 else original_segment.get_turn_end()
        original_segment.add_turn_onset(new_file_displacement)
        new_file_segments.append(original_segment)'''
      else:
        '''new_segment = segment_factory(option)
        trims.append('|sox ' + option['filepath'] + ' -t ' + option['filepath'].split('.')[-1] + ' - trim ' + str(new_segment.get_turn_onset()) + ' ' + str(new_segment.get_turn_duration()))
        new_segment.update_turn_onset(new_file_segments[-1].get_turn_onset() + new_file_segments[-1].get_turn_duration() if len(new_file_segments) > 0 else 0)
        new_file_segments.append(new_segment)
        new_file_displacement += new_segment.get_turn_duration()'''
      
      # DONE
      options_lengths = [len(option) for option in options]
      # ----------

    '''new_filepath = output_folder + file_scp.get_file_id() + '_augmented_' + str(random_seed) + '.' + file_scp.get_format()
    new_filepath, duration = sox_stitch_trims(trims, new_filepath)

    if math.fabs(duration - new_file_segments[-1].get_turn_end()) > 0.1:
      print(sum([segment.get_turn_duration() for segment in new_file_segments]))
      print(new_filepath, duration, new_file_segments[-1].get_turn_end())'''

    break

if __name__ == '__main__':
  main()
