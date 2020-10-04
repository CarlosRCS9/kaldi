#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import functools
import numpy
import itertools
import random

from models import Ivector, Xvector

def get_first_speakers(data, length = None):
  if isinstance(data, dict):
    files_speakers_names = {}
    for file_id, segments in data.items():
      files_speakers_names[file_id] = get_first_speakers(segments, length)
    return files_speakers_names
  else:
    speakers_names = itertools.chain(*map(lambda segment: [speaker.get_name() for speaker in segment.get_speakers()], data))
    speakers_names = list(dict.fromkeys(speakers_names).keys())
    return speakers_names if length is None else speakers_names[:length]

def get_best_speakers(segments, length):
  if isinstance(segments, dict):
    files_speakers_names = {}
    for file_id, segments_ in segments.items():
      files_speakers_names[file_id] = get_best_speakers(segments_, length)
    return files_speakers_names
  else:
    speakers_names_count = {}
    for segment in segments:
      for speaker in segment.get_speakers():
        if speaker.get_name() not in speakers_names_count:
          speakers_names_count[speaker.get_name()] = 0
        speakers_names_count[speaker.get_name()] += 1
    return list(map(lambda value: value[0], sorted(speakers_names_count.items(), key = lambda value: value[1], reverse = True)[:length]))

def limit_segments_speakers_names(segments, speakers_names, log = False):
  if isinstance(segments, dict) and isinstance(speakers_names, dict):
    files_segments = {}
    original_length = 0
    new_length = 0
    for file_id, segments_ in segments.items():
      if file_id in speakers_names:
        files_segments[file_id] = limit_segments_speakers_names(segments_, speakers_names[file_id], False)
        original_length += len(segments_)
        new_length += len(files_segments[file_id])
      else:
        original_length += len(segments_)
    if log:
      print('Kept ' + str(new_length) + ' of ' + str(original_length) + ': ' + str(new_length / original_length))
    return files_segments
  elif not (isinstance(segments, dict) or isinstance(speakers_names, dict)):
    new_segments = list(filter(lambda segment: all([speaker.get_name() in speakers_names for speaker in segment.get_speakers()]), segments))
    if log:
      print('Kept ' + str(len(new_segments)) + ' of ' + str(len(segments)) + ': ' + str(len(new_segments) / len(segments)))
    return new_segments
  else:
    print('ERROR: data type mismatch.')
    return segments

def limit_segments_speakers_length(segments, length = 1, log = False):
  if isinstance(segments, dict):
    files_segments = {}
    original_length = 0
    new_length = 0
    for file_id, segments_ in segments.items():
      files_segments[file_id] = limit_segments_speakers_length(segments_, length, False)
      original_length += len(segments_)
      new_length += len(files_segments[file_id])
    if log:
      print('Kept ' + str(new_length) + ' of ' + str(original_length) + ': ' + str(new_length / original_length))
    return files_segments
  else:
    new_segments = list(filter(lambda segment: len(segment.get_speakers()) <= length, segments))
    if log:
      print('Kept ' + str(len(new_segments)) + ' of ' + str(len(segments)) + ': ' + str(len(new_segments) / len(segments)))
    return new_segments

def balance_speakers_segments_length(segments, log = False):
  if isinstance(segments, dict):
    files_segments = {}
    original_length = 0
    new_length = 0
    for file_id, segments_ in segments.items():
      files_segments[file_id] = balance_speakers_segments_length(segments_, False)
      original_length += len(segments_)
      new_length += len(files_segments[file_id])
    if log:
      print('Kept ' + str(new_length) + ' of ' + str(original_length) + ': ' + str(new_length / original_length))
    return files_segments
  else:
    speakers_segments_indexes = get_speakers_segments_indexes(enumerate(segments))
    min_length = min([len(indexes) for indexes in speakers_segments_indexes.values()])
    for speakers_names, indexes in speakers_segments_indexes.items():
      speakers_segments_indexes[speakers_names] = indexes[:min_length]
    indexes = sorted(itertools.chain(*[indexes for indexes in speakers_segments_indexes.values()]))
    new_segments = [segments[index] for index in indexes]
    if log:
      print('Kept ' + str(len(new_segments)) + ' of ' + str(len(segments)) + ': ' + str(len(new_segments) / len(segments)))
    return new_segments

def limit_speakers_number(data, length, log = False):
  if isinstance(data, dict):
    files_segments = {}
    original_length = 0
    new_length = 0
    for file_id, segments in data.items():
      files_segments[file_id] = limit_speakers_number(segments, length, False)
      original_length += len(segments)
      new_length += len(files_segments[file_id])
    if log:
      print('Kept ' + str(new_length) + ' of ' + str(original_length) + ': ' + str(new_length / original_length))
    return files_segments
  else:
    new_segments = list(filter(lambda segment: len(segment.get_speakers()) <= length, data))
    if log:
      print('Kept ' + str(len(new_segments)) + ' of ' + str(len(data)) + ': ' + str(len(new_segments) / len(data)))
    return new_segments

def reduce_speakers_segments_indexes(accumulator, index_segment):
  index, segment = index_segment
  speakers_names = ','.join(sorted(map(lambda speaker: speaker.get_name(), segment.get_speakers())))
  if speakers_names not in accumulator:
    accumulator[speakers_names] = []
  accumulator[speakers_names].append(index)
  return accumulator

def get_speakers_segments_indexes(indexes_segments):
  return functools.reduce(reduce_speakers_segments_indexes, indexes_segments, {})

def get_speakers_models(segments, speakers_segments_indexes, models_generation_lengths, speakers = None):
  speakers_models = {}
  for speakers_names, indexes in speakers_segments_indexes.items():
    if speakers is None or speakers_names in speakers:
      speakers_models[speakers_names] = {}
      for model_generation_length in models_generation_lengths:
        speakers_models[speakers_names][model_generation_length] = {}
        model_segments = [segments[index] for index in speakers_segments_indexes[speakers_names][:model_generation_length]]   
        
        for name in ['ivectors', 'xvectors']:
          get_embeddings = lambda name, segment: segment.get_ivectors() if name == 'ivectors' else segment.get_xvectors()
          model_embeddings = numpy.transpose([get_embeddings(name, segment) for segment in model_segments])
          model_embeddings = [[embedding.get_value() for embedding in embeddings] for embeddings in model_embeddings]
          model_embeddings = [(Ivector if name == 'ivectors' else Xvector)(numpy.sum(embeddings, 0) / len(embeddings)) for embeddings in model_embeddings]
          speakers_models[speakers_names][model_generation_length][name] = model_embeddings
  return speakers_models

def get_speakers_permutations(speakers_models, length, include_zeros = True, include_overlaps = False):
  speakers_names = [speakers_names for speakers_names in speakers_models.keys() if include_overlaps or len(speakers_names.split(',')) == 1]
  if len(speakers_names) == 0:
    print('ERROR: no speakers left.')
  speakers_names += ['0' for _ in range(length)] if include_zeros or len(speakers_names) < length else []
  return sorted(set(itertools.permutations(speakers_names, length)))

def get_speakers_weights(speakers_segments_indexes, permutations, zero_multiplier = 1):
  zero_multiplier = 1 / zero_multiplier
  speakers_segments_lengths = {}
  for speakers_names, segments_indexes in speakers_segments_indexes.items():
    speakers_segments_lengths[speakers_names] = len(segments_indexes)
  outputs = list(itertools.chain(*permutations))
  speakers_weights = {}
  for speakers_names in outputs:
    segments_length = sum(speakers_segments_lengths.values())
    speakers_length = speakers_segments_lengths[speakers_names] if speakers_names != '0' else segments_length * zero_multiplier
    if speakers_names not in speakers_weights:
      speakers_weights[speakers_names] = 0
    speakers_weights[speakers_names] += speakers_length
    if '0' in outputs and speakers_names != '0':
      speakers_weights['0'] += (segments_length - speakers_length) * zero_multiplier
  weight_sum = sum(speakers_weights.values())
  weight_count = len(speakers_weights.values())
  speakers_weights_inverse = {}
  for speakers_names, weight in speakers_weights.items():
    speakers_weights_inverse[speakers_names] = (weight_sum - speakers_weights[speakers_names]) / ((weight_count - 1) * weight_sum)
  return speakers_weights_inverse

class Permutations:
  def __init__(self, speakers_names, samples, sample_length = None, include_zeros = True, mode = 'uniform'):
    self.samples = samples if isinstance(samples, int) else 0
    self.sample_length = sample_length if isinstance(sample_length, int) else len(speakers_names) 
    self.include_zeros = include_zeros == True
    self.mode = mode
    self.speakers_names = ['0'] if self.include_zeros else []
    for speaker_name in speakers_names:
      if speaker_name not in self.speakers_names:
        self.speakers_names.append(speaker_name)

    self.permutations = []
    self.speakers_names_counts = {}
    for speaker_name in self.speakers_names:
      self.speakers_names_counts[speaker_name] = 0
    if self.mode == 'uniform':
      for i in range(self.samples):
        sample = []
        for j in range(self.sample_length):
          speaker_name = random.choice(self.speakers_names)
          while speaker_name != '0' and speaker_name in sample:
            speaker_name = random.choice(self.speakers_names)
          sample.append(speaker_name)
          self.speakers_names_counts[speaker_name] += 1
        self.permutations.append(sample)
  def __len__(self):
    return self.samples
  def __getitem__(self, key):
    return self.permutations[key]
  def get_speakers_names_counts(self):
    return self.speakers_names_counts

def get_speakers_weights_2(segments, permutations):
  speakers_weights = {}
  index = 0
  for permutation in permutations:
    segment_speakers_names = [speaker.get_name() for speaker in segments[index].get_speakers()]
    for speaker_name in permutation:
      if speaker_name in segment_speakers_names:
        if speaker_name not in speakers_weights:
          speakers_weights[speaker_name] = 0
        speakers_weights[speaker_name] += 1
      else:
        if '0' not in speakers_weights:
          speakers_weights['0'] = 0
        speakers_weights['0'] += 1
    index += 1
    if index == len(segments):
      index = 0
  weight_sum = sum(speakers_weights.values())
  weight_count = len(speakers_weights.values())
  speakers_weights_inverse = {}
  for speaker_name, weight in speakers_weights.items():
    speakers_weights_inverse[speaker_name] = (weight_sum - speakers_weights[speaker_name]) / ((weight_count - 1) * weight_sum)
  return speakers_weights_inverse
