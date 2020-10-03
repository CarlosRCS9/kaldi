#!/usr/bin/env python3
# Copyright 2020 Carlos Castillo
# Apache 2.0

import argparse, os

def get_args():
  parser = argparse.ArgumentParser(description = '')
  parser.add_argument('input_dir', type = str, help = 'Input data directory')
  parser.add_argument('output_dir', type = str, help = 'Output data directory')
  args = parser.parse_args()
  args = check_args(args)
  return args

def check_args(args):
  if not os.path.isdir(args.input_dir):
    raise Exception('input_dir must be a folder')
  if not os.path.isdir(args.output_dir):
    raise Exception('output_dir must be a folder')
  return args

def check_input_dir(input_dir):
  if not os.path.isfile(input_dir + '/segments'):
    raise Exception('segments file does not exist')
  if not os.path.isfile(input_dir + '/wav.scp'):
    raise Exception('wav.scp file does not exist')

def parse_wav_scp(filepath):
  wav_scp = {}
  f = open(filepath, 'r')
  for line in f.readlines():
    recording_id, extended_filename = line.split(' ', 1)
    extended_filename = extended_filename.rstrip()
    wav_scp[recording_id] = { 'extended_filename': extended_filename }
  f.close()
  return wav_scp

def parse_segments(filepath):
  segments = {}
  f = open(filepath, 'r')
  for line in f.readlines():
    utterance_id, recording_id, segment_begin, segment_end = line.rstrip().split()
    segments[utterance_id] = { 'recording_id': recording_id, 'segment_begin': segment_begin, 'segment_end': segment_end }
  f.close()
  return segments

def segments_to_wav_scp(segments, wav_scp, output_dir):
  wav_scp_new = {}
  for utterance_id, value in segments.items():
    recording_id = value['recording_id']
    segment_begin = float(value['segment_begin'])
    segment_end = float(value['segment_end'])
    extended_filename = wav_scp[recording_id]['extended_filename']
    segment_duration = segment_end - segment_begin

    if not os.path.isdir(output_dir + '/tmp'):
      os.makedirs(output_dir + '/tmp')
    tmp_filepath = os.path.abspath(output_dir + '/tmp/' + utterance_id + '.wav')
    if os.path.isfile(tmp_filepath):
      wav_scp_new[utterance_id] = { 'extended_filename': tmp_filepath }
    elif extended_filename[:6] == 'ffmpeg' and extended_filename[-4:] == ' - |':
      extended_filename_new = extended_filename[:6] + ' -ss ' + str(round(segment_begin, 3)) + ' -t ' + str(round(segment_duration, 3)) + extended_filename[6:]
      extended_filename_new = extended_filename_new[:-4] + ' ' + tmp_filepath + '; cat ' + tmp_filepath + ' |'
      wav_scp_new[utterance_id] = { 'extended_filename': extended_filename_new }
  return wav_scp_new

def segments_to_utterance_segments(segments):
  segments_new = {}
  for utterance_id, value in segments.items():
    recording_id = utterance_id
    segment_begin = value['segment_begin']
    segment_end = value['segment_end']
    segment_duration = str(round(float(segment_end) - float(segment_begin), 3))
    segments_new[utterance_id] = { 'recording_id': recording_id, 'segment_begin': '0', 'segment_end': segment_duration }
  return segments_new

def write_segments(segments, output_dir):
  f = open(output_dir + '/segments_tmp', 'w')
  for utterance_id in sorted(segments.keys()):
    value = segments[utterance_id]
    recording_id = value['recording_id']
    segment_begin = value['segment_begin']
    segment_end = value['segment_end']
    f.write(utterance_id + ' ' + recording_id + ' ' + segment_begin + ' ' + segment_end + '\n')
  f.close()

def write_wav_scp(wav_scp, output_dir):
  f = open(output_dir + '/wav_tmp.scp', 'w')
  for recording_id in sorted(wav_scp.keys()):
    value = wav_scp[recording_id]
    extended_filename = value['extended_filename']
    f.write(recording_id + ' ' + extended_filename + '\n')
  f.close()

def main():
  args = get_args()
  check_input_dir(args.input_dir)
  segments = parse_segments(args.input_dir + '/segments')
  wav_scp = parse_wav_scp(args.input_dir + '/wav.scp')
  segments_new = segments_to_utterance_segments(segments)
  #wav_scp_new = segments_to_wav_scp(segments, wav_scp, '/export/b03/carlosc/')
  wav_scp_new = segments_to_wav_scp(segments, wav_scp, args.output_dir)
  write_segments(segments_new, args.output_dir)
  write_wav_scp(wav_scp_new, args.output_dir)

if __name__ == '__main__':
  main()

