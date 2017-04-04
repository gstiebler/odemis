#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 04 Mar 2017

@author: Guilherme Stiebler

Copyright © 2017 Guilherme Stiebler, Éric Piel, Delmic

This file is part of Odemis.

Odemis is free software: you can redistribute it and/or modify it under the terms
of the GNU General Public License version 2 as published by the Free Software
Foundation.

Odemis is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
Odemis. If not, see http://www.gnu.org/licenses/.
'''

import unittest
import logging
from odemis.acq.align import keypoint

import cv2


class TestKeypoint(unittest.TestCase):

    def test_first(self):
        imgs_folder = '/home/gstiebler/Projetos/Delmic/iCLEM/Images/'
        ima = cv2.imread(imgs_folder + '001_CBS_010.jpg', 0)
        imb = cv2.imread(imgs_folder + '20141014-113042_1.jpg', 0)
        mat = keypoint.FindTransform(ima, imb)
        print mat


if __name__ == '__main__':
    unittest.main()
