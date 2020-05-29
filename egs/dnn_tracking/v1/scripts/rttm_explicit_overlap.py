#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import sys

from models import Segment

def get_stdin():
  return sys.stdin

def main():
  print('test')
  stdin = get_stdin()
  for line in stdin:
    print(Segment(line))

if __name__ == '__main__':
  main()
