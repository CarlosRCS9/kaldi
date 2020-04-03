#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import argparse
import sys
import json
from functools import reduce
import itertools
import re
import subprocess

def get_args():
  parser = argparse.ArgumentParser(description='This script is used augment segments by overlapping speakers.')
  parser.add_argument('scp', type=str, help='The audio files locations in scp format.')
  parser.add_argument('output_folder', type=str, help='The folder where the generated audios will be placed.')
  args = parser.parse_args()
  return args

def get_stdin():
  return sys.stdin

def is_valid_segment(segment, maximum_speakers_length = 2, valid_speakers_ids = ['A', 'B']):
  speakers_ids = [speaker['speaker_id'] for speaker in segment['speakers']]
  speakers_ids = list(set(speakers_ids))
  return len(speakers_ids) <= maximum_speakers_length and \
      all(speaker_id in valid_speakers_ids for speaker_id in speakers_ids)

def sox_overlap(input1, input1_start, input1_duration, input2, input2_start, input2_duration, output_filepath):
  bin = './sox_overlap.sh'
  p = subprocess.Popen([bin,
    input1, input1_start, input1_duration,
    input2, input2_start, input2_duration,
    output_filepath], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  output, err = p.communicate()
  rc = p.returncode
  if rc == 0:
    output = output.decode("utf-8")
  else:
    exit('sox_overlap.sh fail')

def main():
  args = get_args()
  stdin = get_stdin()

  f = open(args.scp, 'r')
  scp = [line.split(' ') for line in f.readlines()]
  f.close()
  scp_line = scp[0]
  scp_filepath_index = [re.match(r'(\/.*?\.[\w:]+)', word) is not None for word in scp_line].index(True)
  scp = dict([(line[0], line[scp_filepath_index]) for line in scp])

  segments = []
  for line in stdin:
    segment_json = json.loads(line)
    if is_valid_segment(segment_json):
      segments.append(segment_json)

  recordings_segments_indexes = {}
  for index, segment in enumerate(segments):
    if segment['recording_id'] not in recordings_segments_indexes:
      recordings_segments_indexes[segment['recording_id']] = []
    recordings_segments_indexes[segment['recording_id']].append(index)

  file_wav_scp = ''
  for recording_id in sorted(list(recordings_segments_indexes.keys())):
    recording_segments_indexes = recordings_segments_indexes[recording_id]
    speakers_segments_indexes = {}
    for index in recording_segments_indexes:
      speakers_ids = ','.join(sorted(list(set([speaker['speaker_id'] for speaker in segments[index]['speakers']]))))
      if speakers_ids not in speakers_segments_indexes:
        speakers_segments_indexes[speakers_ids] = []
      speakers_segments_indexes[speakers_ids].append(index)
    single_speaker_segments_indexes = {}
    multiple_speakers_segments_indexes = {}
    for speakers_ids in speakers_segments_indexes:
      if len(speakers_ids.split(',')) > 1:
        multiple_speakers_segments_indexes[speakers_ids] = speakers_segments_indexes[speakers_ids]
      else:
        single_speaker_segments_indexes[speakers_ids] = speakers_segments_indexes[speakers_ids]

    min_single_speaker_segments_length = min([len(single_speaker_segments_indexes[speaker_id]) for speaker_id in single_speaker_segments_indexes])
    single_speaker_combinations = [sorted(combination) for combination in list(itertools.combinations([speaker_id for speaker_id in single_speaker_segments_indexes], 2))]
    
    combination_segments = []
    for combination in single_speaker_combinations:
      combination_speakers_segments_lengths = [len(single_speaker_segments_indexes[speaker_id]) for speaker_id in combination]

      # required if the generated length must be equal to the minimal length of segments of a speaker
      generate_length = min_single_speaker_segments_length - (len(multiple_speakers_segments_indexes[','.join(combination)]) if ','.join(combination) in multiple_speakers_segments_indexes else 0)
      generate_length = generate_length if generate_length > 0 else 0
      # required if the generated length must be the maximum possible
      #generate_length = reduce(lambda x, y: x * y, combination_speakers_segments_lengths)

      for index in range(generate_length):
        combination_segments_indexes = []
        for i, _ in enumerate(combination_speakers_segments_lengths):
          speaker_id = combination[i]
          if i != len(combination_speakers_segments_lengths) - 1:
            index, remainder = divmod(index, reduce(lambda x, y: x * y, combination_speakers_segments_lengths[i + 1:]))
          else:
            index = remainder
          combination_segments_indexes.append(single_speaker_segments_indexes[speaker_id][index])
        combination_speakers = [segments[index]['speakers'][0] for index in combination_segments_indexes] 
        min_combination_speakers_length = min([speaker['duration'] for speaker in combination_speakers])
        new_combination_speakers = [speaker.copy() for speaker in combination_speakers]
        for speaker in new_combination_speakers:
          speaker['duration'] = min_combination_speakers_length
          speaker['ending'] = round(speaker['begining'] + speaker['duration'], 2)
        new_segment = segments[combination_segments_indexes[0]].copy()
        new_segment['augmented'] = True
        new_segment['speakers'] = new_combination_speakers
        new_segment['begining'] = 0
        new_segment['duration'] = min_combination_speakers_length
        new_segment['ending'] = round(new_segment['begining'] + new_segment['duration'], 2)
        new_segment['filepath'] = scp[new_segment['recording_id']]
        combination_segments.append(new_segment)

    for index, segment in enumerate(combination_segments):
      filepath = segment['filepath']
      extension = '.' + filepath.split('.')[1]
      new_recording_id = recording_id + '_combination_' + str(index).zfill(3)
      new_filepath = args.output_folder + new_recording_id + extension
      sox_overlap(filepath, str(segment['speakers'][0]['begining']), str(segment['speakers'][0]['duration']),
                  filepath, str(segment['speakers'][1]['begining']), str(segment['speakers'][1]['duration']),
                  new_filepath)
      new_scp_line = scp_line.copy()
      new_scp_line[0] = new_recording_id
      new_scp_line[scp_filepath_index] = new_filepath
      file_wav_scp += ' '.join(new_scp_line)
      segment['original_recording_id'] = segment['recording_id']
      segment['recording_id'] = new_recording_id
      del segment['filepath']
      print(json.dumps(segment))

  f = open(args.output_folder + 'wav.scp', 'w')
  f.write(file_wav_scp)
  f.close()

if __name__ == '__main__':
  main()
