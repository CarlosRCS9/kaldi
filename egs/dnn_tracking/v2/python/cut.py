#!/usr/bin/env python3
#
# Copyright 2020 Carlos Castillo
# Apache 2.0.

import numpy as np

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
        name       = words[7]
        conf       = words[8]
        slat       = wotds[9]
    def __str__(self):
        return ' '.join([self.type, self.file, self.chnl, str(self.tbeg), str(self.tdur), self.ortho, self.stype, self.name, self.conf, self.slat])

