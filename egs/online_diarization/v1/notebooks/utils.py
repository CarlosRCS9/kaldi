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

a = [0.5161056, 3.323303, -0.2218932, 2.212632, -0.08488278, 0.6095699, 2.061484, 0.1267809, -0.9775604, -0.07349944, 0.8676496, -0.3474629, 1.465098, -0.4181523, 0.9402734, 0.6951039, 0.6974553, -0.2189828, -0.8506244, 1.729026, 0.9744338, 0.9362175, -1.284223, -0.6214003, -0.272966, 0.3092976, -1.115854, -1.336964, -1.045321, 1.784676, 0.9903587, 0.07030118, -0.258367, 0.2569296, 0.3188978, -0.7762743, -0.500159, 1.635644, -1.220187, -0.1978389, -0.4204791, -0.175537, -1.303136, 0.6002243, 0.2082113, -0.1124284, 0.8512208, 0.0153528, -1.704879, -0.8558358, -1.722548, 0.9728361, -0.1880095, 1.027094, -0.3918952, 0.6964331, 1.038561, 0.8142215, 0.7089959, -1.487634, 0.6505318, -0.2076035, 1.740835, 1.183031, 0.8037471, -1.899768, -0.3401686, 0.5246427, -0.1594032, 0.03277509, 0.4094424, 0.9478282, 0.006036461, -0.9612474, -0.07677123, 1.181654, 0.4278452, -1.060346, -0.261407, 0.7542065, -0.3763399, -0.4760149, -0.2255033, -0.1612778, -0.1219221, 0.9430006, -0.2294448, 0.635745, 1.308211, 0.5203381, 0.2668837, -0.8161051, 0.473591, 1.063837, 0.4308696, 0.6808659, -0.1619593, 1.781231, -0.4810635, 0.5916328, -0.2916703, 0.1475444, -1.172362, 0.85771, -0.4996614, 1.304002, 1.314985, 0.3038374, -1.016452, 0.05339971, -0.6296211, -0.1020167, -0.6223015, 0.1429098, -0.6164569, 0.06095246, 1.359548, 0.4101916, -0.5070114, 0.6212752, 0.5918257, 1.343816, 0.7736513, -0.4464976, 1.217789, -0.9706424, 0.6411951, 0.01939208]
b = [0.5161056, 3.323303, -0.2218932, 2.212632, -0.08488278, 0.6095699, 2.061484, 0.1267809, -0.9775604, -0.07349944, 0.8676496, -0.3474629, 1.465098, -0.4181523, 0.9402734, 0.6951039, 0.6974553, -0.2189828, -0.8506244, 1.729026, 0.9744338, 0.9362175, -1.284223, -0.6214003, -0.272966, 0.3092976, -1.115854, -1.336964, -1.045321, 1.784676, 0.9903587, 0.07030118, -0.258367, 0.2569296, 0.3188978, -0.7762743, -0.500159, 1.635644, -1.220187, -0.1978389, -0.4204791, -0.175537, -1.303136, 0.6002243, 0.2082113, -0.1124284, 0.8512208, 0.0153528, -1.704879, -0.8558358, -1.722548, 0.9728361, -0.1880095, 1.027094, -0.3918952, 0.6964331, 1.038561, 0.8142215, 0.7089959, -1.487634, 0.6505318, -0.2076035, 1.740835, 1.183031, 0.8037471, -1.899768, -0.3401686, 0.5246427, -0.1594032, 0.03277509, 0.4094424, 0.9478282, 0.006036461, -0.9612474, -0.07677123, 1.181654, 0.4278452, -1.060346, -0.261407, 0.7542065, -0.3763399, -0.4760149, -0.2255033, -0.1612778, -0.1219221, 0.9430006, -0.2294448, 0.635745, 1.308211, 0.5203381, 0.2668837, -0.8161051, 0.473591, 1.063837, 0.4308696, 0.6808659, -0.1619593, 1.781231, -0.4810635, 0.5916328, -0.2916703, 0.1475444, -1.172362, 0.85771, -0.4996614, 1.304002, 1.314985, 0.3038374, -1.016452, 0.05339971, -0.6296211, -0.1020167, -0.6223015, 0.1429098, -0.6164569, 0.06095246, 1.359548, 0.4101916, -0.5070114, 0.6212752, 0.5918257, 1.343816, 0.7736513, -0.4464976, 1.217789, -0.9706424, 0.6411951, 0.01939208]

print(ivector_plda_scoring(a, b, '../exp/plda/callhome2/ivectors.plda'))
