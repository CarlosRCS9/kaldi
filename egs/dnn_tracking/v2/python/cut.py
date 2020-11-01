#!/usr/bin/env python3
#
# Copyright 2020 Carlos Castillo
# Apache 2.0.

import numpy as np
import itertools

class Rttm:
    def __init__(self, string):
        words = string.strip().split()
        self.type  = words[0]
        self.file  = words[1]
        self.chnl  = words[2]
        self.tbeg  = np.float32(words[3])
        self.tdur  = np.float32(words[4])
        self.ortho = words[5]
        self.stype = words[6]
        self.name  = words[7]
        self.conf  = words[8]
        self.slat  = words[9]
    # Object types: There are four general object categories represented. They are STT objects, MDE objects, source (speaker) objects, and structural objects. Each of these general categories may be represented by one or more types and subtypes.
    def get_type(self):
        return self.type
    # File name: The waveform file base name (i.e., without path names or extensions). 
    def get_file(self):
        return self.file
    # Channel ID The waveform channel (e.g., “1” or “2”).
    def get_chnl(self):
        return self.chnl
    # Beginning time: The beginning time of the object, in seconds, measured from the start time of the file. If there is no beginning time, use tbeg = ”<NA>”.
    def get_tbeg(self):
        return self.tbeg
    # Duration: The duration of the object, in seconds If there is no duration, use tdur = “<NA>”.
    def get_tdur(self):
        return self.tdur
    # Othography field: The orthographic rendering (spelling) of the object for STT object types. If there is no orthographic representation, use ortho = “<NA>”.
    def get_ortho(self):
        return self.ortho
    # Object subtypes: There are four general object categories represented. They are STT objects, MDE objects, source (speaker) objects, and structural objects. Each of these general categories may be represented by one or more types and subtypes.
    def get_stype(self):
        return self.stype
    # Speaker Name field: The name of the speaker. name must uniquely specify the speaker within the scope of the file. If name is not applicable or if no claim is being made as to the identity of the speaker, use name = “<NA>”.
    def get_name(self):
        return self.name
    #  Confidence Score: The confidence (probability) that the object information is correct. If conf is not available, use conf = “<NA>”. 
    def get_conf(self):
        return self.conf
    # Signal Look Ahead Time: The “Signal Look Ahead Time” is the time of the last signal sample (either an image frame or audio sample) used in determining the values within the RTTM Object’s fields. If the algorithm does not compute this statistic, slat = “<NA>”.
    def get_slat(self):
        return self.slat
    def __str__(self):
        return ' '.join([self.type, self.file, self.chnl, str(self.tbeg), str(self.tdur), self.ortho, self.stype, self.name, self.conf, self.slat])

class Speaker:
    def __init__(self, data):
        if isinstance(data, Rttm):
            rttm = data
            self.ortho = rttm.get_ortho()
            self.name  = rttm.get_name()
            self.conf  = rttm.get_conf()
        elif isinstance(data, Speaker):
            speaker = data
            self.ortho = speaker.get_ortho()
            self.name  = speaker.get_name()
            self.conf  = speaker.get_conf()
    def get_ortho(self):
        return self.ortho
    def get_name(self):
        return self.name
    def get_conf(self):
        return self.conf

class Channel:
    def __init__(self, data):
        if isinstance(data, Rttm):
            rttm = data
            self.type          = rttm.get_type()
            self.recording_id  = rttm.get_file()
            self.channel_id    = rttm.get_chnl()
            self.begin_time    = rttm.get_tbeg()
            self.duration_time = rttm.get_tdur()
            self.stype         = rttm.get_stype()
            self.slat          = rttm.get_slat()
            self.speakers      = {}
            self.speakers[rttm.get_name()] = Speaker(rttm)
        elif isinstance(data, Channel):
            channel = data
            self.type          = channel.get_type()
            self.recording_id  = channel.get_recording_id()
            self.channel_id    = channel.get_channel_id()
            self.begin_time    = channel.get_begin_time()
            self.duration_time = channel.get_duration_time()
            self.stype         = channel.get_stype()
            self.slat          = channel.get_slat()
            self.speakers      = {}
            for speaker_name, speaker in channel.get_speakers().items():
                self.speakers[speaker_name] = Speaker(speaker)
    def get_type(self):
        return self.type
    def get_recording_id(self):
        return self.recording_id
    def get_channel_id(self):
        return self.channel_id
    def get_begin_time(self):
        return self.begin_time
    def set_begin_time(self, begin_time):
        self.begin_time = begin_time
    def limit_begin_time(self, begin_time):
        if self.get_begin_time() < begin_time:
            self.set_begin_time(begin_time)
    def get_duration_time(self):
        return self.duration_time
    def set_duration_time(self, duration_time):
        self.duration_time = duration_time
    def get_end_time(self):
        return self.get_begin_time() + self.get_duration_time()
    def set_end_time(self, end_time):
        self.set_duration_time(end_time - self.get_begin_time())
    def limit_end_time(self, end_time):
        if self.get_end_time() > end_time:
            self.set_end_time(end_time)
    def get_stype(self):
        return self.stype
    def get_slat(self):
        return self.slat
    def get_speakers(self):
        return self.speakers

class Cut:
    def __init__(self, data):
        if isinstance(data, Rttm):
            rttm = data
            self.recording_id  = rttm.get_file()
            self.begin_time    = rttm.get_tbeg()
            self.duration_time = rttm.get_tdur()
            self.channels      = {}
            self.channels[rttm.get_chnl()] = Channel(rttm)
        elif isinstance(data, Cut):
            cut = data
            self.recording_id  = cut.get_recording_id()
            self.begin_time    = cut.get_begin_time()
            self.duration_time = cut.get_duration_time()
            self.channels      = {}
            for channel_id, channel in cut.get_channels().items():
                self.channels[channel_id] = Channel(channel)
    def get_recording_id(self):
        return self.recording_id
    def get_begin_time(self):
        return self.begin_time
    def set_begin_time(self, begin_time):
        self.begin_time = begin_time
    def limit_begin_time(self, begin_time):
        if self.get_begin_time() < begin_time:
            self.set_begin_time(begin_time)
        for channel in self.get_channels().values():
            channel.limit_begin_time(begin_time) 
    def get_duration_time(self):
        return self.duration_time
    def set_duration_time(self, duration_time):
        self.duration_time = duration_time
    def get_end_time(self):
        return self.get_begin_time() + self.get_duration_time()
    def set_end_time(self, end_time):
        self.set_duration_time(end_time - self.get_begin_time())
    def limit_end_time(self, end_time):
        if self.get_end_time() > end_time:
            self.set_end_time(end_time)
        for channel in self.get_channels().values():
            channel.limit_end_time(end_time)
    def limit_begin_end_time(self, begin_time, end_time):
        self.limit_begin_time(begin_time)
        self.limit_end_time(end_time)
    def get_channels(self):
        return self.channels
    def is_out_of_timestamps(self, begin_time, end_time):
        return end_time <= self.get_begin_time() or self.get_end_time() <= begin_time
    def get_rttm_string(self):
        output = ''
        for channel_id, channel in self.get_channels().items():
            for speaker_id, speaker in channel.get_speakers().items():
                output += channel.get_type() + ' ' + self.get_recording_id() + ' ' + channel_id + ' ' \
                        + str(self.get_begin_time()) + ' ' + str(self.get_duration_time()) + ' ' + speaker.get_ortho() + ' ' \
                        + channel.get_stype() + ' ' + speaker_id + ' ' + speaker.get_conf() + ' ' + channel.get_slat() + '\n'
        return output

class Recording:
    def __init__(self, recording_id):
        self.recording_id = recording_id
        self.cuts = []
    def get_recording_id(self):
        return self.recording_id
    def get_cuts(self):
        return self.cuts
    def append_cut(self, cut):
        return self.get_cuts().append(cut)
    def explicit_overlap(self):
        timestamps = sorted(set(itertools.chain(*[[cut.get_begin_time(), cut.get_end_time()] for cut in self.get_cuts()])))
        timestamps_pairs = [(timestamps[index], timestamps[index + 1]) for index, _ in enumerate(timestamps[:-1])]
        for begin_time, end_time in timestamps_pairs:
            timestamps_cuts = [cut for cut in self.get_cuts() if not cut.is_out_of_timestamps(begin_time, end_time)]
            if len(timestamps_cuts) > 0:
                print('begin_time', begin_time, 'end_time', end_time)
                print(len(timestamps_cuts))

def cuts_to_recordings(cuts, array = True):
    output = {}
    for cut in cuts:
        recording_id = cut.get_recording_id()
        if recording_id not in output:
            output[recording_id] = Recording(recording_id)
        output[recording_id].append_cut(cut)
    return list(output.values()) if array == True else output

