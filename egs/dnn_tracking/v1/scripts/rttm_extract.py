#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import argparse
import sys

from models import Segment

def get_args():
  parser = argparse.ArgumentParser(description='')
  args = parser.parse_args()
  return args

def get_stdin():
  return sys.stdin

def main():
  args = get_args()
  stdin = get_stdin()

  segments = [Segment(line) for line in stdin]
  for segment in segments:
    segment.print_rttm()

if __name__ == '__main__':
  main()
