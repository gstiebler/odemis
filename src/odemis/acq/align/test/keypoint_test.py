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
from odemis.util.conversion import get_img_transformation_md
from odemis.util.dataio import open_acquisition
import numpy
import cairo
import math
from odemis import model
from numpy.linalg import inv
from scipy import ndimage

imgs_folder = 'C:/Projetos/Delmic/iCLEM/images/'


def preprocess(ima, flip, invert, crop, gaussian_sigma):
    '''
    invert(bool)
    gaussian_sigma: sigma for the gaussian processing
    '''
    metadata_a = ima.metadata
    if ima.ndim > 2:
        ima = cv2.cvtColor(ima, cv2.COLOR_RGB2GRAY)

    # invert on Y axis
    if flip:
        ima = ima[::-1, :]

    # Invert the image brightness
    if invert:
        ima = 255 - ima

    ima_height = ima.shape[0]

    crop_top, crop_bottom, crop_left, crop_right = crop
    # remove the bar
    ima = ima[crop_top:ima.shape[0] - crop_bottom, crop_left:ima.shape[1] - crop_right]

    # equalize histogram
    ima = cv2.equalizeHist(ima)

    # blur (kernel size must be odd)
    ima = ndimage.gaussian_filter(ima, sigma=gaussian_sigma)

    return  model.DataArray(ima, metadata_a)

class TestKeypoint(unittest.TestCase):

    def test_first(self):
        image_pairs = [
            (
                ('Slice69.tif', True, True, (0, 0, 0, 0), 5), 
                ('g_009_gray_cropped.tif', False, False, (0, 0, 0, 0), 2)
            ),
            (
                ('001_CBS_010.tif', False, False, (0, 0, 0, 0), 0), 
                ('20141014-113042_1.tif', False, False, (0, 0, 0, 0), 0)
            ),
            (
                ('t3 DELPHI.tiff', False, False, (0, 200, 0, 0), 3),
                ('t3 testoutA3.tif', False, False, (0, 420, 0, 0), 3)
            )
        ]
        image_pair = image_pairs[2]
        tem_img = open_acquisition(imgs_folder + image_pair[0][0])[0].getData()
        sem_img = open_acquisition(imgs_folder + image_pair[1][0])[0].getData()
        tem_img = preprocess(tem_img, image_pair[0][1], image_pair[0][2], image_pair[0][3], image_pair[0][4])
        sem_img = preprocess(sem_img, image_pair[1][1], image_pair[1][2], image_pair[1][3], image_pair[1][4])
        tmat, tem_kp, sem_kp = keypoint.FindTransformORB(tem_img, sem_img)

        tem_painted_kp = cv2.drawKeypoints(tem_img, tem_kp, None, color=(0,255,0), flags=0)
        sem_painted_kp = cv2.drawKeypoints(sem_img, sem_kp, None, color=(0,255,0), flags=0)
        cv2.imwrite(imgs_folder + 'tem_kp.jpg', tem_painted_kp)
        cv2.imwrite(imgs_folder + 'sem_kp.jpg', sem_painted_kp)

        warped_im = cv2.warpPerspective(tem_img, tmat, (sem_img.shape[1], sem_img.shape[0]))
        merged_im = cv2.addWeighted(sem_img, 0.5, warped_im, 0.5, 0.0)
        cv2.imwrite(imgs_folder + 'merged_with_warped.jpg', merged_im)
        print tmat
        print get_img_transformation_md(tmat, tem_img)

    def test_get_img_transformation_md(self):
        rot = 0.2
        scale_x = 0.9
        scale_y = 0.8
        shear = -0.15
        ps_mat = numpy.matrix([[scale_x, 0], [0, scale_y]])
        rcos, rsin = math.cos(rot), math.sin(rot)
        rot_mat = numpy.matrix([[rcos, -rsin], [rsin, rcos]])
        shear_mat = numpy.matrix([[1, 0], [-shear, 1]])
        tmat = rot_mat * shear_mat * ps_mat

        tmat33 = numpy.zeros((3, 3), dtype=numpy.float)
        tmat33[0:2, 0:2] = tmat
        transf_md = get_img_transformation_md(tmat33)
        self.assertAlmostEqual(rot, transf_md[model.MD_ROTATION])
        self.assertEqual((scale_x, scale_y), transf_md[model.MD_PIXEL_SIZE])
        self.assertAlmostEqual(shear, transf_md[model.MD_SHEAR])

    def test_synthetic_images(self):
        image = numpy.zeros((1000, 1000, 4), dtype=numpy.uint8)
        surface = cairo.ImageSurface.create_for_data(image, cairo.FORMAT_ARGB32, 1000, 1000)
        cr = cairo.Context(surface)
        cr.set_source_rgb(1.0, 1.0, 1.0)
        cr.paint()

        cr.set_source_rgb(0.0, 0.0, 0.0)

        # draw circles
        cr.arc(200, 150, 80, 0, 2*math.pi)
        cr.fill()

        cr.arc(400, 150, 70, 0, 2*math.pi)
        cr.fill()

        cr.arc(700, 180, 50, 0, 2*math.pi)
        cr.fill()

        cr.arc(200, 500, 80, 0, 2*math.pi)
        cr.fill()

        cr.arc(400, 600, 70, 0, 2*math.pi)
        cr.fill()

        cr.arc(600, 500, 50, 0, 2*math.pi)
        cr.fill()

        cr.arc(600, 500, 50, 0, 2*math.pi)
        cr.fill()

        cr.arc(500, 500, 350, 0, 2*math.pi)
        cr.set_line_width(5)
        cr.stroke()

        cr.arc(600, 500, 50, 0, 2*math.pi)
        cr.fill()

        # rectangle
        cr.rectangle(600, 700, 200, 100)
        cr.fill()

        angle = 0.3
        scale = 0.7
        translation_x = 150.0
        translation_y = 160.0
        print 'cos', math.cos(angle)
        print 'sin', math.sin(angle)
        rot_mat = cv2.getRotationMatrix2D((500.0, 500.0), math.degrees(angle), scale)
        print 'rot_mat'
        print rot_mat
        rot_mat[0, 2] += translation_x
        rot_mat[1, 2] += translation_y
        rotated = cv2.warpAffine(image, rot_mat, (1000, 1000),\
                borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))

        tmat_odemis = keypoint.FindTransform(rotated, image)
        warped_im = cv2.warpPerspective(rotated, tmat_odemis, (rotated.shape[1], rotated.shape[0]),\
                borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))

        print 'tmat_odemis'
        print tmat_odemis
        transf_md = get_img_transformation_md(tmat_odemis, image)
        print transf_md

        cv2.imwrite(imgs_folder + 'test.jpg', image)
        cv2.imwrite(imgs_folder + 'rotated.jpg', rotated)
        cv2.imwrite(imgs_folder + 'rotated_opencv.jpg', warped_im)


if __name__ == '__main__':
    unittest.main()