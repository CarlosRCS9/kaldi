#!/usr/bin/env python3
# Copyright 2021 Carlos Castillo
#
# Apache 2.0

from models import Rttm
import sys

def get_stdin ():
  return sys.stdin

def main ():
  stdin = get_stdin()
  rttm = Rttm(stdin)
  print(rttm)

if __name__ == '__main__':
  main()
