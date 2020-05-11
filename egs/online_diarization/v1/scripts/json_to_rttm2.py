#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import argparse
import sys
import json

from models import Segment_complex

def get_recordings_speakers_ids(recordings_segments, maximum_speakers_length = 2):
    recordings_speakers_ids = {}
    for recording_id in recordings_segments:
        if recording_id not in recordings_speakers_ids:
            recordings_speakers_ids[recording_id] = []
        for segment in recordings_segments[recording_id]:
            for speaker in segment.speakers:
                if len(recordings_speakers_ids[recording_id]) < maximum_speakers_length and speaker.speaker_id not in recordings_speakers_ids[recording_id]:
                  recordings_speakers_ids[recording_id].append(speaker.speaker_id)
    return recordings_speakers_ids

def is_valid_speaker_segment(segment, recordings_speakers_ids, maximum_speakers_length = 2):
    speakers_ids = [speaker.speaker_id for speaker in segment.speakers]
    speakers_ids = list(set(speakers_ids))
    return len(speakers_ids) <= maximum_speakers_length and \
        all(speaker_id in recordings_speakers_ids[segment.recording_id] for speaker_id in speakers_ids)

def filter_recordings_segments(recordings_segments, segment_validation_function = lambda segment: True):
    filtered_recordings_segments = {}
    segments_original = 0
    segments_filtered = 0
    for recording_id in recordings_segments:
        segments_original += len(recordings_segments[recording_id])
        filtered_recordings_segments[recording_id] = list(filter(segment_validation_function, recordings_segments[recording_id]))
        segments_filtered += len(filtered_recordings_segments[recording_id])
    #print(round(segments_filtered / segments_original, 2), 'segments left.')
    return filtered_recordings_segments

# is_valid_segment [VALIDATED]
# validates if a segment meets a maximum number of speakers,
# and that all the speakers in the segment belong to a list.
def is_valid_segment(segment_complex, maximum_speakers_length = None, valid_speakers_ids = None):
    speakers_ids = [speaker.speaker_id for speaker in segment_complex.speakers]
    speakers_ids = list(set(speakers_ids))
    return (maximum_speakers_length is None or len(speakers_ids) <= maximum_speakers_length) and \
        (valid_speakers_ids is None or all(speaker_id in valid_speakers_ids for speaker_id in speakers_ids))

def get_args():
  parser = argparse.ArgumentParser(description='')
  parser.add_argument('--overlap-speaker', type=str, default='true', help='If true multiple-speakers segments get the "Z" speaker id in the output.')
  parser.add_argument('--maximum-speakers', type=str, default='None', help='The maximum number of speakers for each segment.')
  parser.add_argument('--valid-speakers', type=str, default='None', help='Comma separated valid speaker ids.')
  args = parser.parse_args()
  return args

def get_stdin():
  return sys.stdin

def main():
  args = get_args()
  args.overlap_speaker = args.overlap_speaker.lower() == 'true'
  args.maximum_speakers = None if args.maximum_speakers == 'None' else int(args.maximum_speakers)
  args.valid_speakers = None if args.valid_speakers == 'None' else args.valid_speakers.split(',')
  stdin = get_stdin()
  segments = [Segment_complex(json.loads(line)) for line in stdin]
  recordings_segments = {}
  for segment in segments:
    if segment.recording_id not in recordings_segments:
      recordings_segments[segment.recording_id] = []
    recordings_segments[segment.recording_id].append(segment)
  recordings_speakers_ids = get_recordings_speakers_ids(recordings_segments, args.maximum_speakers)
  recordings_segments_filtered = filter_recordings_segments(recordings_segments, lambda segment: is_valid_speaker_segment(segment, recordings_speakers_ids, args.maximum_speakers))
  for recording_id in recordings_segments_filtered:
    for segment in recordings_segments_filtered[recording_id]:
      print(segment.get_rttm(args.overlap_speaker))

if __name__ == '__main__':
  main()
