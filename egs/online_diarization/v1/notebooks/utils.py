#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import subprocess

def eer_score(res_filepath, log_directory = None):
  bin = '../eer_score.sh'
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
