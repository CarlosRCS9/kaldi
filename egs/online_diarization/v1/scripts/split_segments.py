#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import argparse
import sys
import json

class Speaker:
  def __init__(self, segment_complex, speaker):
    self.speaker_id = speaker['speaker_id']
    self.begining = speaker['begining'] if speaker['begining'] > segment_complex.begining else segment_complex.begining
    self.ending = speaker['ending'] if speaker['ending'] < segment_complex.ending else segment_complex.ending
    self.duration = self.ending - self.begining
  def json(self):
    self_json = self.__dict__
    self_json['begining'] = round(self_json['begining'], 2)
    self_json['ending'] = round(self_json['ending'], 2)
    self_json['duration'] = round(self_json['duration'], 2)
    return self_json

class Segment_complex:
  def __init__(self, begining, ending, segment):
    self.type = segment['type']
    self.recording_id = segment['recording_id']
    self.channel = segment['channel']
    self.begining = begining
    self.ending = ending
    self.duration = self.ending - self.begining
    self.ortho = segment['ortho']
    self.stype = segment['stype']
    self.speakers = [Speaker(self, speaker) for speaker in segment['speakers']]
    self.conf = segment['conf']
    self.slat = segment['slat']
  def __str__(self):
    return str(self.__class__) + ": " + str(self.__dict__)
  def json(self):
    self_json = self.__dict__
    self_json['begining'] = round(self_json['begining'], 2)
    self_json['ending'] = round(self_json['ending'], 2)
    self_json['duration'] = round(self_json['duration'], 2)
    self_json['speakers'] = [speaker.json() for speaker in self.speakers]
    return self_json

def get_args():
  parser = argparse.ArgumentParser(description='This script splits the segments of a given file to a given length and overlap.')
  parser.add_argument('input_mode', type=str, help='json or rttm.')
  parser.add_argument('--length', type=float, default=0.0, help='segment max length')
  parser.add_argument('--overlap', type=float, default=0.0, help='segment overlap')
  parser.add_argument('--min-segment', type=float, default=0.0, help='minimal length of a generated segment')
  args = parser.parse_args()
  return args

def get_stdin():
  return sys.stdin

def main():
  args = get_args()
  stdin = get_stdin()
  if args.input_mode == 'json':
    for line in stdin:
      if args.length <= 0.0:
        print(line, end = '')
      else:
        segment = json.loads(line)
        begining = segment['begining']
        while begining < segment['ending']:
          ending = begining + args.length
          new_segment = Segment_complex(begining, segment['ending'] if ending > segment['ending'] else ending, segment)
          if new_segment.duration >= args.min_segment:
            print(json.dumps(new_segment.json()))
          begining = ending - args.overlap
  else:
    exit('Not implemented mode.')

if __name__ == '__main__':
  main()

