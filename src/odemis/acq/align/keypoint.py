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

    # instantiate the feature detector
    feature_detector = cv2.SIFT()

    # find and compute the descriptors
    ima_kp, ima_des = feature_detector.detectAndCompute(ima, None)
    imb_kp, imb_des = feature_detector.detectAndCompute(imb, None)

    FLANN_INDEX_KDTREE = 0
    index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
    search_params = dict(checks = 50)
    flann = cv2.FlannBasedMatcher(index_params, search_params)
    matches = flann.knnMatch(ima_des,imb_des,k=2)

    # store all the good matches as per Lowe's ratio test.
    selected_matches = []
    for m,n in matches:
        if m.distance < 0.7 * n.distance:
            selected_matches.append(m)

    # get keypoints for selected matches
    selected_ima_kp = [list(ima_kp[m.queryIdx].pt) for m in selected_matches]
    selected_imb_kp = [list(imb_kp[m.trainIdx].pt) for m in selected_matches]

    # ima_painted_kp = cv2.drawKeypoints(ima, ima_kp, None, color=(0,255,0), flags=0)
    # imb_painted_kp = cv2.drawKeypoints(imb, imb_kp, None, color=(0,255,0), flags=0)
    # imgs_folder = 'C:/Projetos/Delmic/iCLEM/images/'
    # cv2.imwrite(imgs_folder + 'ima_painted_kp.jpg', ima_painted_kp)
    # cv2.imwrite(imgs_folder + 'imb_painted_kp.jpg', imb_painted_kp)

    selected_ima_kp = np.array([selected_ima_kp])
    selected_imb_kp = np.array([selected_imb_kp])

    # testing detecting the matching points automatically
    mat, mask = cv2.findHomography(selected_ima_kp, selected_imb_kp, cv2.RANSAC)
    if mat is None:
        raise ValueError("The images does not match")

    return mat

def Preprocess(ima, imb):
    if ima.ndim > 2:
        ima = cv2.cvtColor(ima, cv2.COLOR_RGB2GRAY)

    if imb.ndim > 2:
        imb = cv2.cvtColor(imb, cv2.COLOR_RGB2GRAY)

    # invert on Y axis
    ima = cv2.flip(ima, 0)

    # Invert the image brightness
    ima = 255 - ima

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
    ima = cv2.GaussianBlur(ima, (41, 41), 10)
    imb = cv2.GaussianBlur(imb, (21, 21), 5)

    return ima, imb
