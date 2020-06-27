conf_vector = 'xvectors'
conf_vector_length = 512
conf_models_generation_length = 20
conf_models_container_length = 2
conf_permutations_include_zeros = False

import os
import json
from functools import reduce

# is_valid_segment [DONE]
def is_valid_segment(segment):
    return len(segment['speakers']) == 1 \
            and len(segment['ivectors']) == 1 \
            and len(segment['xvectors']) == 1 \
            and segment['speakers'][0]['speaker_id'] in ['A', 'B']

# load_recordings_segments [DONE]
def load_recordings_segments(directory):
    filenames = [filename for filename in os.listdir(directory) if os.path.isfile(os.path.join(directory, filename))]
    recordings_segments = {}
    recordings_length = len(filenames)
    recordings_count = 0
    for filename in filenames:
        recording_id = filename.split('.')[0]
        filepath = os.path.join(directory, filename)
        file = open(filepath, 'r')
        recordings_segments[recording_id] = [json.loads(line) for line in file.readlines()]
        file.close()
        recordings_segments[recording_id] = list(filter(is_valid_segment, recordings_segments[recording_id]))
        recordings_count += 1
        print('Loading ' + directory + ' ' + str(recordings_count) + '/' + str(recordings_length), end = '\r')
    return recordings_segments

# speakers_get_indexes [DONE]
def speakers_get_indexes(accumulator, speaker_tuple):
    speaker_id, index = speaker_tuple
    if speaker_id in accumulator:
        accumulator[speaker_id].append(index)
    else:
        accumulator[speaker_id] = [index]
    return accumulator

# balance_segments [DONE]
def balance_segments(recordings_segments, minimum_speakers, minimum_speaker_length):
    new_recordings_segments = {}
    for recording_id in recordings_segments:
        recording_segments = recordings_segments[recording_id]
        speakers_indexes = [(segment['speakers'][0]['speaker_id'], index) for index, segment in enumerate(recording_segments)]
        speakers_indexes = reduce(speakers_get_indexes, speakers_indexes, {})
        speakers_lengths = [(speaker_id, len(speakers_indexes[speaker_id])) for speaker_id in speakers_indexes]
        speakers_lengths.sort(key = lambda x: x[1])
        speakers_lengths_min = speakers_lengths[0][1]
        if len(speakers_lengths) >= minimum_speakers and speakers_lengths_min >= minimum_speaker_length:
            recording_indexes = []
            for speaker_id in speakers_indexes:
                speakers_indexes[speaker_id] = speakers_indexes[speaker_id][:speakers_lengths_min]
                recording_indexes += speakers_indexes[speaker_id]
            new_recordings_segments[recording_id] = [segment for index, segment in enumerate(recordings_segments[recording_id]) if index in recording_indexes]
    print('Recordings left: ' + str(len(new_recordings_segments)) + '/' + str(len(recordings_segments)))
    return new_recordings_segments

from torch.utils.data import Dataset
import numpy as np
import itertools

class Recordings_dataset(Dataset):
    def __init__(self, recordings_segments, recordings_ids):
        self.recordings_ids = recordings_ids if isinstance(recordings_ids, list) else [recordings_ids]
        self.recordings_segments = {}
        for recording_id in self.recordings_ids:
            self.recordings_segments[recording_id] = recordings_segments[recording_id]
        self.mode = conf_vector
        self.models_generation_length = conf_models_generation_length
        self.models_container_length = conf_models_container_length
        self.permutations_include_zeros = conf_permutations_include_zeros
        self.recordings_data = {}
        self.recordings_map = []
        self.recordings_length = 0
        for recording_id in self.recordings_ids:
            self.recordings_data[recording_id] = {}
            recording_segments = self.recordings_segments[recording_id]
            recording_data = self.recordings_data[recording_id]
            recording_data['speakers_indexes'] = [(segment['speakers'][0]['speaker_id'], index) for index, segment in enumerate(recording_segments)]
            recording_data['speakers_indexes'] = reduce(speakers_get_indexes, recording_data['speakers_indexes'], {})
            recording_data['speakers_indexes_lengths_max'] = max([len(recording_data['speakers_indexes'][speaker_id]) for speaker_id in recording_data['speakers_indexes']])
            recording_data['speakers_models'] = {}
            for speaker_id in recording_data['speakers_indexes']:
                speaker_indexes = recording_data['speakers_indexes'][speaker_id]
                speaker_vectors = [np.asarray(recording_segments[index][self.mode][0]['value']) for index in speaker_indexes[:self.models_generation_length]]
                recording_data['speakers_models'][speaker_id] = [np.sum(speaker_vectors, 0) / len(speaker_vectors)]
            if self.permutations_include_zeros:
                recording_data['permutations'] = list(itertools.permutations(list(recording_data['speakers_models'].keys()) \
                + ['0' for i in range(self.models_container_length)], self.models_container_length))
            else:
                recording_data['permutations'] = list(itertools.permutations(list(recording_data['speakers_models'].keys()), self.models_container_length))
            recording_data['permutations'] = list(set(recording_data['permutations']))
            recording_data['permutations'].sort()
            recording_data['permutations_map'] = []
            recording_data['permutations_length'] = 0
            for index, permutation in enumerate(recording_data['permutations']):
                speakers_models_length = int(np.prod([len(recording_data['speakers_models'][speaker_id]) for speaker_id in permutation if speaker_id != '0']))
                recording_data['permutations_map'].append((recording_data['permutations_length'], recording_data['permutations_length'] + speakers_models_length - 1, index))
                recording_data['permutations_length'] += speakers_models_length
            recording_data['length'] = len(recording_segments) * recording_data['permutations_length']
            self.recordings_map.append((self.recordings_length, self.recordings_length + recording_data['length'] - 1, recording_id))
            self.recordings_length += recording_data['length']
    def __len__(self):
        return self.recordings_length
    def __getitem__(self, idx):
        recording_tuple = list(filter(lambda recording_tuple: recording_tuple[0] <= idx and idx <= recording_tuple[1], self.recordings_map))[0]
        recording_idx = idx - recording_tuple[0]
        recording_id = recording_tuple[2]
        recording_data = self.recordings_data[recording_id]
        
        segment_id, segment_idx = divmod(recording_idx, recording_data['permutations_length'])
        segment = self.recordings_segments[recording_id][segment_id]
        target_id = segment['speakers'][0]['speaker_id']
        vector = np.asarray(segment[self.mode][0]['value'])
        
        permutation_tuple = list(filter(lambda permutation_tuple: permutation_tuple[0] <= segment_idx and segment_idx <= permutation_tuple[1], recording_data['permutations_map']))[0]
        permutation_id = permutation_tuple[2]
        permutation = recording_data['permutations'][permutation_id]
        
        models_container = [np.asarray(recording_data['speakers_models'][speaker_id][0]) if speaker_id != '0' else np.random.uniform(-0.1, 0.1, len(vector)) for speaker_id in permutation]
        models_weigths = np.asarray([len(recording_data['speakers_indexes'][speaker_id]) if speaker_id != '0' else recording_data['speakers_indexes_lengths_max'] for speaker_id in permutation])
        models_weigths_sum = np.sum(models_weigths)
        models_weigths = np.ones(len(models_weigths)) - models_weigths / models_weigths_sum
        
        x = [vector] + models_container
        y = np.asarray([speaker_id == target_id for speaker_id in permutation], dtype = float)
        z = models_weigths
        
        return x, y, z

import subprocess
import re

def plda_score(plda_filepath, ref_vector, test_vector):
    ref_string = str(list(ref_vector)).replace(',', '').replace('[', '[ ').replace(']', ' ]')
    test_string = str(list(test_vector)).replace(',', '').replace('[', '[ ').replace(']', ' ]')

    bin = './plda_score.sh'
    p = subprocess.Popen([bin, plda_filepath, ref_string, test_string], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = p.communicate()
    rc = p.returncode
    if rc == 0:
        lines =  output.decode("utf-8").split('\n')
        pldaLine = [line for line in lines if 'reference test' in line][0]
        return float(re.findall('\d+\.\d+', pldaLine)[0])
    else:
        print(err)
        exit('plda_socre.sh fail')

def xvectors_plda(plda_filepath, ref_vector, test_vector):
    ref_string = str(list(ref_vector)).replace(',', '').replace('[', '[ ').replace(']', ' ]')
    test_string = str(list(test_vector)).replace(',', '').replace('[', '[ ').replace(']', ' ]')

    bin = './xvectors_plda.sh'
    p = subprocess.Popen([bin, plda_filepath, ref_string, test_string], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = p.communicate()
    rc = p.returncode
    if rc == 0:
        lines =  output.decode("utf-8").split('\n')
        pldaLine = lines[0]
        return float(re.findall('\d+\.\d+', pldaLine)[0])
    else:
        print(err)
        exit('xvectors_plda.sh fail')

def md_eval(ref_filepath, res_filepath):
    bin = '../../../tools/sctk-2.4.10/src/md-eval/md-eval.pl'
    p = subprocess.Popen([bin, '-r', ref_filepath, '-s', res_filepath], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = p.communicate()
    rc = p.returncode
    if rc == 0:
        lines =  output.decode("utf-8").split('\n')
        derLine = [line for line in lines if 'OVERALL SPEAKER DIARIZATION ERROR' in line][0]
        return float(re.findall('\d+\.\d+', derLine)[0])
    else:
        exit('md-eval.pl fail')

def test_diarization(groundtruth_rttm_filepath, plda_filepath,  recordings_segments, recordings_ids):
    results = {}
    results_reduced = {}
    for recording_id in recordings_ids:
        print(recording_id, 'diarization start.')
        # Getting the speaker's models
        recording_dataset = Recordings_dataset(recordings_segments, recording_id)
        speakers_models = recording_dataset.recordings_data[recording_id]['speakers_models']
        speakers_models = [speakers_models[speaker_id][0] for speaker_id in speakers_models]
        #speakers_models.append(np.random.uniform(-0.1, 0.1, conf_vector_length))
        #speakers_models = [np.random.uniform(-0.1, 0.1, 128)] + (speakers_models)
        #speakers_models = [speakers_models[1]] + [np.random.uniform(-0.1, 0.1, 128)] + [speakers_models[0]]
        # At this point there is no information about the speaker identity, only the model
        results[recording_id] = []
        for segment in recordings_segments[recording_id]:
            vector = np.asarray(segment[conf_vector][0]['value'])
            output = [xvectors_plda(plda_filepath, speaker_model, vector) for speaker_model in speakers_models]
            index = np.argmax(output)
            #print(output, index)
            results[recording_id].append({ 'begining': segment['begining'], 'ending': segment['ending'], 'speaker_id': index })
            if len(results[recording_id]) > 2:
                if results[recording_id][len(results[recording_id]) - 1]['speaker_id'] == results[recording_id][len(results[recording_id]) - 3]['speaker_id']:
                    if results[recording_id][len(results[recording_id]) - 1]['speaker_id'] != results[recording_id][len(results[recording_id]) - 2]['speaker_id']:
                        results[recording_id][len(results[recording_id]) - 2]['speaker_id'] = results[recording_id][len(results[recording_id]) - 1]['speaker_id']
                        results[recording_id][len(results[recording_id]) - 1]['modified'] = True
        results_reduced[recording_id] = []
        last_speaker_id = -1
        last_speaker = { 'begining': 0, 'ending': 0, 'speaker_id': -1 }
        for segment in results[recording_id] + [{ 'begining': 0, 'ending': 0, 'speaker_id': -1 }]:
            begining = segment['begining']
            ending = segment['ending']
            speaker_id = segment['speaker_id']
            if last_speaker_id != speaker_id:
                if last_speaker_id != -1:
                    results_reduced[recording_id].append(last_speaker)
                last_speaker_id = speaker_id
                last_speaker = { 'begining': begining, 'ending': ending, 'speaker_id': speaker_id }
            else:
                if begining <= last_speaker['ending']:
                    last_speaker['ending'] = ending
                else:
                    if last_speaker_id != -1:
                        results_reduced[recording_id].append(last_speaker)
                    last_speaker_id = speaker_id
                    last_speaker = { 'begining': begining, 'ending': ending, 'speaker_id': speaker_id }
        results_rttm = ''
        for recording_id in results_reduced:
            for segment in results_reduced[recording_id]:
                result_rttm = 'SPEAKER ' + recording_id + ' 1 ' + str(segment['begining']) + ' ' + str(round(segment['ending'] - segment['begining'], 2)) + ' <NA> <NA> ' + str(segment['speaker_id']) + ' <NA> <NA>'
                results_rttm += result_rttm + '\n'

    #groundtruth_rttm_filepath = '../callhome1_1.0_0.5.rttm'
    file = open(groundtruth_rttm_filepath, 'r')
    groundtruth_rttm = ''.join([line for line in file.readlines() if (line.split(' ')[1] in recordings_ids) and \
                    (line.split(' ')[7] in ['A', 'B'])])
    file.close()

    file = open('test_results.rttm', 'w')
    file.write(results_rttm)
    file.close()

    file = open('test_groundtruth.rttm', 'w')
    file.write(groundtruth_rttm)
    file.close()

    return md_eval('test_groundtruth.rttm', 'test_results.rttm')

recordings_segments_directory = 'exp/pre_norm/dihard_2019_dev/json'
groundtruth_rttm_filepath = 'data/dihard_2019_dev_1.0_0.5.rttm'
plda_filepath = 'exp/plda/dihard_2019_eval/xvectors.plda'

recordings_segments = load_recordings_segments(recordings_segments_directory)
print()
recordings_valid_segments = balance_segments(recordings_segments, 2, 0)
recording_ids = [recording_id for recording_id in recordings_valid_segments]
recording_ids.sort()
der = test_diarization(groundtruth_rttm_filepath, plda_filepath, recordings_segments, recording_ids)
print(der)
