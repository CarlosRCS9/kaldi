#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import os
import kaldi_utils
import numpy as np
from functools import reduce
import matplotlib.pyplot as plt
from itertools import cycle

def compute_min_dcf(directory, target_probability = 0.01):
  scores_filepath = directory + '/dcf.scores'
  trials_filepath = directory + '/dcf.trials'
  return kaldi_utils.compute_min_dcf(scores_filepath, trials_filepath, target_probability)

def mean_compute_min_dcf(directories, target_probability = 0.01):
  return reduce(lambda acc, directory: acc + compute_min_dcf(directory, target_probability), directories, 0) / len(directories)

base_directory = 'TODO'
directories = os.listdir(base_directory)
experiments = list(set(['_'.join(directory.split('_')[:-1]) for directory in directories]))
experiments = [(experiment, experiment.split('_')[-3], experiment.split('_')[-2]) for experiment in experiments]
experiments.sort(key = lambda experiment: experiment[1] + experiment[2].zfill(2))
labels = []
lines = ['-','--','-.',':']
linecycler = cycle(lines)
for experiment in experiments:
  if experiment[2] != '15':
    experiment_directories = list(filter(lambda directory: experiment[0] in directory, directories))
    experiment_directories = [base_directory + '/' + directory for directory in experiment_directories]

    x = np.linspace(0.01, 0.5, 50)
    y = np.vectorize(lambda x: mean_compute_min_dcf(experiment_directories, x))(x)

    plt.plot(x * 100, y, next(linecycler))
    labels.append(('i-vector' if experiment[1] == 'ivectors' else 'x-vector') + ' ' + str(int(experiment[2]) * 0.5 + 0.5)  + ' s')

plt.xlabel('Target probability (%)')
plt.ylabel('minDCF')
plt.legend(labels)
plt.grid()
plt.show()
