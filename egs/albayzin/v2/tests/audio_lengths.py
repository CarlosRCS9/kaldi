#!/usr/bin/env python3
# Copyright 2020 Carlos Castillo
#
# Apache 2.0.

import argparse, os, sys
import numpy as np

def get_args():
  parser = argparse.ArgumentParser(description = '')
  parser.add_argument('file', type = str, help = '')
  args = parser.parse_args()
  return args

def main():
  args = get_args()
  if not os.path.isfile(args.file):
    sys.exit(args.file + ' not found')

  files_durations = {}
  with open(args.file) as f:
    for line in f:
      if '/' in line:
        filepath = line.rstrip()
        files_durations[filepath] = []
      else:
         files_durations[filepath].append(float(line.rstrip()))
      if 'str' in line:
        break
  for filepath, durations in files_durations.items():
    print(filepath)
    sum = np.sum(durations)
    std = np.std(durations)
    mean = np.mean(durations)

    print('total(s): ' + str(sum) + ' mean(s): ' + str(mean) + ' std(s): ' + str(std))
    print('total(h): ' + str(sum / 3600) + ' mean(h): ' + str(mean / 3600) + ' std(h): ' + str(std / 3600))

if __name__ == '__main__':
  main()

