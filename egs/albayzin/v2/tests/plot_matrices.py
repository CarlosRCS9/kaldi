#!/usr/bin/env python3
# Copyright 2020 Carlos Castillo
#
# Apache 2.0.

import argparse, os, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import random

def get_args():
  parser = argparse.ArgumentParser(description = '')
  parser.add_argument('matrix_a_filepath', type = str, help = '')
  parser.add_argument('matrix_b_filepath', type = str, help = '')
  args = parser.parse_args()
  return args

def is_number(input):
  try:
    float(input)
    return True
  except ValueError:
    return False

def main():
  args = get_args()
  if not os.path.isfile(args.matrix_a_filepath):
    sys.exit(args.matrix_a_filepath + ' not found')
  if not os.path.isfile(args.matrix_b_filepath):
    sys.exit(args.matrix_b_filepath + ' not found')

  a_files_data = {}
  b_files_data = {}
  for files_data, matrix_filepath in [(a_files_data, args.matrix_a_filepath), (b_files_data, args.matrix_b_filepath)]:
    print(matrix_filepath)
    with open(matrix_filepath) as f:
      first_flag = False
      last_flag = False
      for line in f:
        before, _, after = line.partition(' ')
        if (not is_number(before) or '[' in line) and before:
          first_flag = True
          file_id = before
        elif first_flag:
          first_flag = False
          files_data[file_id] = {}
          files_data[file_id]['vector'] = np.asarray([float(word) for word in line.split()])
          vector_size = files_data[file_id]['vector'].size
          files_data[file_id]['matrix'] = np.zeros([vector_size, vector_size])
          row = 0
          files_data[file_id]['matrix'][row] = files_data[file_id]['vector']
        else:
          row += 1
          if row == vector_size - 1:
            last_flag = True
            line = line.partition(']')[0]
          files_data[file_id]['matrix'][row][row:] = np.asarray([float(word) for word in line.split()[row:]])
          if last_flag:
            last_flag = False
            #print(files_data[file_id]['matrix'].shape)
            #print(files_data[file_id]['matrix'])
            #break #TODO delete this
            print(file_id, files_data[file_id]['matrix'].shape)
        if 'str' in line:
          break

  for files_data, files_samples, color in [(a_files_data, [], 'r'), (b_files_data, [], 'b')]:
    for file_id, values in files_data.items():
      vector_size = values['vector'].size
      samples = int(vector_size / 10)
      row_indexes = random.sample(range(vector_size), samples)
      column_indexes = [random.choice(range(row_index, vector_size)) for row_index in row_indexes]
      matrix_samples = [values['matrix'][row][column] for row, column in zip(row_indexes, column_indexes)]
      files_samples += matrix_samples
    plt.hist(files_samples, bins = 1000, color = color, alpha = 0.5)
  plt.savefig('matrices.png')

if __name__ == '__main__':
  main()

