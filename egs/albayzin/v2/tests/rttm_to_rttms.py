#!/usr/bin/env python3
# Copyright 2020 Carlos Castillo
#
# Apache 2.0.

import argparse, os, sys

def get_args():
  parser = argparse.ArgumentParser(description = '')
  parser.add_argument('rttm', type = str, help = '')
  args = parser.parse_args()
  return args

def main():
  args = get_args()
  if not os.path.isfile(args.rttm):
    sys.exit(args.rttm + ' not found')

  recording_rttm = {}
  with open(args.rttm) as f:
    for line in f:
      recording_id = line.partition(' ')[2].partition(' ')[0]
      if recording_id not in recording_rttm:
        recording_rttm[recording_id] = []
      recording_rttm[recording_id].append(line)
      if 'str' in line:
        break

  filename, file_extension = os.path.splitext(args.rttm)
  os.makedirs(filename, exist_ok = True)
  for recording_id, rttm in recording_rttm.items():
    f = open(filename + '/' + recording_id + file_extension, 'w')
    for line in rttm:
      f.write(line)
    f.close()

if __name__ == '__main__':
  main()


