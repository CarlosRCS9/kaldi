#!/usr/bin/env python3
# Copyright 2020 Carlos Castillo
#
# Apache 2.0.

import argparse, os, sys

def get_args():
  parser = argparse.ArgumentParser(description = '')
  parser.add_argument('data_dir', type = str, help = '')
  args = parser.parse_args()
  return args

def main():
  args = get_args()
  if not os.path.isfile(args.data_dir + '/segments'):
    sys.exit(args.data_dir + '/segments not found')

  recordings_times = {}
  with open(args.data_dir + '/segments') as f:
    for line in f:
      utterance_id, recording_id, onset, end = line.rstrip().split()
      if recording_id not in recordings_times:
        recordings_times[recording_id] = []
      recordings_times[recording_id].append({ 'onset': onset, 'end': end })
      if 'str' in line:
        break

  for recording_id, values in recordings_times.items():
    f = open(args.data_dir + '/' + recording_id + '.sad', 'w')
    #print(recording_id)
    for value in values:
      f.write(value['onset'] + ' ' +  value['end'] + ' speech\n')
      #print(value['onset'], value['end'], 'speech')
    f.close()
    print(args.data_dir + '/' + recording_id + '.sad')

if __name__ == '__main__':
  main()


