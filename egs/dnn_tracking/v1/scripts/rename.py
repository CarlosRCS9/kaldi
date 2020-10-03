#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import argparse, sys

def get_args():
  parser = argparse.ArgumentParser(description = '')
  parser.add_argument('file_name', type = str, help = '')
  args = parser.parse_args()
  return args

def get_stdin():
  return sys.stdin

def main():
  args = get_args()
  stdin = get_stdin()
  f = open(args.file_name, 'r+b')
  file_map = {}
  for line in f.readlines():
    file, name = line.decode('utf-8').rstrip().split()
    file_map[file] = name
  f.close()
  for line in stdin:
    for file in sorted(file_map.keys(), key = len, reverse = True):
      line = line.replace(file, file_map[file])
    print(line, end = '')

if __name__ == '__main__':
  main()

