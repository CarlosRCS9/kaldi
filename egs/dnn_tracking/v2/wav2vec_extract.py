#!/usr/bin/env python
# Copyright 2020 Carlos Castillo
# Apache 2.0.

import argparse, os, sys
from scipy.io import wavfile
import numpy as np

import torch
from fairseq.models.wav2vec import Wav2VecModel

def get_args():
  parser = argparse.ArgumentParser(description = '')
  parser.add_argument('data_dir', type = str, help = '')
  args = parser.parse_args()
  return args

def main():
  args = get_args()
  if not os.path.isdir(args.data_dir):
    sys.exit(args.data_dir + ' must be a directory.')
  if not os.path.isfile(args.data_dir + '/wav.scp'):
    sys.exit(args.data_dir + '/wav.scp not found.')

  wav = {}
  f = open(args.data_dir + '/wav.scp', 'r')
  for line in f.readlines():
    try:
      recording_id, filepath = line.rstrip().split()
      wav[recording_id] = filepath
    except:
      pass
  f.close()

  cp = torch.load('wav2vec_large.pt')
  model = Wav2VecModel.build_model(cp['args'], task=None)
  model.load_state_dict(cp['model'])
  model.eval()

  for recording_id, filepath in wav.items():
    rate, data = wavfile.read(filepath)
    tensor = torch.tensor(np.copy(data))

    z = model.feature_extractor(tensor.unsqueeze(0))
    c = model.feature_aggregator(z)
    print(c)
    break
    
if __name__ == '__main__':
  main()



#wav_input_16khz = torch.randn(1,10000)
#z = model.feature_extractor(wav_input_16khz)
#c = model.feature_aggregator(z)
#print(c)

