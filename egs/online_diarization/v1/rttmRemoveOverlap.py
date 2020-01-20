#!/usr/bin/env python3

# Copyright 2019 Carlos Castillo
# Apache 2.0.

import numpy as np

class Segment:
  def __init__(self, rttm_line):
    rttm_line_data = rttm_line.split()
    self.type = rttm_line_data[0]
    self.recording_id = rttm_line_data[1]
    self.channel = rttm_line_data[2]
    self.begining = float(rttm_line_data[3])
    self.duration = float(rttm_line_data[4])
    self.ending = self.begining + self.duration #round
    self.ortho = rttm_line_data[5]
    self.stype = rttm_line_data[6]
    self.speaker_id = rttm_line_data[7]
    self.conf = rttm_line_data[8]
    self.slat = rttm_line_data[9]
  def __str__(self):
    return str(self.__class__) + ": " + str(self.__dict__)
  def overlap(self, begining, ending):
    return not (ending <= self.begining or self.ending <= begining)

class Speaker:
  def __init__(self, segment_complex, segment):
    self.speaker_id = segment.speaker_id
    self.begining = segment.begining if segment.begining > segment_complex.begining else segment_complex.begining
    self.ending = segment.ending if segment.ending < segment_complex.ending else segment_complex.ending
    self.duration = self.ending - self.begining #round
  def __str__(self):
    return str(self.__class__) + ": " + str(self.__dict__)
  def mix_speaker(self, speaker):
    if self.speaker_id != speaker.speaker_id:
      exit('speaker_ids doesnt match.')
    self.begining = self.begining if self.begining < speaker.begining else speaker.begining
    self.ending = self.ending if self.ending > speaker.ending else speaker.ending
    self.duration = self.ending - self.begining

class Segment_complex:
  def __init__(self, begining, ending, segment):
    self.type = segment.type
    self.recording_id = segment.recording_id
    self.channel = segment.channel
    self.begining = begining
    self.ending = ending
    self.duration = self.ending - self.begining #round
    self.ortho = segment.ortho
    self.stype = segment.stype
    self.speakers = [Speaker(self, segment)]
    self.conf = segment.conf
    self.slat = segment.slat
  def __str__(self):
    return str(self.__class__) + ": " + str(self.__dict__)
  def add_segment(self, segment):
    self.speakers.append(Speaker(self, segment))
  def same_speakers(self, segment_complex):
    self_speakers = [speaker.speaker_id for speaker in self.speakers]
    self_speakers.sort()
    target_speakers = [speaker.speaker_id for speaker in segment_complex.speakers]
    target_speakers.sort()
    return np.array_equal(self_speakers, target_speakers)
  def mix_segment_complex(self, segment_complex):
    self.begining = self.begining if self.begining < segment_complex.begining else segment_complex.begining
    self.ending = self.ending if self.ending > segment_complex.ending else segment_complex.ending
    self.duration = self.ending - self.begining #round
    self.speakers.sort(key = lambda speaker: speaker.speaker_id)
    segment_complex.speakers.sort(key = lambda speaker: speaker.speaker_id)
    for i in range(len(self.speakers)):
      self.speakers[i].mix_speaker(segment_complex.speakers[i])
  def print_rttm(self):
    print(' '.join([self.type, self.recording_id, self.channel, str(round(self.begining, 2)), str(round(self.duration, 2)), self.ortho, self.stype, self.speakers[0].speaker_id if len(self.speakers) == 1 else 'Z', self.conf, self.slat]))

def get_stdin():
  import sys
  return sys.stdin

def main():
  stdin = get_stdin()
  segments = [Segment(line) for line in stdin]
  recording_ids = []
  for segment in segments:
    if segment.recording_id not in recording_ids:
      recording_ids.append(segment.recording_id)
  # ----- Recording ----- #
  for recording_id in recording_ids:
    recording_segments = [segment for segment in segments if segment.recording_id == recording_id]
    times_beginings = [segment.begining for segment in recording_segments]
    times_endings = [segment.ending for segment in recording_segments]
    times = times_beginings + times_endings
    times = list(set(times))
    times.sort()
    segments_complex = []
    for i in range(len(times) - 1):
      time_segments = [segment for segment in recording_segments if segment.overlap(times[i], times[i + 1])]
      if len(time_segments) > 0:
        segment_complex = Segment_complex(times[i], times[i + 1], time_segments[0])
        for segment in time_segments[1:]:
          segment_complex.add_segment(segment)
        segments_complex.append(segment_complex)
    segments_complex_reduced = [segments_complex[0]]
    for i in range(len(segments_complex)):
      if (i != 0):
        if segments_complex_reduced[-1].ending == segments_complex[i].begining and segments_complex_reduced[-1].same_speakers(segments_complex[i]):
          segments_complex_reduced[-1].mix_segment_complex(segments_complex[i])
        else:
          segments_complex_reduced.append(segments_complex[i])

    for segment_complex in segments_complex_reduced:
      segment_complex.print_rttm()

if __name__ == '__main__':
  main()
