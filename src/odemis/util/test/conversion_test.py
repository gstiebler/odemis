#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 1 Jul 2013

@author: Éric Piel

Copyright © 2013 Éric Piel, Delmic

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
from __future__ import division

from odemis import model
from odemis.util import conversion
from odemis.util.conversion import \
    convert_to_object, \
    reproduce_typed_value, \
    get_img_transformation_matrix,\
    get_tile_md_pos, \
    get_img_transformation_md
import unittest
import math
import numpy


class TestConversion(unittest.TestCase):

    def test_wave2rgb(self):
        #         (input) (expected output)
        values = [(200.51513e-9, (255, 0, 255)),
                  (350e-9, (255, 0, 255)),
                  (490e-9, (0, 255, 255)),
                  (700e-9, (255, 0, 0)),
                  (900.5e-9, (255, 0, 0)),
                  ]
        for (i, eo) in values:
            o = conversion.wave2rgb(i)
            self.assertEquals(o, eo, u"%f nm -> %s should be %s" % (i * 1e9, o, eo))

    def test_convertToObject_good(self):
        """
        check various inputs and compare to expected output
        for values that should work
        """
        # example value / input str / expected output
        tc = [("-1561", -1561),
              ("0.123", 0.123),
              ("true", True),
              ("c: 6,d: 1.3", {"c": 6., "d":1.3}),
              ("-9, -8", [-9, -8]),
              (" 9, -8", [9, -8]),
              ("0, -8, -15.e-3, 6.", [0, -8, -15e-3, 6.0]),
              ("0.1", 0.1),
              ("[aa,bb]", ["aa", "bb"]),
              # TODO: more complicated but nice to support for the user
              # ("256 x 256 px", (256, 256)),
              # ("21 x 0.2 m", (21, 0.2)),
              ("", None),
              ("{5: }", {5: None}), # Should it fail?
              ("-1, 63, 12", [-1, 63, 12]), # NotifyingList becomes a list
              ("9.3, -8", [9.3, -8]),
              # Note: we don't support SI prefixes
              ("[aa, c a]", ["aa", "c a"]),
              ]

        for str_val, expo in tc:
            out = convert_to_object(str_val)
            self.assertEqual(out, expo,
                 "Testing with '%s' -> %s" % (str_val, out))

    def test_convertToObject_bad(self):
        """
        check various inputs and compare to expected output
        for values that should raise an exception
        """
        # example value / input str
        tc = [("{5:"),
              ("[5.3"),
              # ("5,6]"), # TODO
              ]

        for str_val in tc:
            with self.assertRaises((ValueError, TypeError)):
                out = convert_to_object(str_val)

    def test_reproduceTypedValue_good(self):
        """
        check various inputs and compare to expected output
        for values that should work
        """
        lva = model.ListVA([12, -3])
        # example value / input str / expected output
        tc = [(3, "-1561", -1561),
              (-9.3, "0.123", 0.123),
              (False, "true", True),
              ({"a": 12.5, "b": 3.}, "c:6,d:1.3", {"c": 6., "d":1.3}),
              ((-5, 0, 6), " 9, -8", (9, -8)),  # we don't force to be the same size
              ((1.2, 0.0), "0, -8, -15e-3, 6.", (0.0, -8.0, -15e-3, 6.0)),
              ([1.2, 0.0], "0.1", [0.1]),
              (("cou", "bafd"), "aa,bb", ("aa", "bb")),
              # more complicated but nice to support for the user
              ((1200, 256), "256 x 256 px", (256, 256)),
              ((1.2, 256), " 21 x 0.2 m", (21, 0.2)),
              ([-5, 0, 6], "9,, -8", [9, -8]),
              ((1.2, 0.0), "", tuple()),
              (lva.value, "-1, 63, 12", [-1, 63, 12]),  # NotifyingList becomes a list
              ((-5, 0, 6), "9.3, -8", (9, 3, -8)),  # maybe this shouldn't work?
              # Note: we don't support SI prefixes
              (("cou",), "aa, c a", ("aa", " c a")),  # TODO: need to see if spaces should be kept or trimmed
              ]

        for ex_val, str_val, expo in tc:
            out = reproduce_typed_value(ex_val, str_val)
            self.assertEqual(out, expo,
                 "Testing with %s / '%s' -> %s" % (ex_val, str_val, out))

    def test_reproduceTypedValue_bad(self):
        """
        check various inputs and compare to expected output
        for values that should raise an exception
        """
        # example value / input str
        tc = [(3, "-"),
              (-9, "0.123"),
              (False, "56"),
              ({"a": 12.5, "b": 3.}, "6,1.3"),
              (9.3, "0, 123"),
              ]

        for ex_val, str_val in tc:
            with self.assertRaises((ValueError, TypeError)):
                out = reproduce_typed_value(ex_val, str_val)

    def test_get_img_transformation_matrix(self):
        # simplest matrix
        md = {
            model.MD_PIXEL_SIZE: (1.0, 1.0),
            model.MD_ROTATION: 0.0,
            model.MD_SHEAR: 0.0,
        }
        mat = get_img_transformation_matrix(md)
        numpy.testing.assert_almost_equal(mat, [[1., 0.], [0., -1.]])

        micro = 1.0e-06
        # 90 degrees of rotation
        md = {
            model.MD_PIXEL_SIZE: (micro, micro),
            model.MD_ROTATION: math.pi / 2,
        }
        mat = get_img_transformation_matrix(md)
        numpy.testing.assert_almost_equal(mat, [[0.0, micro], [micro, 0.0]])

        # 180 degrees of rotation
        md = {
            model.MD_PIXEL_SIZE: (micro, micro),
            model.MD_ROTATION: math.pi,
        }
        mat = get_img_transformation_matrix(md)
        numpy.testing.assert_almost_equal(mat, [[-micro, 0.0], [0.0, micro]])

        # scale and rotation 45 degrees
        md = {
            model.MD_PIXEL_SIZE: (micro, micro),
            model.MD_ROTATION: math.pi / 4,
        }
        mat = get_img_transformation_matrix(md)
        sin = math.sin(math.pi / 4) * micro
        numpy.testing.assert_almost_equal(mat, [[sin, sin], [sin, -sin]])

        # scale and rotation 45 degrees
        md = {
            model.MD_PIXEL_SIZE: (micro, micro),
            model.MD_SHEAR: 0.5,
        }
        mat = get_img_transformation_matrix(md)
        numpy.testing.assert_almost_equal(mat, [[micro, 0.0], [-0.5 * micro, -micro]])

        # everything
        md = {
            model.MD_PIXEL_SIZE: (micro, micro),
            model.MD_ROTATION: math.pi / 4,
            model.MD_SHEAR: 0.1,
        }
        mat = get_img_transformation_matrix(md)
        numpy.testing.assert_almost_equal(mat, [[7.77817459e-07, sin], [6.36396103e-07, -sin]])

        # nothing
        md = {}
        with self.assertRaises(ValueError): # MD_PIXEL_SIZE must be present
            mat = get_img_transformation_matrix(md)

    def test_get_tile_md_pos(self):
        TILE_SIZE = 256
        BASE_MD_POS = (10e-6, 50e-6)

        tile_md = {
            model.MD_PIXEL_SIZE: (1e-6, 1e-6),
        }
        orig_md = {
            model.MD_ROTATION: 0.2,
            model.MD_SHEAR: 0.3,
            model.MD_POS: BASE_MD_POS,
            model.MD_PIXEL_SIZE: (1e-6, 1e-6)
        }
        tile = model.DataArray(numpy.zeros((TILE_SIZE, TILE_SIZE), numpy.uint8), tile_md)
        # image with the same size of the tile
        origda = model.DataArray(numpy.zeros((TILE_SIZE, TILE_SIZE), numpy.uint8), orig_md)
        # tile_md_pos should be the same as the full image, as there is only one tile
        tile_md_pos = get_tile_md_pos((0, 0), (TILE_SIZE, TILE_SIZE), tile, origda)
        self.assertEqual(tile_md_pos, BASE_MD_POS)

        # image with some tiles
        origda = model.DataArray(numpy.zeros((7 * TILE_SIZE, 11 * TILE_SIZE), numpy.uint8), orig_md)
        # tile_md_pos should be the same as the full image, as it is the center tile
        tile_md_pos = get_tile_md_pos((5, 3), (TILE_SIZE, TILE_SIZE), tile, origda)
        self.assertEqual(tile_md_pos, BASE_MD_POS)

        # image with some tiles
        origda = model.DataArray(numpy.zeros((6 * TILE_SIZE, 10 * TILE_SIZE), numpy.uint8), orig_md)
        tile_md_pos = get_tile_md_pos((5, 3), (TILE_SIZE, TILE_SIZE), tile, origda)
        numpy.testing.assert_almost_equal(tile_md_pos, [0.000168507098607, -8.76534042110e-05])

        # corner tile
        origda = model.DataArray(numpy.zeros((2000, 1000), numpy.uint8), orig_md)
        tile_md_pos = get_tile_md_pos((6, 5), (TILE_SIZE, TILE_SIZE), tile, origda)
        numpy.testing.assert_almost_equal(tile_md_pos, [0.0013012299138, -0.00046085531169])

        # 1 x 1 tile_size
        tile = model.DataArray(numpy.zeros((1, 1), numpy.uint8), tile_md)
        origda = model.DataArray(numpy.zeros((6 * TILE_SIZE, 10 * TILE_SIZE), numpy.uint8), orig_md)
        # it should be really close to BASE_MD_POS
        tile_md_pos = get_tile_md_pos((5, 3), (TILE_SIZE, TILE_SIZE), tile, origda)
        numpy.testing.assert_almost_equal(tile_md_pos, [1.06191683539e-05, 4.94622913898e-05])

        # 1 x 1 tile_size and tile.shape
        origda = model.DataArray(numpy.zeros((101, 201), numpy.uint8), orig_md)
        tile_md_pos = get_tile_md_pos((100, 50), (1, 1), tile, origda)
        self.assertEqual(tile_md_pos, BASE_MD_POS)

        # Second zoom level. The pixel size of the tile should be twice the value of the
        # pixel size of the image
        tile_md[model.MD_PIXEL_SIZE] = (2e-6, 2e-6)

        tile = model.DataArray(numpy.zeros((TILE_SIZE, TILE_SIZE), numpy.uint8), tile_md)
        # Zoomed image with the same size of the tile. The full image should be
        # twice the size of the image on the second zoom level
        origda = model.DataArray(numpy.zeros((TILE_SIZE * 2, TILE_SIZE * 2), numpy.uint8), orig_md)
        # tile_md_pos should be the same as the zoomed image, as there is only one tile
        tile_md_pos = get_tile_md_pos((0, 0), (TILE_SIZE, TILE_SIZE), tile, origda)
        self.assertEqual(tile_md_pos, BASE_MD_POS)

        # Third zoom level. The pixel size of the tile should be 4 times the value of the
        # pixel size of the image (2 ** 2)
        tile_md[model.MD_PIXEL_SIZE] = (4e-6, 4e-6)
        tile = model.DataArray(numpy.zeros((TILE_SIZE, TILE_SIZE), numpy.uint8), tile_md)
        # Zoomed image with 4 tiles. The only tile with TILE_SIZE X TILE_SIZE dimensions in
        # this image will be the top-left tile. The others will be smaller
        img_shape = (TILE_SIZE * 8 - 20, TILE_SIZE * 8 - 12)
        origda = model.DataArray(numpy.zeros(img_shape, numpy.uint8), orig_md)

        tile_md_pos = get_tile_md_pos((0, 0), (TILE_SIZE, TILE_SIZE), tile, origda)
        numpy.testing.assert_almost_equal(tile_md_pos, [-0.0006158036968, 0.00059024084721])
        tile_md_pos = get_tile_md_pos((0, 1), (TILE_SIZE, TILE_SIZE), tile, origda)
        numpy.testing.assert_almost_equal(tile_md_pos, [-0.00041236630212, -0.000413347328499])
        tile_md_pos = get_tile_md_pos((1, 1), (TILE_SIZE, TILE_SIZE), tile, origda)
        numpy.testing.assert_almost_equal(tile_md_pos, [0.00065225309200, -0.00051098638647])

    def test_get_img_transformation_md(self):
        tx = 1.1
        ty = 2.2
        rot = 0.35
        scale = (0.8, 0.9)
        shear = 0.2

        ps_mat = numpy.matrix([[scale[0], 0, 0], [0, scale[1], 0], [0, 0, 1]])
        rcos, rsin = math.cos(rot), math.sin(rot)
        rot_mat = numpy.matrix([[rcos, -rsin, 0], [rsin, rcos, 0], [0, 0, 1]])
        shear_mat = numpy.matrix([[1, 0, 0], [shear, 1, 0], [0, 0, 1]])
        tmat = rot_mat * shear_mat * ps_mat
        tmat[0, 2] = tx
        tmat[1, 2] = ty
        metadata = get_img_transformation_md(tmat)
        print metadata
        self.assertEqual((tx, ty), metadata[model.MD_POS])
        self.assertEqual(scale, metadata[model.MD_PIXEL_SIZE])
        self.assertEqual(rot, metadata[model.MD_ROTATION])
        self.assertEqual(shear, metadata[model.MD_SHEAR])


if __name__ == "__main__":
    unittest.main()


# vim:tabstop=4:shiftwidth=4:expandtab:spelllang=en_gb:spell:
