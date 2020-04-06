#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import argparse
import itertools
import json
import math
import os
import random
import re
import subprocess
import sys

from copy import deepcopy
from functools import reduce
from itertools import chain
from models import Segment_complex

def get_args():
  parser = argparse.ArgumentParser(description='')
  parser.add_argument('scp', type=str, help='The audio files locations in scp format.')
  parser.add_argument('output_folder', type=str, help='The folder where the generated audios will be placed.')
  args = parser.parse_args()
  return args

def get_stdin():
  return sys.stdin

def read_scp(filepath):
  f = open(filepath, 'r')
  scp = [line.split(' ') for line in f.readlines()]
  f.close()
  scp_line = scp[0]
  scp_filepath_index = [re.match(r'(\/.*?\.[\w:]+)', word) is not None for word in scp_line].index(True)
  return dict([(line[0], line[scp_filepath_index]) for line in scp])

def get_recordings_segments(acc, segment):
  if segment.recording_id not in acc:
    acc[segment.recording_id] = []
  acc[segment.recording_id].append(segment)
  return acc

def get_speakers_segments(acc, segment, valid_speakers = None):
  if len(segment.speakers) == 1 and (valid_speakers is None or segment.speakers[0].speaker_id in valid_speakers):
    if segment.speakers[0].speaker_id not in acc:
      acc[segment.speakers[0].speaker_id] = []
    acc[segment.speakers[0].speaker_id].append(segment)
  return acc

def sox_stich_audio(input_filepath, timestamps, output_filepath):
  if not os.path.exists(output_filepath):
    extension = input_filepath.split('.')[-1]
    trims = ['|sox ' + input_filepath + ' -t ' + extension + ' - trim ' + str(timestamp[0]) + ' ' + str(timestamp[1]) for timestamp in timestamps]
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
    length = float(output.decode("utf-8"))
    return (output_filepath, length)

def sox_mix_audio(input_filepaths, min_duration, output_filepath):
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
    length = float(output.decode("utf-8"))
    return (output_filepath, length)

def main():
  args = get_args()
  stdin = get_stdin()
  scp = read_scp(args.scp)
  segments = [Segment_complex(json.loads(line)) for line in stdin]
  recordings_segments = reduce(get_recordings_segments, segments, {})
  for recording_id in sorted(list(recordings_segments.keys())):
    recording_extension = scp[recording_id].split('.')[-1]
    recording_segments = sorted(recordings_segments[recording_id], key = lambda segment: segment.begining)
    speakers_segments = reduce(lambda acc, segment: get_speakers_segments(acc, segment, ['A', 'B', 'B1']), recording_segments, {})
    speakers_stiched = {}
    for speaker_id in speakers_segments:
      speaker_segments = speakers_segments[speaker_id]
      timestamps = sorted([(round(segment.begining, 2), round(segment.duration, 2)) for segment in speaker_segments], key = lambda tuple: tuple[0])
      filepath = args.output_folder + recording_id + '_' + speaker_id + '.' + recording_extension
      filepath, duration = sox_stich_audio(scp[recording_id], timestamps, filepath)
      speakers_stiched[speaker_id] = { 'filepath': filepath, 'duration': math.floor(duration * 100) / 100.0 }

    combinations_timestamps = []
    for combination in [sorted(combination) for combination in list(itertools.combinations([speaker_id for speaker_id in speakers_stiched], 2))]:
      filepaths = [speakers_stiched[speaker_id]['filepath'] for speaker_id in combination]
      durations = [speakers_stiched[speaker_id]['duration'] for speaker_id in combination]
      min_duration = min(durations)
      filepath = args.output_folder + recording_id + '_'.join([''] + combination) + '.' + recording_extension
      filepath, min_duration = (sox_mix_audio(filepaths, min_duration, filepath))
      
      left_duration = min_duration
      split_durations = []
      while left_duration > 1.5:
        duration = math.floor(math.sqrt(left_duration) * 100) / 100.0
        split_durations.append(duration)
        left_duration -= duration
      split_durations.append(round(left_duration, 2))
      split_beginings = [round(sum(split_durations[:index]), 2) for index, duration in enumerate(split_durations)]
      split_timestamps = list(zip(split_beginings, split_durations))
      combinations_timestamps.append((combination, filepath, split_timestamps))

    combinations_timestamps = [[{ 'combination': combination, 'filepath': filepath, 'timestamp': timestamp } for timestamp in timestamps] for combination, filepath, timestamps in combinations_timestamps]
    combinations_timestamps_lengths = [len(combination_timestamps) for combination_timestamps in combinations_timestamps]
    combinations_timestamps_mix = []
    while sum(combinations_timestamps_lengths) > 0:
      combinations_indexes = list(chain(*[[index] * len(combination_timestamps) for index, combination_timestamps in enumerate(combinations_timestamps)]))
      combination_index = random.choice(combinations_indexes)
      combinations_timestamps_mix.append(combinations_timestamps[combination_index].pop(0))
      combinations_timestamps_lengths = [len(combination_timestamps) for combination_timestamps in combinations_timestamps]
    

    new_recording_segments = deepcopy(recording_segments)
    print(recording_id)
    print(len(new_recording_segments))
    print(len(combinations_timestamps_mix))

if __name__ == '__main__':
  main()
