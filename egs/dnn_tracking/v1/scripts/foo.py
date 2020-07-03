#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import argparse

from models import get_rttm_segments_features

def get_args():
  parser = argparse.ArgumentParser(description='')
  parser.add_argument('rttm', type=str, help='')
  parser.add_argument('segments', type=str, help='')
  parser.add_argument('ivectors', type=str, help='')
  args = parser.parse_args()
  return args

def main():
  args = get_args()

  files_segments = get_rttm_segments_features(args.rttm, args.segments, args.ivectors)

if __name__ == '__main__':
  main()
