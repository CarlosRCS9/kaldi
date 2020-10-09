#!/usr/bin/env python3
# Copyright 2020 Carlos Castillo
#
# Apache 2.0.

import argparse, os, sys, itertools
from models import Segment, sort_segments_by_file_id, get_segments_explicit_overlap

def get_args():
  parser = argparse.ArgumentParser(description = '')
  parser.add_argument('rttm', type = str, help = '')
  parser.add_argument('segments', type = str, help = '')
  parser.add_argument('speaker', type = str, help = '')
  args = parser.parse_args()
  return args

def main():
  args = get_args()
  if not os.path.isfile(args.rttm):
    sys.exit(args.rttm + ' not found')
  if not os.path.isfile(args.segments):
    sys.exit(args.segments + ' not found')

  segments = []
  with open(args.rttm) as f:
    for line in f:
      try:
        segments.append(Segment(line))
      except:
        pass
      if 'str' in line:
        break
  recordings_segments = sort_segments_by_file_id(segments)

  recordings_utterances = {}
  with open(args.segments) as f:
    for line in f:
      try:
        utterance_id, recording_id, onset, end = line.rstrip().split()
        onset = float(onset)
        end = float(end)
        if recording_id not in recordings_utterances:
          recordings_utterances[recording_id] = []
        recordings_utterances[recording_id].append({ 'utterance_id': utterance_id, 'onset': onset, 'end': end })
      except:
        pass
      if 'str' in line:
        break

  speaker_name = {}
  speaker_count = 0
  f_segments = open(args.segments + '_tmp', 'w')
  f_utt2spk = open(os.path.dirname(args.segments) + '/utt2spk_tmp', 'w')
  for recording_id in sorted(recordings_utterances.keys()):
    try:
      utterances = recordings_utterances[recording_id]
      segments = get_segments_explicit_overlap(recordings_segments[recording_id])
      for utterance in utterances:
        utterance_segments = []
        for segment in segments:
          if segment.get_turn_end() > utterance['onset'] and segment.get_turn_onset() < utterance['end']:
            utterance_segments.append(segment)
        if len(utterance_segments) > 0:
          speakers = sorted(set(itertools.chain(*[[speaker.get_name() for speaker in segment.get_speakers()] for segment in utterance_segments])))
          speakers_string = '-'.join(speakers)
          if speakers_string not in speaker_name:
            speaker_name[speakers_string] = args.speaker + str(speaker_count).zfill(3)
            speaker_count += 1
          segment_string = utterance['utterance_id'] + ' ' + recording_id + ' ' + str(utterance['onset']) + ' ' + str(utterance['end'])
          utt2spk_string = utterance['utterance_id'] + ' ' + speaker_name[speakers_string]
          f_segments.write(segment_string + '\n')
          f_utt2spk.write(utt2spk_string + '\n')
    except:
      pass
  f_segments.close()
  f_utt2spk.close()

if __name__ == '__main__':
  main()


