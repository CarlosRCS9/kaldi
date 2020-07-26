#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import functools
import numpy
import itertools

from scripts.models import Ivector

def get_first_speakers(data, length):
  if isinstance(data, dict):
    files_speakers_names = {}
    for file_id, segments in data.items():
      files_speakers_names[file_id] = get_first_speakers(segments, length)
    return files_speakers_names
  else:
    speakers_names = itertools.chain(*map(lambda segment: [speaker.get_name() for speaker in segment.get_speakers()], data))
    return list(dict.fromkeys(speakers_names).keys())[:length]

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

def get_speakers_models(segments, speakers_segments_indexes, models_generation_lengths):
  speakers_models = {}
  for speakers_names, indexes in speakers_segments_indexes.items():
    speakers_models[speakers_names] = {}
    for model_generation_length in models_generation_lengths:
      speakers_models[speakers_names][model_generation_length] = {}
      model_segments = [segments[index] for index in speakers_segments_indexes[speakers_names][:model_generation_length]]
      model_ivectors = numpy.transpose([[ivector for ivector in segment.get_ivectors()] for segment in model_segments])
      model_ivectors = [[ivector.get_value() for ivector in ivectors] for ivectors in model_ivectors]
      model_ivectors = [Ivector(numpy.sum(ivectors, 0) / len(ivectors)) for ivectors in model_ivectors]
      speakers_models[speakers_names][model_generation_length]['ivectors'] = model_ivectors
  return speakers_models

def get_speakers_permutations(speakers_models, length, include_zeros = True, include_overlaps = False):
    speakers_names = [speakers_names for speakers_names in speakers_models.keys() if include_overlaps\
                      or len(speakers_names.split(',')) == 1]
    if len(speakers_names) == 0:
        print('ERROR: no speakers left.')
    speakers_names += ['0' for _ in range(length)] if include_zeros or len(speakers_names) < length else []
    return sorted(set(itertools.permutations(speakers_names, length)))
