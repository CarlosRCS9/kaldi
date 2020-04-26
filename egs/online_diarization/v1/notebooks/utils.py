#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import subprocess
import re

def compute_min_dcf(scores_filepath, trials_filepath, target_probability = 0.01, log_directory = None):
  bin = '../sid/compute_min_dcf.py'
  command = [bin, '--p-target', str(target_probability), scores_filepath, trials_filepath]
  p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  output, err = p.communicate()
  rc = p.returncode
  if rc == 0:
    output = output.decode("utf-8")
    if log_directory is not None:
      file = open(log_directory + '/dcf.log', 'w')
      file.write(output)
      file.close()
    return float(output)
  else:
    exit(err)

def compute_eer(res_filepath, log_directory = None):
  bin = '../../../../src/ivectorbin/compute-eer'
  command = [bin, res_filepath]
  p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  output, err = p.communicate()
  rc = p.returncode
  if rc == 0:
    output = output.decode("utf-8")
    if log_directory is not None:
      file = open(log_directory + '/eer.log', 'w')
      file.write(output)
      file.close()
    return float(output)
  else:
    exit(err)

def md_eval(ref_filepath, res_filepath, log_directory = None):
  bin = '../../../../tools/sctk-2.4.10/src/md-eval/md-eval.pl'
  command = [bin, '-r', ref_filepath, '-s', res_filepath]
  p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  output, err = p.communicate()
  rc = p.returncode
  if rc == 0:
    output = output.decode("utf-8")
    if log_directory is not None:
      file = open(log_directory + '/der.log', 'w')
      file.write(output)
      file.close()
    lines =  output.split('\n')
    derLine = [line for line in lines if 'OVERALL SPEAKER DIARIZATION ERROR' in line][0]
    return float(re.findall('\d+\.\d+', derLine)[0])
  else:
    exit(err)

def ivector_plda_scoring(ref_vector, test_vector, plda_filepath):
  ref_string = str(list(ref_vector)).replace(',', '').replace('[', '[ ').replace(']', ' ]')
  test_string = str(list(test_vector)).replace(',', '').replace('[', '[ ').replace(']', ' ]')
  bin = '../../../../src/ivectorbin/ivector-plda-scoring'
  command = [bin, plda_filepath, 'ark:echo reference ' + ref_string + '|', 'ark:echo test ' + test_string + '|', 'echo reference test|', '|cat']
  p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  output, err = p.communicate()
  rc = p.returncode
  if rc == 0:
    lines =  output.decode("utf-8").split('\n')
    pldaLine = [line for line in lines if 'reference test' in line][0]
    return float(re.findall('\d+\.\d+', pldaLine)[0])
  else:
    exit(err)
