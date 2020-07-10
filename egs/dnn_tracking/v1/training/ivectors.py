#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import argparse

import sys
spath = '../'
sys.path.insert(0, spath)
from scripts.models import get_rttm_segments_features, sort_segments_by_speakers, Ivector
from scripts.notebook import limit_speakers_number, get_speakers_segments_indexes, get_speakers_models, get_speakers_permutations
from torch.utils.data import Dataset
import numpy
import pytorch_lightning
import torch
torch.set_default_tensor_type(torch.cuda.FloatTensor)
from torch.utils.data import DataLoader

class Files_dataset(Dataset):
    def __init__(self,
                 files_segments,
                 models_generation_lengths = [3],
                 models_container_length = 2,
                 include_zeros = True,
                 include_overlaps = False,
                 feature='ivectors'):
        self.files_segments = files_segments
        self.include_overlaps = include_overlaps
        self.feature = feature
        self.speakers_segments_indexes = {}
        self.speakers_models = {}
        self.speakers_permutations = {}
        self.lookup = []
        self.length = 0
        for file_id, segments in self.files_segments.items():
            self.speakers_segments_indexes[file_id] = get_speakers_segments_indexes(enumerate(segments))
            self.speakers_models[file_id] = get_speakers_models(segments,
                                                                self.speakers_segments_indexes[file_id],
                                                                models_generation_lengths)
            self.speakers_permutations[file_id] = get_speakers_permutations(self.speakers_models[file_id],
                                                                            models_container_length,
                                                                            include_zeros,
                                                                            include_overlaps)
            for index, permutation in enumerate(self.speakers_permutations[file_id]):
                models_length = numpy.prod([len(self.speakers_models[file_id][speakers_names].keys())\
                if speakers_names != '0' else 1 for speakers_names in permutation])
                length = models_length * len(segments)
                self.lookup.append({\
                                    'file_id': file_id,\
                                    'permutation_index': index,\
                                    'models_length': models_length,\
                                    'segments_length': len(segments),\
                                    'permutation_length': length,\
                                    'onset': self.length,\
                                    'end': self.length + length - 1 })
                self.length += length

    def __len__(self):
        return self.length

    def __getitem__(self, idx):
        lookup = [value for value in self.lookup if value['onset'] <= idx and idx <= value['end']][0]
        index = idx - lookup['onset']
        permutation = self.speakers_permutations[lookup['file_id']][lookup['permutation_index']]
        remainder, segment_index = divmod(index, lookup['segments_length'])
        models_container = []
        for index, speakers_names in enumerate(permutation):
            models_lengths = [len(self.speakers_models[lookup['file_id']][speakers_names].keys()) if speakers_names != '0' else 1 for speakers_names in permutation][index + 1:]
            if index != len(permutation) - 1:
                model_index, remainder = divmod(remainder, int(numpy.prod(models_lengths)))
            else:
                model_index = remainder
            if speakers_names != '0':
                models_container.append(self.speakers_models[lookup['file_id']][speakers_names][list(self.speakers_models[lookup['file_id']][speakers_names].keys())[model_index]])
            else:
                # TODO: improve
                models_container.append({ 'ivectors': [Ivector(numpy.random.uniform(-0.1, 0.1, 400).astype(numpy.float32))] })
        segment = self.files_segments[lookup['file_id']][segment_index]
        segment_speakers = [speaker.get_name() for speaker in segment.get_speakers()]
        x = [value[self.feature][0].get_value() for value\
             in models_container + [{ 'ivectors': segment.get_ivectors() }]]
        if self.include_overlaps:
            segment_speakers = ','.join(sorted(set(segment_speakers)))
            y = numpy.asarray([speakers_names == segment_speakers for speakers_names in permutation], dtype = numpy.float32)
        else:
            y = numpy.asarray([speakers_names in segment_speakers for speakers_names in permutation], dtype = numpy.float32) / len(segment_speakers)
        return x, y

class DNNModel(pytorch_lightning.LightningModule):

    def __init__(self):
        super().__init__()
        m = 400 # embedding length
        n = 2   # models container length
        self.cnn1 = torch.nn.Sequential(
            torch.nn.Conv1d((n + 1), n ** 3, 3),
            torch.nn.ReLU(),
            torch.nn.Conv1d(n ** 3, n ** 2, 3),
            torch.nn.ReLU(),
            torch.nn.Conv1d(n ** 2, n, 3),
            torch.nn.ReLU(),
        )
        self.fc1 = torch.nn.Sequential(
            torch.nn.Linear((m - 6) * n, n * 32),
            torch.nn.ReLU(),
            torch.nn.Linear(n * 32, n * 16),
            torch.nn.ReLU(),
            torch.nn.Linear(n * 16, n),
            torch.nn.Sigmoid(),
        )

    def forward(self, x):
        x = torch.stack(x, 1)
        x = self.cnn1(x)
        x = x.view(x.shape[0], -1)
        x = self.fc1(x)
        return x

    def training_step(self, batch, batch_nb):
        x, y = batch
        criterion = torch.nn.BCELoss()
        loss = criterion(self(x), y)
        tensorboard_logs = {'train_loss': loss}
        return {'loss': loss, 'log': tensorboard_logs}

    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters(), lr = 0.0001)

def get_args():
  parser = argparse.ArgumentParser()
  parser.add_argument('--gpus', default=None)
  args = parser.parse_args()
  return args

def main():
  args = get_args()
  # -------------------------------------------------- #
  print('Loading dev segments...')
  dev_rttm     = '../exp/dihardii/development/ref_augmented_0_1.5_0.5_0.5.rttm'
  dev_segments = '../exp/dihardii/development/augmented_0/segments'
  dev_ivectors = '../exp/dihardii/development/augmented_0/exp/make_ivectors/ivector.txt'
  dev_files_segments = get_rttm_segments_features(dev_rttm, dev_segments, dev_ivectors)
  # -------------------------------------------------- #
  print('Loading eval segments...')
  eval_rttm     = '../exp/dihardii/evaluation/ref_augmented_0_1.5_0.5_0.5.rttm'
  eval_segments = '../exp/dihardii/evaluation/augmented_0/segments'
  eval_ivectors = '../exp/dihardii/evaluation/augmented_0/exp/make_ivectors/ivector.txt'
  eval_files_segments = get_rttm_segments_features(eval_rttm, eval_segments, eval_ivectors)
  # -------------------------------------------------- #
  dev_files_segments_lim = limit_speakers_number(dev_files_segments, 2, log = True)
  eval_files_segments_lim = limit_speakers_number(eval_files_segments, 2, log = True)
  # -------------------------------------------------- #
  train_loader = DataLoader(Files_dataset(dev_files_segments_lim), batch_size = 128, shuffle = True, num_workers=4, pin_memory=True)
  model = DNNModel()
  trainer = pytorch_lightning.Trainer(gpus = args.gpus, distributed_backend = 'ddp', progress_bar_refresh_rate = 20)    
  trainer.fit(model, train_loader)

if __name__ == '__main__':
    main()
