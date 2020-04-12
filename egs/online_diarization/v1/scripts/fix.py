from torch.utils.data import Dataset
import random
import numpy as np
import itertools

def generate_speaker_model(recording_segments,
                           speaker_segments_indexes,
                           models_generation_length,
                           vector = 'ivectors',
                           selection = 'first',
                           indexes = []):
    if selection == 'first':
        selected_segments = [recording_segments[index] for _, index, _ in speaker_segments_indexes[:models_generation_length]]
    elif selection == 'random':
        selected_segments = [recording_segments[index] for _, index, _ in random.sample(speaker_segments_indexes, models_generation_length if models_generation_length < len(speaker_segments_indexes) else len(speaker_segments_indexes))]
    else:
        print('ERROR: unknown speaker model segments selection strategy.')
    selected_vectors = [np.asarray(segment[vector][0]['value']) for segment in selected_segments]
    return np.sum(selected_vectors, 0) / len(selected_vectors)

def get_recordings_ids(acc, segment):
    if segment['recording_id'] not in acc:
        acc.append(segment['recording_id'])
    return acc

def get_speakers_segments_indexes(acc, recording_id_index_real, recording_segments):
    _, index, _ = recording_id_index_real
    speakers_ids = ','.join(sorted([speaker['speaker_id'] for speaker in recording_segments[index]['speakers']]))
    if speakers_ids not in acc:
        acc[speakers_ids] = []
    acc[speakers_ids].append(recording_id_index_real)
    return acc
    
class Recordings_dataset(Dataset):
    def __init__(self,
                 recordings_segments,
                 recordings_ids = None,
                 vector = 'ivectors',
                 models_container_length = 2,
                 models_container_include_zeros = True,
                 models_container_include_overlaps = False,
                 models_generation_lengths = [3],
                 models_generation_selection = 'first',
                 balance_segments = True,
                 balance_segments_selection = 'copy',
                 false_segments = True
                ):
        if recordings_ids is None:
            recordings_ids = [recording_id for recording_id in recordings_segments]
        self.recordings_ids = recordings_ids if isinstance(recordings_ids, list) else [recordings_ids]
        self.recordings_segments = {}
        for recording_id in self.recordings_ids:
            self.recordings_segments[recording_id] = recordings_segments[recording_id]
        self.vector = vector
        self.models_container_length = models_container_length
        self.models_container_include_zeros = models_container_include_zeros
        self.models_container_include_overlaps = models_container_include_overlaps
        self.models_generation_lengths = models_generation_lengths
        self.models_generation_selection = models_generation_selection
        self.balance_segments = balance_segments
        self.balance_segments_selection = balance_segments_selection
        self.false_segments = false_segments
        # ------------------------- #
        self.recordings_data = {}
        self.recordings_map = []
        self.recordings_length = 0
        for recording_id in self.recordings_ids:
            self.recordings_data[recording_id] = {}
            self.recordings_data[recording_id]['recording_segments_indexes'] = [(recording_id, index, True) for index, _ in enumerate(self.recordings_segments[recording_id])]
            # ----- Obtaining speakers segments indexes ----- #
            self.recordings_data[recording_id]['speakers_segments_indexes'] = reduce(lambda acc, recording_id_index_real: get_speakers_segments_indexes(acc, recording_id_index_real, self.recordings_segments[recording_id]), self.recordings_data[recording_id]['recording_segments_indexes'], {})
            # ----- Balancing speakers segments indexes ----- #
            self.recordings_data[recording_id]['speakers_segments_indexes_lengths_max'] = max([len(self.recordings_data[recording_id]['speakers_segments_indexes'][speakers_ids]) for speakers_ids in self.recordings_data[recording_id]['speakers_segments_indexes']])
            if self.balance_segments:
                if self.balance_segments_selection == 'copy':
                    for speakers_ids in self.recordings_data[recording_id]['speakers_segments_indexes']:
                        for i in range(self.recordings_data[recording_id]['speakers_segments_indexes_lengths_max'] - len(self.recordings_data[recording_id]['speakers_segments_indexes'][speakers_ids])):
                            recording_id_index_real = random.choice(self.recordings_data[recording_id]['speakers_segments_indexes'][speakers_ids])
                            self.recordings_data[recording_id]['recording_segments_indexes'].append(recording_id_index_real)
                            self.recordings_data[recording_id]['speakers_segments_indexes'][speakers_ids].append(recording_id_index_real)
                else:
                    print('ERROR: unknown balancing segments selection strategy.')
            # ----- Generating speakers models ----- #
            self.recordings_data[recording_id]['speakers_models'] = {}
            for speakers_ids in self.recordings_data[recording_id]['speakers_segments_indexes']:
                self.recordings_data[recording_id]['speakers_models'][speakers_ids] = {}
                for models_generation_length in models_generation_lengths:
                    speakers_model = generate_speaker_model(self.recordings_segments[recording_id], self.recordings_data[recording_id]['speakers_segments_indexes'][speakers_ids], models_generation_length, self.vector, self.models_generation_selection)
                    self.recordings_data[recording_id]['speakers_models'][speakers_ids][models_generation_length] = [speakers_model]
            # ----- Generating permutations ----- #
            if self.models_container_include_zeros:
                self.recordings_data[recording_id]['permutations'] = list(itertools.permutations(list(self.recordings_data[recording_id]['speakers_models'].keys()) \
                + ['0' for i in range(self.models_container_length)], self.models_container_length))
            else:
                self.recordings_data[recording_id]['permutations'] = list(itertools.permutations(list(self.recordings_data[recording_id]['speakers_models'].keys()), self.models_container_length))
            self.recordings_data[recording_id]['permutations'] = sorted(set(self.recordings_data[recording_id]['permutations']))
            if not self.models_container_include_overlaps:
                self.recordings_data[recording_id]['permutations'] = [permutation for permutation in self.recordings_data[recording_id]['permutations'] if all(len(speakers_ids.split(',')) == 1 for speakers_ids in permutation)]
            # ----- Generating false segments indexes ----- #
            if self.false_segments:
                other_recordings_segments_indexes = []
                for other_recording_id in self.recordings_segments:
                    if other_recording_id != recording_id:
                        for index, _ in enumerate(self.recordings_segments[other_recording_id]):
                            other_recordings_segments_indexes.append((other_recording_id, index, False))
                other_recordings_segments_indexes = random.sample(other_recordings_segments_indexes, self.recordings_data[recording_id]['speakers_segments_indexes_lengths_max'])
                options = [self.recordings_data[recording_id]['recording_segments_indexes'], other_recordings_segments_indexes]
                options_lengths = [len(option) for option in options]
                new_recording_segments_indexs = []
                while sum(options_lengths) > 0:
                    options_indexes = list(itertools.chain(*[[index] * len(option) for index, option in enumerate(options)]))
                    option_index = random.choice(options_indexes)
                    index_real = options[option_index].pop(0)
                    new_recording_segments_indexs.append(index_real)
                    options_lengths = [len(option) for option in options]
                self.recordings_data[recording_id]['recording_segments_indexes'] = new_recording_segments_indexs
            # ----- Calculating recording length ----- #
            self.recordings_data[recording_id]['permutations_map'] = []
            self.recordings_data[recording_id]['permutations_length'] = 0
            for index, permutation in enumerate(self.recordings_data[recording_id]['permutations']):
                speakers_models_length = int(np.prod([np.sum([len(self.recordings_data[recording_id]['speakers_models'][speakers_ids][models_generation_length]) for models_generation_length in self.recordings_data[recording_id]['speakers_models'][speakers_ids]]) for speakers_ids in permutation if speakers_ids != '0']))
                self.recordings_data[recording_id]['permutations_map'].append((self.recordings_data[recording_id]['permutations_length'], self.recordings_data[recording_id]['permutations_length'] + speakers_models_length - 1, index))
                self.recordings_data[recording_id]['permutations_length'] += speakers_models_length
            self.recordings_data[recording_id]['length'] = len(self.recordings_data[recording_id]['recording_segments_indexes']) * self.recordings_data[recording_id]['permutations_length']
            self.recordings_map.append((self.recordings_length, self.recordings_length + self.recordings_data[recording_id]['length'] - 1, recording_id))
            self.recordings_length += self.recordings_data[recording_id]['length']
    def __len__(self):
        return self.recordings_length
    def __getitem__(self, idx):
        recording_limits = list(filter(lambda recording_limits: recording_limits[0] <= idx and idx <= recording_limits[1], self.recordings_map))[0]
        recording_idx = idx - recording_limits[0]
        recording_id = recording_limits[2]
        recording_data = self.recordings_data[recording_id]
        
        segment_index, segment_idx = divmod(recording_idx, recording_data['permutations_length'])
        index_real = recording_data['recording_segments_indexes'][segment_index]
        segment = self.segments[index_real[0]]
        vector = np.asarray(segment[self.vector][0]['value'])
        
        permutation_limits = list(filter(lambda permutation_limits: permutation_limits[0] <= segment_idx and segment_idx <= permutation_limits[1], recording_data['permutations_map']))[0]
        permutation_idx = segment_idx - permutation_limits[0]
        permutation_index = permutation_limits[2]
        permutation = recording_data['permutations'][permutation_index]
        
        speakers_models_lengths = [np.sum([len(recording_data['speakers_models'][speakers_ids][models_generation_length]) for models_generation_length in recording_data['speakers_models'][speakers_ids]])  if speakers_ids != '0' else 1 for speakers_ids in permutation]
        models_container = []
        model_index = permutation_idx
        for i, length_i in enumerate(speakers_models_lengths):
            if i != len(speakers_models_lengths) - 1:
                model_index, remainder = divmod(model_index, np.sum(speakers_models_lengths[i + 1:]))
            else:
                model_index = remainder
            models_container.append(recording_data['speakers_models'][permutation[i]][self.models_generation_lengths[model_index]][0] if permutation[i] != '0' else np.random.uniform(-0.1, 0.1, len(vector)))
        
        models_weigths = np.asarray([len(recording_data['speakers_segments_indexes'][speakers_ids]) if speakers_ids != '0' else recording_data['speakers_segments_indexes_lengths_max'] for speakers_ids in permutation])
        models_weigths_sum = np.sum(models_weigths)
        models_weigths = np.ones(len(models_weigths)) - models_weigths / models_weigths_sum
        
        targets_ids = [speaker['speaker_id'] for speaker in segment['speakers']]
        
        x = [vector] + models_container
        if self.models_container_include_overlaps:
            targets_ids = ','.join(sorted(list(set(targets_ids))))
            y = np.asarray([speakers_ids == targets_ids for speakers_ids in permutation], dtype = float)
        else:
            y = np.asarray([speaker_id in targets_ids for speaker_id in permutation], dtype = float) / len(targets_ids)
        z = models_weigths
        
        return x, y, z
    
recording_dataset = Recordings_dataset(a_recordings_train_segments)