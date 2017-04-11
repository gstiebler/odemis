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
import math
from odemis import model

imgs_folder = 'C:/Projetos/Delmic/iCLEM/images/'

class TestKeypoint(unittest.TestCase):

    def test_first(self):
        # ima = cv2.imread(imgs_folder + '20141014-113042_1.jpg', 0)
        # imb = cv2.imread(imgs_folder + '001_CBS_010.jpg', 0)
        ima = open_acquisition(imgs_folder + 'Slice69.tif')[0].getData()
        imb = open_acquisition(imgs_folder + 'g_009.tif')[0].getData()
        ima, imb = keypoint.Preprocess(ima, imb)
        tmat = keypoint.FindTransform(ima, imb)
        warped_im = cv2.warpPerspective(ima, tmat, (imb.shape[1], imb.shape[0]))
        merged_im = cv2.addWeighted(imb, 0.5, warped_im, 0.5, 0.0)
        cv2.imwrite(imgs_folder + 'warped.jpg', merged_im)

        print tmat
        print get_img_transformation_md(tmat)

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
        image = numpy.ones((1000, 1000), dtype=numpy.uint8)
        # draw a triangle
        for i in range(0, 200):
            image[(i + 200), (200 - i * 0.7):(200 + i * 1.0)] = 255
        # draw a rectangle
        # image[500:700, 400:800] = 255

        # draw a trapezoid
        for i in range(0, 200):
            image[(i + 500), (400 - i * 0.2):(800 + i * 0.1)] = 255

        angle = 0.2
        print 'cos', math.cos(angle)
        print 'sin', math.sin(angle)
        rot_mat = cv2.getRotationMatrix2D((500, 500), math.degrees(angle), 1.0)
        print 'rot mat', rot_mat
        # rot_mat[0, 2] = 0.0
        # rot_mat[1, 2] = 0.0
        rotated = cv2.warpAffine(image, rot_mat, (1000, 1000))

        tmat_odemis = keypoint.FindTransform(rotated, image)
        warped_im = cv2.warpPerspective(rotated, tmat_odemis, (rotated.shape[1], rotated.shape[0]))

        print tmat_odemis
        transf_md = get_img_transformation_md(tmat_odemis)
        print transf_md

        cv2.imwrite(imgs_folder + 'test.jpg', image)
        cv2.imwrite(imgs_folder + 'rotated.jpg', rotated)
        cv2.imwrite(imgs_folder + 'rotated_opencv.jpg', warped_im)


if __name__ == '__main__':
    unittest.main()