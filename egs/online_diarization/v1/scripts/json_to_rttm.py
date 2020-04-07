#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import argparse
import sys

from models import Segment_complex

def get_args():
  parser = argparse.ArgumentParser(description='')
  parser.add_argument('--overlap-speaker', type=str, default='true', help='If true multiple-speakers segments get the "Z" speaker id in the output.')
  args = parser.parse_args()
  return args

def get_stdin():
  return sys.stdin

def main():
  args = get_args()
  args.overlap_speaker = args.overlap_speaker.lower() == 'true'
  stdin = get_stdin()
  segments = [Segment_complex(json.loads(line)) for line in stdin]
  for segment in segments:
    print(segment.get_rttm(args.overlap_speaker))

if __name__ == '__main__':
  main()
