#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

from functools import reduce
import argparse
import re
import subprocess
import sys
import json
import itertools

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
  trims = ['|sox ' + input_filepath + ' -t sph - trim ' + str(timestamp[0]) + ' ' + str(timestamp[1]) + '' for timestamp in timestamps]
  command = ['sox'] + trims + [output_filepath]
  '''p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  output, err = p.communicate()
  rc = p.returncode
  if rc == 0:
    command = ['soxi', '-D', output_filepath]
    p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = p.communicate()
    rc = p.returncode
    if rc == 0:
      length = float(output.decode("utf-8"))
      return (output_filepath, length)
    else:
      print(err)
      exit(1)
  else:
    print(err)
    exit(1)'''
  command = ['soxi', '-D', output_filepath]
  p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  output, err = p.communicate()
  rc = p.returncode
  if rc == 0:
    length = float(output.decode("utf-8"))
    return (output_filepath, length)
  else:
    print(err)
    exit(1)

def main():
  args = get_args()
  stdin = get_stdin()
  scp = read_scp(args.scp)
  segments = [Segment_complex(json.loads(line)) for line in stdin]
  recordings_segments = reduce(get_recordings_segments, segments, {})
  for recording_id in sorted(list(recordings_segments.keys())):
    print(recording_id)
    recording_segments = recordings_segments[recording_id]
    speakers_segments = reduce(lambda acc, segment: get_speakers_segments(acc, segment, ['A', 'B']), recording_segments, {})
    speakers_stiched = {}
    for speaker_id in speakers_segments:
      speaker_segments = speakers_segments[speaker_id]
      timestamps = sorted([(round(segment.begining, 2), round(segment.duration, 2)) for segment in speaker_segments], key = lambda tuple: tuple[0])
      filepath = args.output_folder + recording_id + '_' + speaker_id + '.' + scp[recording_id].split('.')[1]
      filepath, duration = sox_stich_audio(scp[recording_id], timestamps, filepath)
      speakers_stiched[speaker_id] = { 'filepath': filepath, 'duration': duration }
    for combination in [sorted(combination) for combination in list(itertools.combinations([speaker_id for speaker_id in speakers_stiched], 2))]:
      durations = [speakers_stiched[speaker_id]['duration'] for speaker_id in combination]
      min_duration = min(durations)
      print(min_duration)

if __name__ == '__main__':
  main()
