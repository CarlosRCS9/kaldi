#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import argparse
import sys

from models import read_wav_scp

def get_args():
  parser = argparse.ArgumentParser(description='')
  parser.add_argument('wav_scp', type=str, help='')
  parser.add_argument('output_folder', type=str, help='')
  args = parser.parse_args()
  return args

def get_stdin():
  return sys.stdin

def main():
  args = get_args()
  stdin = get_stdin()

  wav_scp = read_wav_scp(args.wav_scp)
  for file_id in wav_scp:
    print(wav_scp[file_id])

if __name__ == '__main__':
  main()
