#!/usr/bin/env python3
# Copyright 2021 Carlos Castillo
#
# Apache 2.0

from models import Rttm_line
import sys

def get_stdin ():
  return sys.stdin

def main ():
  stdin = get_stdin()
  for line in stdin:
    Rttm_line(line)

if __name__ == '__main__':
  main()
