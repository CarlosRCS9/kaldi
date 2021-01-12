#!/usr/bin/env python
# Copyright 2020 Carlos Castillo
# Apache 2.0.

import argparse, os, sys
from scipy.io import wavfile
import numpy as np
sys.path.insert(0, 'python')
from cut import Rttm, Cut, cuts_to_recordings
import itertools
import kaldi_io

import torch
from fairseq.models.wav2vec import Wav2VecModel

def get_args():
  parser = argparse.ArgumentParser(description = '')
  parser.add_argument('data_dir', type = str, help = '')
  parser.add_argument('output_dir', type = str, help = '')
  args = parser.parse_args()
  return args

def main():
  args = get_args()
  if not os.path.isdir(args.data_dir):
    sys.exit(args.data_dir + ' must be a directory.')
  if not os.path.isfile(args.data_dir + '/ref.rttm'):
    sys.exit(args.data_dir + '/ref.rttm not found.')
  if not os.path.isfile(args.data_dir + '/wav.scp'):
    sys.exit(args.data_dir + '/wav.scp not found.')
  if not os.path.isfile(args.data_dir + '/frame_shift'):
    sys.exit(args.data_dir + '/frame_shift')
  if os.path.isfile(args.output_dir):
    sys.exit(args.output_dir + ' must not be a file.')
  if not os.path.isdir(args.output_dir):
    os.makedirs(args.output_dir)

  wav = {}
  f = open(args.data_dir + '/wav.scp', 'r')
  for line in f.readlines():
    try:
      recording_id, filepath = line.rstrip().split()
      wav[recording_id] = filepath
    except:
      pass
  f.close()

  cuts = []
  f = open(args.data_dir + '/ref.rttm', 'r')
  for line in f.readlines():
    try:
      cuts.append(Cut(Rttm(line)))
    except:
      pass
  f.close()
  recordings = cuts_to_recordings(cuts, array = False)
  recordings_cuts = {}
  for recording_id in recordings:
    recordings[recording_id].explicit_overlap()
    recordings_cuts[recording_id] = [Cut(cut) for cut in recordings[recording_id].get_cuts() \
            if cut.get_speakers_length() == 1]

  frame_shift = 0.01
  f = open(args.data_dir + '/frame_shift')
  frame_shift = float(f.readline().strip())
  f.close()

  utt2dur = {}
  utt2num_frames = {}
  f = open(args.data_dir + '/utt2dur', 'r')
  for line in f.readlines():
    try:
      recording_id, duration = line.strip().split()
      utt2dur[recording_id] = float(duration)
      utt2num_frames[recording_id] = int(round(utt2dur[recording_id] / frame_shift))
    except:
      pass
  f.close()

  recordings_frames_speakers = {}
  for recording_id, filepath in wav.items():
    if recording_id in recordings_cuts:
      recordings_frames_speakers[recording_id] = {}
      num_frames = utt2num_frames[recording_id]
      timestamps = [(round(frame * frame_shift, 2), round((frame + 1) * frame_shift, 2)) for frame in range(num_frames - 1)][1:]
      cuts = recordings_cuts[recording_id]
      cut_index = 0
      for timestamps_index, (begin, end) in enumerate(timestamps):
        timestamps_cuts = []
        while cut_index < len(cuts):
          if begin < round(cuts[cut_index].get_end_time(), 2) \
                  and round(cuts[cut_index].get_begin_time(), 2) < end:
            timestamps_cuts.append(cuts[cut_index])
          if cut_index + 1 < len(cuts) \
                  and round(cuts[cut_index + 1].get_end_time(), 2) \
                  and round(cuts[cut_index + 1].get_begin_time(), 2) < end:
            cut_index += 1
          else:
            break
        if len(timestamps_cuts) > 0:
          speakers = list(itertools.chain(*list(itertools.chain(*[[value.keys() for value in cut.get_speakers().values()] for cut in timestamps_cuts]))))
          if len(speakers) == 1:
            recordings_frames_speakers[recording_id][timestamps_index] = { 'begin': begin, 'end': end, 'speaker': speakers[0] }

  cp = torch.load('wav2vec_large.pt')
  model = Wav2VecModel.build_model(cp['args'], task=None)
  model.load_state_dict(cp['model'])
  model.eval()

  recordings_frames_features = {}
  for recording_id, filepath in wav.items():
    if recording_id in recordings_cuts:
      rate, data = wavfile.read(filepath)
      tensor = torch.tensor(np.copy(data))

      z = model.feature_extractor(tensor.unsqueeze(0))
      c = model.feature_aggregator(z)

      #z_numpy = z.detach().numpy()[0]
      z_numpy = c.detach().numpy()[0]
      num_frames = z_numpy.shape[1]
      recordings_frames_features[recording_id] = [(z_numpy[:, frame], recordings_frames_speakers[recording_id][frame]) for frame in range(num_frames) if frame in recordings_frames_speakers[recording_id]]


  segments_file = open(args.output_dir + '/segments', 'w')
  utt2spk_file = open(args.output_dir + '/utt2spk', 'w')
  ark_scp_output = 'ark:| copy-vector ark:- ark,scp:' + args.output_dir + '/ivector.ark,' + args.output_dir + '/ivector.scp'
  ark_file = kaldi_io.open_or_fd(ark_scp_output, 'wb')

  for recording_id in recordings_frames_features:
    utterance_count = 0
    for vector, values in recordings_frames_features[recording_id]:
      begin = values['begin']
      end = values['end']
      speaker = values['speaker']

      utterance_id = recording_id + '_' + str(utterance_count).zfill(3) + '-' + str(round(begin * 100)).zfill(8) + '-' + str(round(end * 100)).zfill(8)
      speaker_id = recording_id + '_' + speaker

      segments_file.write(utterance_id + ' ' + recording_id + ' ' + str(begin) + ' ' + str(end) + '\n')
      utt2spk_file.write(utterance_id + ' ' + speaker_id + '\n')
      kaldi_io.write_vec_flt(ark_file, vector, key = utterance_id)
      utterance_count += 1

  segments_file.close()
  utt2spk_file.close()
  ark_file.close()
    
if __name__ == '__main__':
  main()

