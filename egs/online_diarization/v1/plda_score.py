#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import argparse
import os
import subprocess
import re

def get_args():
  parser = argparse.ArgumentParser(description='This script gets the plda score of two i-vectors.')
  parser.add_argument('ref_filepath', type=str, help='The reference i-vector.')
  parser.add_argument('test_filepath', type=str, help='The test i-vector.')
  parser.add_argument('trials_filepath', type=str, help='The trials filepath.')
  args = parser.parse_args()
  return args

def main():
  args = get_args()
  ref_filepath = args.ref_filepath
  test_filepath = args.test_filepath
  trials_filepath = args.trials_filepath

  bin = './plda_score.sh'
  p = subprocess.Popen([bin, ref_filepath, test_filepath, trials_filepath], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  output, err = p.communicate()
  rc = p.returncode
  if rc == 0:
    lines =  output.decode("utf-8").split('\n')
    pldaLine = [line for line in lines if 'reference test' in line][0]
    print(re.findall('\d+\.\d+', pldaLine)[0])
  else:
    print(err)
    exit('plda_socre.sh fail')

if __name__ == '__main__':
  main()
