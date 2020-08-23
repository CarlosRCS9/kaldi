import copy
import kaldi_utils

def tracking_tester(recordings_segments,
                    recordings_ids = None,
                    scoring_function = None,
                    groundtruth_filepath = '',
                    groundtruth_valid_speakers_ids = ['A', 'B'],
                    vector = 'ivectors',
                    models_container_length = 2,
                    models_container_include_overlaps = False,
                    models_generation_length = 3,
                    models_generation_selection = 'first',
                    save_dir = 'tmp'):

    if recordings_ids is None:
        recordings_ids = [recording_id for recording_id in recordings_segments]
    recordings_ids = recordings_ids if isinstance(recordings_ids, list) else [recordings_ids]
    recordings_ids.sort()
    
    results = {}
    results_reduced = {}
    results_rttm = ''
    results_scores = {}
    eer_scores = ''
    dcf_scores = ''
    dcf_trials = ''
    for i, recording_id in enumerate(recordings_ids):
        print('tracking running: recording ' + str(i + 1) + '/' + str(len(recordings_ids)), end = '\r')
        # ----- Generating the models of each speaker in this recording ----- #
        recording_dataset = Recordings_dataset(recordings_segments,
                                               recording_id,
                                               vector = vector,
                                               models_container_length = models_container_length,
                                               models_container_include_zeros = False,
                                               models_container_include_overlaps = models_container_include_overlaps,
                                               models_generation_lengths = [models_generation_length],
                                               models_generation_selection = models_generation_selection)
        speakers_models = recording_dataset.recordings_data[recording_id]['speakers_models']
        speakers_segments_indexes_lengths_max = recording_dataset.recordings_data[recording_id]['speakers_segments_indexes_lengths_max']
        speakers_ids = [speakers_ids for speakers_ids in speakers_models]
        models_container = [speakers_models[speakers_ids][models_generation_length][0] for speakers_ids in speakers_models if models_container_include_overlaps or len(speakers_ids.split(',')) == 1]
        # ----- Filling with 0's the remaining spaces of the speaker's models container ----- #
        for i in range(models_container_length - len(models_container)):
            models_container.append(np.random.uniform(-0.1, 0.1, len(models_container[0])))
            
        # ----- Obtaining the recording segments indexes ----- #
        recording_segments_indexes = [(recording_id, index, True) for index, segment, in enumerate(recordings_segments[recording_id])]
        
        '''# ----- Generating the false segments indexes ----- #
        other_recordings_segments = {}
        other_recordings_segments_indexes = []
        
        for other_recording_id in recordings_segments:
            if other_recording_id != recording_id:
                other_recordings_segments[other_recording_id] = []
                #other_recordings_segments_indexes += [(other_recording_id, index, False) for index, segment in enumerate(recordings_segments[other_recording_id])]
                other_dataset = Recordings_dataset(recordings_segments,
                                                   other_recording_id,
                                                   vector = vector,
                                                   models_container_length = models_container_length,
                                                   models_container_include_zeros = False,
                                                   models_container_include_overlaps = models_container_include_overlaps,
                                                   models_generation_lengths = [models_generation_length],
                                                   models_generation_selection = models_generation_selection)
                other_speakers_models = other_dataset.recordings_data[other_recording_id]['speakers_models']
                other_speakers_segments = [other_dataset.recordings_data[other_recording_id]['speakers_segments_indexes'][speakers_ids][0] for speakers_ids in other_speakers_models]
                other_speakers_segments = [copy.deepcopy(recordings_segments[segment_recording_id][segment_index]) for segment_recording_id, segment_index, segment_real in other_speakers_segments]
                other_speakers_models = [other_speakers_models[speakers_ids][models_generation_length][0] for speakers_ids in other_speakers_models]
                for index, segment in enumerate(other_speakers_segments):
                    other_speakers_segments[index][vector][0]['value'] = other_speakers_models[index]
                    other_recordings_segments[other_recording_id].append(other_speakers_segments[index])
                    other_recordings_segments_indexes.append((other_recording_id, len(other_recordings_segments[other_recording_id]) - 1, False))                

        #other_recordings_segments_indexes = random.sample(other_recordings_segments_indexes, speakers_segments_indexes_lengths_max if speakers_segments_indexes_lengths_max < len(other_recordings_segments_indexes) else len(other_recordings_segments_indexes))    
        options = [recording_segments_indexes, other_recordings_segments_indexes]
        options_lengths = [len(option) for option in options]
        new_recording_segments_indexes = []
        while sum(options_lengths) > 0:
            options_indexes = list(itertools.chain(*[[index] * len(option) for index, option in enumerate(options)]))
            option_index = random.choice(options_indexes)
            new_recording_segments_indexes.append(options[option_index].pop(0))
            options_lengths = [len(option) for option in options]
        recording_segments_indexes = new_recording_segments_indexes'''
        
        # ----- Obtaining the recording tracking results ----- #
        results[recording_id] = []
        results_scores[recording_id] = []
        for segment_recording_id, segment_index, segment_real in recording_segments_indexes:
            #segment = recordings_segments[segment_recording_id][segment_index]
            if segment_real:
                segment = recordings_segments[segment_recording_id][segment_index]
            else:
                segment = other_recordings_segments[segment_recording_id][segment_index]
            segment_vector = np.asarray(segment[vector][0]['value'])
            segment_vector_id = segment[vector][0]['ivector_id' if vector == 'ivectors' else 'xvector_id']
            
            scores = scoring_function(segment_vector, models_container)
            
            targets_ids = sorted([speaker['speaker_id'] for speaker in segment['speakers']])
            labels = ['target' if segment_real and targets_ids == sorted(speaker_id.split(',')) else 'nontarget' for speaker_id in speakers_ids]
            
            utterances = [recording_id + '_' + speaker_id for speaker_id in speakers_ids]
            
            # utt1, utt2, score, target/nontarget
            scores_labels = list(zip([segment_vector_id for speaker_id in speakers_ids], utterances, labels, scores))
            results_scores[recording_id].append(scores_labels)
            
            if segment_real:
                index = np.argmax(scores)
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
        for scores_labels in results_scores[recording_id]:
            for score_label in scores_labels:
                # ('iaab_000-00000000-00000099', 'iaab_B', 'target', 0.9978078)
                eer_score = '{:f}'.format(score_label[3]) + ' ' + score_label[2]
                eer_scores += eer_score + '\n'
                dcf_score = score_label[0] + ' ' + score_label[1] + ' ' + '{:f}'.format(score_label[3])
                dcf_scores += dcf_score + '\n'
                dcf_trial = score_label[0] + ' ' + score_label[1] + ' '+ score_label[2]
                dcf_trials += dcf_trial + '\n'
        for segment in results_reduced[recording_id]:
            result_rttm = 'SPEAKER ' + recording_id + ' 1 ' + str(segment['begining']) + ' ' + str(round(segment['ending'] - segment['begining'], 2)) + ' <NA> <NA> ' + str(segment['speaker_id']) + ' <NA> <NA>'
            results_rttm += result_rttm + '\n'
    print('traking done: recording', str(i + 1) + '/' + str(len(recordings_ids)), '          ')

    file = open(groundtruth_filepath, 'r')
    groundtruth_rttm = ''.join([line for line in file.readlines() if (line.split(' ')[1] in recordings_ids) and \
                    (line.split(' ')[7] in groundtruth_valid_speakers_ids)])
    file.close()
    
    !mkdir -p $save_dir
    
    file = open(save_dir + '/eer.scores', 'w')
    file.write(eer_scores)
    file.close()
    
    file = open(save_dir + '/dcf.scores', 'w')
    file.write(dcf_scores)
    file.close()
    
    file = open(save_dir + '/dcf.trials', 'w')
    file.write(dcf_trials)
    file.close()
    
    file = open(save_dir + '/groundtruth.rttm', 'w')
    file.write(groundtruth_rttm)
    file.close()
    
    file = open(save_dir + '/results.rttm', 'w')
    file.write(results_rttm)
    file.close()
    
    output_der = kaldi_utils.md_eval(save_dir + '/groundtruth.rttm', save_dir + '/results.rttm', log_directory=save_dir)
    output_eer = kaldi_utils.compute_eer(save_dir + '/eer.scores', log_directory=save_dir)
    output_dcf = kaldi_utils.compute_min_dcf(save_dir + '/dcf.scores', save_dir + '/dcf.trials', log_directory=save_dir)

    return { 'der': output_der, 'eer': output_eer, 'dcf': output_dcf }

for vector in ['xvectors']:
    vector_length = 128 if vector == 'ivectors' else 128
    for models_generation_length in [5, 10, 20]:
        for i in range(1):
            print(vector, vector_length, models_generation_length, i)

            test_id = 'dihard_PLDA_clean_' + vector + '_' + str(models_generation_length) + '_' + str(i)

            a_results = tracking_tester(a_recordings_test_segments,
                                        scoring_function = lambda vector, models_container: plda_selector(vector, models_container, b_plda),
                                        groundtruth_filepath = a_groundtruth,
                                        groundtruth_valid_speakers_ids = ['A', 'B'],
                                        vector = vector,
                                        models_container_length = models_container_length,
                                        models_container_include_overlaps = models_container_include_overlaps,
                                        models_generation_length = models_generation_length,
                                        models_generation_selection = models_generation_selection,
                                        save_dir = 'batch/' + test_id + '_a')

            b_results = tracking_tester(b_recordings_test_segments,
                                        scoring_function = lambda vector, models_container: plda_selector(vector, models_container, a_plda),
                                        groundtruth_filepath = b_groundtruth,
                                        groundtruth_valid_speakers_ids = ['A', 'B'],
                                        vector = vector,
                                        models_container_length = models_container_length,
                                        models_container_include_overlaps = models_container_include_overlaps,
                                        models_generation_length = models_generation_length,
                                        models_generation_selection = models_generation_selection,
                                        save_dir = 'batch/' + test_id + '_b')

            print(a_results)
            print(b_results)
            output_der = (a_results['der'] + b_results['der']) / 2
            output_eer = (a_results['eer'] + b_results['eer']) / 2
            output_dcf = (a_results['dcf'] + b_results['dcf']) / 2
            results = { 'der': output_der, 'eer': output_eer, 'dcf': output_dcf }
            print(results)

            file = open('batch/results.csv', 'a')
            file.write(test_id + ', ' + json.dumps(a_results) + ', ' + json.dumps(b_results) + ', ' + json.dumps(results) + '\n')
            file.close()
