#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import os
import subprocess
import numpy

def cut_and_stitch(scp, timestamps_pairs, output_filepath):
  if not os.path.exists(output_filepath):
    trims = ['|sox ' + scp.get_filepath() + ' -t ' + scp.get_format() + ' - trim ' + str(onset) + ' ' + str(duration) for onset, duration in timestamps_pairs]
    command = ['sox'] + trims + [output_filepath]
    p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = p.communicate()
    rc = p.returncode
    if rc != 0:
      print(err)
      exit(1)
  command = ['soxi', '-D', output_filepath]
  p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  output, err = p.communicate()
  rc = p.returncode
  if rc != 0:
    print(err)
    exit(1)
  else:
    duration = numpy.float32(output.decode("utf-8"))
    return (output_filepath, duration)

def mix_files(input_filepaths, min_duration, output_filepath):
  if not os.path.exists(output_filepath):
    trims = ['|sox ' + filepath + ' -t ' + filepath.split('.')[-1] + ' - trim 0 ' + str(min_duration) for filepath in input_filepaths]
    command = ['sox', '-m'] + trims + [output_filepath]
    p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = p.communicate()
    rc = p.returncode
    if rc != 0:
      print(err)
      exit(1)
  command = ['soxi', '-D', output_filepath]
  p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  output, err = p.communicate()
  rc = p.returncode
  if rc != 0:
    print(err)
    exit(1)
  else:
    duration = numpy.float32(output.decode("utf-8"))
    return (output_filepath, duration)

def stitch_trims(trims, output_filepath):
  if not os.path.exists(output_filepath):
    command = ['sox'] + trims + [output_filepath]
    p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = p.communicate()
    rc = p.returncode
    if rc != 0:
      print(err)
      exit(1)
  command = ['soxi', '-D', output_filepath]
  p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  output, err = p.communicate()
  rc = p.returncode
  if rc != 0:
    print(err)
    exit(1)
  else:
    duration = numpy.float32(output.decode("utf-8"))
    return (output_filepath, duration)
