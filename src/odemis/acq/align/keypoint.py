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

import numpy as np
import cv2
import math

BAR_LEN_FACTOR = 0.06
NUM_SELECTED_KP = 10

def FindTransform(ima, imb):
    """
    ima(DataArray of shape YaXa with int or float): the first image
    imb(DataArray of shape YbXb with int or float): the second image.
        Note that the shape doesn't have to be any relationship with the shape of the
        first dimension(doesn't even need to be the same ratio)
    return (ndarray of shape 3, 3): transformation matrix to align the second image on the
        first image. (bottom row is (0, 0, 1), and right column is translation)
    raises:
    ValueError: if no good transformation is found.
    """

    # Invert the image
    #ima = 255 - ima

    ima_height = ima.shape[0]
    # calculate the height of the bar
    barLen = int(ima_height * BAR_LEN_FACTOR)

    # remove the bar on both images
    ima = ima[:-barLen, :]
    imb = imb[:-barLen, :]

    # equalize histogram
    ima = cv2.equalizeHist(ima)
    imb = cv2.equalizeHist(imb)

    # blur (window size must be odd)
    # ima = cv2.GaussianBlur(ima, (41, 41), 10)

    # TODO resize?

    # With sift, not available on default OpenCV installation
    # sift = cv2.xfeatures2d.SIFT_create()
    # ima_kp = cv2.drawKeypoints(ima, kp)

    # Initiate ORB detector
    orb = cv2.ORB()

    # find and compute the descriptors with ORB
    ima_kp, ima_des = orb.detectAndCompute(ima, None)
    imb_kp, imb_des = orb.detectAndCompute(imb, None)

    # create BFMatcher object
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    # Match descriptors.
    matches = bf.match(ima_des, imb_des)
    # Sort them in the order of their distance.
    sorted_matches = sorted(matches, key = lambda x:x.distance)

    # get the best matches
    selected_matches = sorted_matches[:NUM_SELECTED_KP]

    # get keypoints for selected matches
    selected_ima_kp = [list(ima_kp[m.queryIdx].pt) for m in selected_matches]
    selected_imb_kp = [list(imb_kp[m.trainIdx].pt) for m in selected_matches]

    selected_ima_kp = np.array([selected_ima_kp])
    selected_imb_kp = np.array([selected_imb_kp])

    # testing detecting the matching points automatically
    mat, mask = cv2.findHomography(selected_ima_kp, selected_imb_kp, cv2.RANSAC)
    if mat is None:
        raise ValueError("The images does not match")

    return mat
