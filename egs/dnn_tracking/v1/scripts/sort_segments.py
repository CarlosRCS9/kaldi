#!/usr/bin/env python3
#
# Copyright 2020 Carlos Castillo
# Apache 2.0.

import argparse

def get_args():
  parser = argparse.ArgumentParser(description='')
  parser.add_argument('segments', type = str, help = 'Input segments file')
  parser.add_argument('--labels', type = str, default = None, help = 'Input labels file')
  args = parser.parse_args()
  return args

def main():
  args = get_args()
  f = open(args.segments, 'r')
  lines = [line for line in f.readlines()]
  f.close()
  recordings_utterances = {}
  for line in lines:
    utterance_id, recording_id, segment_begin, segment_end = line.rstrip().split()
    segment_begin = float(segment_begin)
    segment_end = float(segment_end)
    if recording_id not in recordings_utterances:
      recordings_utterances[recording_id] = []
    recordings_utterances[recording_id].append({ 'utterance_id': utterance_id, 'segment_begin': segment_begin, 'segment_end': segment_end })
  if args.labels is not None:
    f = open(args.labels, 'r')
    lines = [line for line in f.readlines()]
    f.close()
    utterances_labels = {}
    for line in lines:
      utterance_id, speaker_id = line.rstrip().split()
      utterances_labels[utterance_id] = { 'speaker_id': speaker_id }

  segments_tmp = open(args.segments + '_tmp', 'w')
  if args.labels is not None:
    labels_tmp = open(args.labels + '_tmp', 'w')
  for recording_id in sorted(recordings_utterances.keys()):
    recordings_utterances[recording_id].sort(key = lambda segment: segment['segment_begin'])
    for segment in recordings_utterances[recording_id]:
      segments_tmp.write(' '.join([segment['utterance_id'], recording_id, str(segment['segment_begin']), str(segment['segment_end']), '\n']))
      if args.labels is not None:
        labels_tmp.write(' '.join([segment['utterance_id'], utterances_labels[segment['utterance_id']]['speaker_id'], '\n']))
  segments_tmp.close()
  if args.labels is not None:
    labels_tmp.close()

if __name__ == '__main__':
  main()
