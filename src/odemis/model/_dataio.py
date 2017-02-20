#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 24 Jan 2017

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
from abc import ABCMeta, abstractmethod


class DataArrayShadow(object):
    """
    This class contains information about a DataArray.
    It has all the useful attributes of a DataArray, but not the actual data.
    """
    __metaclass__ = ABCMeta

    def __init__(self, shape, dtype, metadata=None, maxzoom=None):
        """
        Constructor
        shape (tuple of int): The shape of the corresponding DataArray
        dtype (numpy.dtype): The data type
        metadata (dict str->val): The metadata
        maxzoom (0<=int): the maximum zoom level possible. If the data isn't
            encoded in pyramidal format, the attribute is not present.
            The shape of the images in each zoom level is as following:
            (shape of full image) // (2**z)
            where z is the index of the zoom level
        """
        self.shape = shape
        self.ndim = len(shape)
        self.dtype = dtype
        self.metadata = metadata if metadata else {}
        if maxzoom is not None:
            self.maxzoom = maxzoom

    @abstractmethod
    def getData(self, n):
        """
        Fetches the whole data (at full resolution) of image at index n.
        n (0<=int): index of the image
        return DataArray: the data, with its metadata (ie, identical to .content[n] but
            with the actual data)
        """
        pass

    @abstractmethod
    def getTile(self, x, y, zoom):
        '''
        Fetches one tile
        x (0<=int): X index of the tile.
        y (0<=int): Y index of the tile
        zoom (0<=int): zoom level to use. The total shape of the image is shape / 2**zoom.
            The number of tiles available in an image is ceil((shape//zoom)/tile_shape)
        return (DataArray): the shape of the DataArray is typically of shape
        '''
        pass


class AcquisitionData(object):
    """
    It's an abstract class to represent an opened file. It allows
    to have random access to a sub-part of any image in the file. It's extended by
    each dataio converter to actually support the specific file format.
    """
    __metaclass__ = ABCMeta

    def __init__(self, content, thumbnails=None):
        self.content = content
        self.thumbnails = thumbnails if thumbnails else ()
