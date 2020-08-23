#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import argparse
import os

from kaldi_utils import md_eval, compute_eer2, compute_min_dcf

callhome_invalid = ['iaab', 'iaad', 'iaae', 'iaag', 'iaah', 'iaaj', 'iaak', 'iaao', 'iaap', 'iaas', 'iaav', 'iaaz', 'iaba', 'iabd', 'iabg', 'iabh', 'iabi', 'iabn', 'iabq', 'iabu', 'iabz', 'iacb', 'iace', 'iacf', 'iacg', 'iack', 'iacn', 'iacu', 'iadh', 'iadi', 'iadj', 'iadk', 'iadm', 'iado', 'iadp', 'iadq', 'iadr', 'iadt', 'iadw', 'iadx', 'iaec', 'iaem', 'iaeq', 'iaer', 'iaet', 'iaeu', 'iaex', 'iaez', 'iafb', 'iafe', 'iaff', 'iafh', 'iafn', 'iafp', 'iafr', 'iafs', 'iafu', 'iafx', 'iaga', 'iagc', 'iage', 'iagg', 'iagj', 'iagm', 'iagp', 'iagr', 'iags', 'iagt', 'iagu', 'iagv', 'iagw', 'iagx', 'iagy', 'iagz', 'iahb', 'iahd', 'iahe', 'iahf', 'iahk', 'iahp', 'iahs', 'iahu', 'iaif', 'iaig', 'iaii', 'iaij', 'iail', 'iaio', 'iaip', 'iaiq', 'iais', 'iait', 'iaiv', 'iaiw', 'iaiy', 'iajb', 'iajg', 'iajj', 'iajk', 'iajn', 'iajq', 'iajr', 'iajs', 'iaju', 'iaka', 'iake', 'iakf', 'iakg', 'iaki', 'iakk', 'iakn', 'iako', 'iakp', 'iakr', 'iaku', 'iakv', 'ialb', 'ialf', 'ialh', 'ialj', 'ialk', 'iall', 'ialn', 'ialu', 'ialv', 'ialz', 'iama', 'iamd', 'iame', 'iamf', 'iamg', 'iamh', 'iaml', 'iams', 'iamt', 'iamu', 'iamw', 'ianb', 'iand', 'iang', 'ianj', 'iank', 'iann', 'iano', 'ianp', 'ianq', 'ianr', 'ians', 'iant', 'ianu', 'ianv', 'ianx', 'iaoa', 'iaoc', 'iaoh', 'iaon', 'iaop', 'iaos', 'iaov', 'iaoy', 'iaoz', 'iapd', 'iapj', 'iapl', 'iapo', 'iapq', 'iaps', 'iapt', 'iapu', 'iapv', 'iapx', 'iapz', 'iaqb', 'iaqc', 'iaqf', 'iaqg', 'iaqk', 'iaqs', 'iaqw', 'iaqx', 'iaqz', 'iard', 'iarf', 'iarh', 'iari', 'iarj', 'iarl', 'iarm', 'iarn', 'iaro', 'iarq', 'iasa', 'iash', 'iasj', 'iasw', 'iatb', 'iatd']
dihardii_invalid = ['DH_0002', 'DH_0004', 'DH_0008', 'DH_0009', 'DH_0011', 'DH_0013', 'DH_0015', 'DH_0015', 'DH_0016', 'DH_0018', 'DH_0019', 'DH_0021', 'DH_0021', 'DH_0022', 'DH_0023', 'DH_0024', 'DH_0024', 'DH_0025', 'DH_0026', 'DH_0027', 'DH_0028', 'DH_0029', 'DH_0032', 'DH_0032', 'DH_0033', 'DH_0034', 'DH_0034', 'DH_0035', 'DH_0036', 'DH_0036', 'DH_0037', 'DH_0038', 'DH_0038', 'DH_0039', 'DH_0040', 'DH_0041', 'DH_0042', 'DH_0042', 'DH_0043', 'DH_0044', 'DH_0044', 'DH_0045', 'DH_0046', 'DH_0046', 'DH_0047', 'DH_0048', 'DH_0048', 'DH_0049', 'DH_0052', 'DH_0053', 'DH_0054', 'DH_0056', 'DH_0057', 'DH_0059', 'DH_0060', 'DH_0062', 'DH_0064', 'DH_0066', 'DH_0066', 'DH_0067', 'DH_0068', 'DH_0070', 'DH_0072', 'DH_0073', 'DH_0073', 'DH_0074', 'DH_0074', 'DH_0075', 'DH_0076', 'DH_0077', 'DH_0077', 'DH_0078', 'DH_0079', 'DH_0080', 'DH_0081', 'DH_0081', 'DH_0082', 'DH_0082', 'DH_0083', 'DH_0083', 'DH_0084', 'DH_0085', 'DH_0086', 'DH_0087', 'DH_0088', 'DH_0093', 'DH_0095', 'DH_0097', 'DH_0098', 'DH_0099', 'DH_0100', 'DH_0102', 'DH_0103', 'DH_0104', 'DH_0105', 'DH_0107', 'DH_0107', 'DH_0108', 'DH_0109', 'DH_0109', 'DH_0110', 'DH_0110', 'DH_0111', 'DH_0112', 'DH_0112', 'DH_0113', 'DH_0113', 'DH_0114', 'DH_0114', 'DH_0115', 'DH_0116', 'DH_0116', 'DH_0117', 'DH_0118', 'DH_0119', 'DH_0119', 'DH_0120', 'DH_0121', 'DH_0121', 'DH_0122', 'DH_0123', 'DH_0123', 'DH_0124', 'DH_0126', 'DH_0127', 'DH_0127', 'DH_0128', 'DH_0129', 'DH_0130', 'DH_0132', 'DH_0133', 'DH_0134', 'DH_0135', 'DH_0137', 'DH_0138', 'DH_0139', 'DH_0140', 'DH_0142', 'DH_0143', 'DH_0144', 'DH_0145', 'DH_0147', 'DH_0149', 'DH_0150', 'DH_0151', 'DH_0152', 'DH_0153', 'DH_0154', 'DH_0154', 'DH_0155', 'DH_0155', 'DH_0156', 'DH_0156', 'DH_0158', 'DH_0159', 'DH_0159', 'DH_0161', 'DH_0161', 'DH_0162', 'DH_0162', 'DH_0163', 'DH_0163', 'DH_0164', 'DH_0164', 'DH_0165', 'DH_0165', 'DH_0166', 'DH_0166', 'DH_0167', 'DH_0167', 'DH_0168', 'DH_0168', 'DH_0170', 'DH_0171', 'DH_0171', 'DH_0172', 'DH_0173', 'DH_0174', 'DH_0177', 'DH_0179', 'DH_0180', 'DH_0181', 'DH_0181', 'DH_0182', 'DH_0182', 'DH_0183', 'DH_0183', 'DH_0184', 'DH_0185', 'DH_0186', 'DH_0187', 'DH_0187', 'DH_0188', 'DH_0188', 'DH_0189', 'DH_0190', 'DH_0191', 'DH_0191', 'DH_0192', 'DH_0192', 'DH_0193', 'DH_0194']
def get_args():
  parser = argparse.ArgumentParser(description = '')
  parser.add_argument('dataset', type = str, help = '')
  parser.add_argument('target_probability', type = float, help = '')
  parser.add_argument('folder', type = str, help = '')
  args = parser.parse_args()
  return args

def main():
  args = get_args()
  invalid = callhome_invalid if args.dataset == 'callhome' else dihardii_invalid
  folder_a = args.folder
  folder_b = folder_a[:-2] + '_b'

  ders = []
  eers = []
  dcfs = []
  ders_filtered = []
  eers_filtered = []
  dcfs_filtered = []
  for folder in [folder_a, folder_b]:
    filtered_folder = folder + '/filtered'
    os.makedirs(filtered_folder, exist_ok = True)
    # ------------------------- DER ------------------------- # 
    f = open(folder + '/groundtruth.rttm', 'r')
    lines = [line for line in f.readlines() if line.split()[1] not in invalid]
    f.close()
    f = open(filtered_folder + '/groundtruth.rttm', 'w')
    f.write(''.join(lines))
    f.close()
    f = open(folder + '/results.rttm', 'r')
    lines = [line for line in f.readlines() if line.split()[1] not in invalid]
    f.close()
    f = open(filtered_folder + '/results.rttm', 'w')
    f.write(''.join(lines))
    f.close()
    ders += [md_eval(folder + '/groundtruth.rttm', folder + '/results.rttm', folder)]
    ders_filtered += [md_eval(filtered_folder + '/groundtruth.rttm', filtered_folder + '/results.rttm', filtered_folder)]
    # ------------------------- EER, minDCF ------------------------- #
    f = open(folder + '/eer.scores', 'r')
    eer_scores = [line for line in f.readlines()]
    f.close()
    f = open(folder + '/dcf.scores', 'r')
    dcf_scores = [line for line in f.readlines()]
    f.close()
    f = open(folder + '/dcf.trials', 'r')
    dcf_trials = [line for line in f.readlines()]
    f.close()
    eer_scores_filtered = []
    dcf_scores_filtered = []
    dcf_trials_filtered = []
    for (eer_score, dcf_score, dcf_trial) in zip(eer_scores, dcf_scores, dcf_trials):
      file_id = dcf_trial.split('_')[0] if args.dataset == 'callhome' else dcf_trial[:7]
      if file_id not in invalid:
        eer_scores_filtered += [eer_score]
        dcf_scores_filtered += [dcf_score]
        dcf_trials_filtered += [dcf_trial]
    f = open(filtered_folder + '/eer.scores', 'w')
    f.write(''.join(eer_scores_filtered))
    f.close()
    f = open(filtered_folder + '/dcf.scores', 'w')
    f.write(''.join(dcf_scores_filtered))
    f.close()
    f = open(filtered_folder + '/dcf.trials', 'w')
    f.write(''.join(dcf_trials_filtered))
    f.close()
    eers += [compute_eer2(folder + '/eer.scores', folder)]
    eers_filtered += [compute_eer2(filtered_folder + '/eer.scores', filtered_folder)]
    dcfs += [compute_min_dcf(folder + '/dcf.scores', folder + '/dcf.trials', args.target_probability, folder)]
    dcfs_filtered += [compute_min_dcf(filtered_folder + '/dcf.scores', filtered_folder + '/dcf.trials', args.target_probability, filtered_folder)]

  print('original:', 'der', sum(ders) / 2, 'eer', sum(eers) / 2, 'minDCF', sum(dcfs) / 2, 'filtered:', 'der', sum(ders_filtered) / 2, 'eer', sum(eers_filtered) / 2, 'minDCF', sum(dcfs_filtered) / 2)

if __name__ == '__main__':
  main()

