"""
Created on Jan 4, 2017

@author: kratenko
"""

import hashlib
import bz2


class PapupPayload:

    def __init__(self, redundancy=1, compression=0, encryption=0):
        self.padding = None
        self.data = None
        self.redundancy = redundancy
        self.compression = compression
        self.encryption = encryption

    def set_data(self, data):
        self.data = data
        self.raw_data_length = len(self.data)
        self.raw_data_sha1 = hashlib.sha1(self.data)

    def do_compression(self):
        if self.compression == 0:
            # no compression
            print("no compression")
            pass
        elif self.compression == 1:
            # bz2, 9
            print("bz2 compression")
            self.data = bz2.compress(self.data)
        else:
            raise ValueError(
                "Invalid compression method: {}".format(self.compression))

    def do_encryption(self):
        if self.encryption == 0:
            # no encryption
            pass
        else:
            raise ValueError(
                "Invalid encryption method: {}".format(self.encryption))
