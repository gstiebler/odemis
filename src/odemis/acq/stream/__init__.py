# -*- coding: utf-8 -*-
"""
Created on 25 Jun 2014

@author: Rinze de Laat

Copyright © 2013-2015 Rinze de Laat, Éric Piel, Delmic

This file is part of Odemis.

Odemis is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License version 2 as published by the Free Software Foundation.

Odemis is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even
the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
Public License for more details.

You should have received a copy of the GNU General Public License along with Odemis. If not,
see http://www.gnu.org/licenses/.

"""


# This module contains classes that describe Streams, which are basically
# Detector, Emitter and Dataflow associations.


from __future__ import division

from ._base import *
from ._helper import *
from ._live import *
from ._static import *
from ._sync import *

from abc import ABCMeta
import threading


# Generic cross-cut types
class OpticalStream:
    __metaclass__ = ABCMeta

OpticalStream.register(CameraStream)
OpticalStream.register(StaticFluoStream)
OpticalStream.register(StaticBrightfieldStream)


class EMStream:
    """All the stream types related to electron microscope"""
    __metaclass__ = ABCMeta

EMStream.register(SEMStream)
EMStream.register(SpotSEMStream)
EMStream.register(StaticSEMStream)


class CLStream:
    """
    All the stream types related to cathodoluminescence with one C dimension
    (otherwise, it's a SpectrumStream)
    """
    __metaclass__ = ABCMeta

CLStream.register(CLSettingsStream)
CLStream.register(StaticCLStream)
# TODO, also include MonochromatorSettingsStream and SEMMDStream?


class SpectrumStream:
    __metaclass__ = ABCMeta

SpectrumStream.register(SpectrumSettingsStream)
SpectrumStream.register(StaticSpectrumStream)
SpectrumStream.register(SEMSpectrumMDStream)


class ARStream:
    __metaclass__ = ABCMeta

ARStream.register(ARSettingsStream)
ARStream.register(StaticARStream)
ARStream.register(SEMARMDStream)


# TODO: make it like a VA, so that it's possible to know when it changes
class StreamTree(object):
    """ Object which contains a set of streams, and how they are merged to
    appear as one image. It's a tree which has one stream per leaf and one merge
    operation per node. => recursive structure (= A tree is just a node with
    a merge method and a list of subnodes, either streamtree as well, or stream)
    """

    def __init__(self, operator=None, streams=None, **kwargs):
        """
        :param operator: (callable) a function that takes a list of
            RGB DataArrays in the same order as the streams are given and the
            additional arguments and returns one DataArray.
            By default operator is an average function.
        :param streams: (list of Streams or StreamTree): a list of streams, or
            StreamTrees.
            If a StreamTree is provided, its outlook is first computed and then
            passed as an RGB DataArray.
        :param kwargs: any argument to be given to the operator function
        """
        self.operator = operator or img.Average

        streams = streams or []
        assert(isinstance(streams, list))

        self.streams = []
        self.flat = model.ListVA([], readonly=True)
        self.should_update = model.BooleanVA(False)
        self.size = model.IntVA(0)
        self.kwargs = kwargs

        for s in streams:
            self.add_stream(s)

    def __str__(self):
        return "[" + ", ".join(str(s) for s in self.streams) + "]"

    def __len__(self):
        acc = 0

        for s in self.streams:
            if isinstance(s, Stream):
                acc += 1
            elif isinstance(s, StreamTree):
                acc += len(s)

        return acc

    def __getitem__(self, index):
        """ Return the Stream of StreamTree using index reference val[i] """
        return self.streams[index]

    def __contains__(self, the_stream):
        for stream in self.streams:
            if isinstance(the_stream, StreamTree) and the_stream in stream:
                return True
            elif stream == the_stream:
                return True
        return False

    def add_stream(self, stream):
        if isinstance(stream, (Stream, StreamTree, RGBSpatialProjection)):
            self.streams.append(stream)
            self.size.value = len(self.streams)
            if hasattr(stream, 'should_update'):
                stream.should_update.subscribe(self.on_stream_update_changed, init=True)
        else:
            msg = "Illegal type %s found in add_stream!" % type(stream)
            raise ValueError(msg)
        # Also update the flat streams list
        curr_streams = self.getStreams()
        self.flat._value = curr_streams
        self.flat.notify(curr_streams)

    def remove_stream(self, stream):
        if hasattr(stream, 'should_update'):
            stream.should_update.unsubscribe(self.on_stream_update_changed)
        self.streams.remove(stream)
        self.size.value = len(self.streams)
        self.on_stream_update_changed()
        # Also update the flat streams list
        curr_streams = self.getStreams()
        self.flat._value = curr_streams
        self.flat.notify(curr_streams)

    def on_stream_update_changed(self, _=None):
        """ Set the 'should_update' attribute when a streams' should_update VA changes """
        # At least one stream is live, so we 'should update'
        for s in self.streams:
            if hasattr(s, "should_update") and s.should_update.value:
                self.should_update.value = True
                break
        else:
            self.should_update.value = False

    def getStreams(self):
        """ Return the list of streams used to compose the picture """

        streams = []

        for s in self.streams:
            if isinstance(s, (Stream, RGBSpatialProjection)) and s not in streams:
                streams.append(s)
            elif isinstance(s, StreamTree):
                sub_streams = s.getStreams()
                for sub_s in sub_streams:
                    if sub_s not in streams:
                        streams.append(sub_s)

        return streams

#     def getImage(self, rect, mpp):
#         """
#         Returns an image composed of all the current stream images.
#         Precisely, it returns the output of a call to operator.
#         rect (2-tuple of 2-tuple of float): top-left and bottom-right points in
#           world position (m) of the area to draw
#         mpp (0<float): density (meter/pixel) of the image to compute
#         """
#         # TODO: probably not so useful function, need to see what canvas
#         #  it will likely need as argument a wx.Bitmap, and view rectangle
#         #  that will define where to save the result
#
#         # TODO: cache with the given rect and mpp and last update time of each
#         # image
#
#         # create the arguments list for operator
#         images = []
#         for s in self.streams:
#             if isinstance(s, Stream):
#                 images.append(s.image.value)
#             elif isinstance(s, StreamTree):
#                 images.append(s.getImage(rect, mpp))
#
#         return self.operator(images, rect, mpp, **self.kwargs)

    def getImages(self):
        """
        return a list of all the .image (which are not None) and the source stream
        return (list of (image, stream)): A list with a tuple of (image, stream)
        """
        images = []
        for s in self.streams:
            if isinstance(s, StreamTree):
                images.extend(s.getImages())
            elif isinstance(s, Stream):
                if hasattr(s, "image"):
                    im = s.image.value
                    if im is not None:
                        images.append((im, s))

        return images

    def get_streams_by_type(self, stream_types):
        """ Return a flat list of streams of `stream_type` within the StreamTree """

        streams = []

        for s in self.streams:
            if isinstance(s, StreamTree):
                streams.extend(s.get_streams_by_type(stream_types))
            elif isinstance(s, stream_types):
                streams.append(s)

        return streams


class DataProjection(object):

    def __init__(self, stream):
        '''
        stream (Stream): the Stream to project
        '''
        self.stream = stream

        # TODO: We need to reorganise everything so that the
        # image display is done via a dataflow (in a separate thread), instead
        # of a VA.
        self._im_needs_recompute = threading.Event()
        self._imthread = threading.Thread(target=self._image_thread,
                                          args=(weakref.ref(self),),
                                          name="Image computation")
        self._imthread.daemon = True
        self._imthread.start()

        # DataArray or None: RGB projection of the raw data
        self.image = model.VigilantAttribute(None)

    @staticmethod
    def _image_thread(wstream):
        """ Called as a separate thread, and recomputes the image whenever it receives an event
        asking for it.

        Args:
            wstream (Weakref to a Stream): the stream to follow

        """
        pass


class RGBSpatialProjection(DataProjection):

    def __init__(self, stream):
        '''
        stream (Stream): the Stream to project
        '''
        super(RGBSpatialProjection, self).__init__(stream)

        self.should_update = model.BooleanVA(False)
        self.name = stream.name
        self.image = model.VigilantAttribute(None)
        #self.image.subscribe(self._onImageUpdated)

        # self.stream.image.subscribe(self._onStreamImageUpdated)
        # Don't call at init, so don't set metadata if default value
        self.stream.tint.subscribe(self.needImageUpdate)
        self.stream.intensityRange.subscribe(self.needImageUpdate)
        self.stream.auto_bc.subscribe(self.needImageUpdate)
        self.stream.auto_bc_outliers.subscribe(self.needImageUpdate)

        # TODO: We need to reorganise everything so that the
        # image display is done via a dataflow (in a separate thread), instead
        # of a VA.
        self._im_needs_recompute = threading.Event()
        weak = weakref.ref(self)
        self._imthread = threading.Thread(target=self._image_thread,
                                          args=(weak,),
                                          name="Image computation")
        self._imthread.daemon = True
        self._imthread.start()
        if isinstance(stream.raw, tuple):
            raw = stream._das
            md = raw.metadata
            # TODO The code below is copied from StaticStream. Someday StaticStream will
            # not have this code anymore

            # get the pixel size of the full image
            ps = md[model.MD_PIXEL_SIZE]
            max_mpp = ps[0] * (2 ** raw.maxzoom)
            # sets the mpp as the X axis of the pixel size of the full image
            mpp_rng = (ps[0], max_mpp)
            self.mpp = model.FloatContinuous(max_mpp, mpp_rng, setter=self._set_mpp)

            full_rect = img._getBoundingBox(raw)
            l, t, r, b = full_rect
            rect_range = ((l, b, l, b), (r, t, r, t))
            self.rect = model.TupleContinuous(full_rect, rect_range)

            self.mpp.subscribe(self._onMpp)
            self.rect.subscribe(self._onRect)

            # initialize the projected tiles cache
            self._projectedTilesCache = {}
            # initialize the raw tiles cache
            self._rawTilesCache = {}

            # When True, the projected tiles cache should be invalidated
            self._projectedTilesInvalid = True

    #def _onStreamImageUpdated(self, image):
    #    self.image.value = image

    #def _onImageUpdated(self, image):
    #    self.stream.image.value = image

    def needImageUpdate(self, param):
        self._projectedTilesInvalid = True
        self._shouldUpdateImage()

    def _onMpp(self, mpp):
        self.stream.mpp.value = mpp

    def _onRect(self, rect):
        self.stream.rect.value = rect

    def _set_mpp(self, mpp):
        ps0 = self.mpp.range[0]
        exp = math.log(mpp / ps0, 2)
        exp = round(exp)
        return ps0 * 2 ** exp

    def onTint(self, value):
        if isinstance(self.raw, list):
            if len(self.stream.raw) > 0:
                raw = self.stream.raw[0]
            else:
                raw = None
        elif isinstance(self.stream.raw, tuple):
            raw = self.stream._das
        else:
            raise AttributeError(".raw must be a list of DA/DAS or a tuple of tuple of DA")

        if raw is not None:
            # If the image is pyramidal, the exported image is based on tiles from .raw.
            # And the metadata from raw will be used to generate the metadata of the merged
            # image from the tiles. So, in the end, the exported image metadata will be based
            # on the raw metadata
            raw.metadata[model.MD_USER_TINT] = value

        self._shouldUpdateImage()

    def _projectXY2RGB(self, data, tint=(255, 255, 255)):
        """
        Project a 2D spatial DataArray into a RGB representation
        data (DataArray): 2D DataArray
        tint ((int, int, int)): colouration of the image, in RGB.
        return (DataArray): 3D DataArray
        """
        # TODO replace by local irange
        irange = self.stream._getDisplayIRange()
        rgbim = img.DataArray2RGB(data, irange, tint)
        rgbim.flags.writeable = False
        # Commented to prevent log flooding
        # if model.MD_ACQ_DATE in data.metadata:
        #     logging.debug("Computed RGB projection %g s after acquisition",
        #                    time.time() - data.metadata[model.MD_ACQ_DATE])
        md = self.stream._find_metadata(data.metadata)
        md[model.MD_DIMS] = "YXC" # RGB format
        return model.DataArray(rgbim, md)

    def _shouldUpdateImage(self):
        """
        Ensures that the image VA will be updated in the "near future".
        """
        # If the previous request is still being processed, the event
        # synchronization allows to delay it (without accumulation).
        self._im_needs_recompute.set()

    def getBoundingBox(self):
        return self.stream.getBoundingBox()

    @staticmethod
    def _image_thread(wprojection):
        """ Called as a separate thread, and recomputes the image whenever it receives an event
        asking for it.

        Args:
            wstream (Weakref to a Stream): the stream to follow

        """

        try:
            projection = wprojection()
            stream = projection.stream
            name = stream.name.value
            im_needs_recompute = projection._im_needs_recompute
            # Only hold a weakref to allow the stream to be garbage collected
            # On GC, trigger im_needs_recompute so that the thread can end too
            wprojection = weakref.ref(projection, lambda o: im_needs_recompute.set())

            tnext = 0
            while True:
                # del projection
                im_needs_recompute.wait()  # wait until a new image is available
                projection = wprojection()
                stream = projection.stream

                if projection is None:
                    logging.debug("Projection %s disappeared so ending image update thread", name)
                    break

                tnow = time.time()

                # sleep a bit to avoid refreshing too fast
                tsleep = tnext - tnow
                if tsleep > 0.0001:
                    time.sleep(tsleep)

                tnext = time.time() + 0.1  # max 10 Hz
                im_needs_recompute.clear()
                projection._updateImage()
        except Exception:
            logging.exception("image update thread failed")

        gc.collect()

    def _zFromMpp(self):
        """
        Return the zoom level based on the current .mpp value
        return (int): The zoom level based on the current .mpp value
        """
        md = self.stream._das.metadata
        ps = md[model.MD_PIXEL_SIZE]
        return int(math.log(self.mpp.value / ps[0], 2))

    def _rectWorldToPixel(self, rect):
        """
        Convert rect from world coordinates to pixel coordinates
        rect (tuple containing x1, y1, x2, y2): Rect on world coordinates
        return (tuple containing x1, y1, x2, y2): Rect on pixel coordinates
        """
        md = self.stream._das.metadata
        ps = md.get(model.MD_PIXEL_SIZE, (1e-6, 1e-6))
        pos = md.get(model.MD_POS, (0.0, 0.0))
        # Removes the center coordinates of the image. After that, rect will be centered on 0, 0
        rect = (
            rect[0] - pos[0],
            rect[1] - pos[1],
            rect[2] - pos[0],
            rect[3] - pos[1]
        )
        dims = md.get(model.MD_DIMS, "CTZYX"[-self.stream._das.ndim::])
        img_shape = (self.stream._das.shape[dims.index('X')], self.stream._das.shape[dims.index('Y')])

        # Converts rect from physical to pixel coordinates.
        # The received rect is relative to the center of the image, but pixel coordinates
        # are relative to the top-left corner. So it also needs to sum half image.
        # The -1 are necessary on the right and bottom sides, as the coordinates of a pixel
        # are -1 relative to the side of the pixel
        # The '-' before ps[1] is necessary due to the fact that 
        # Y in pixel coordinates grows down, and Y in physical coordinates grows up
        return (
            int(round(rect[0] / ps[0] + img_shape[0] / 2)),
            int(round(rect[1] / (-ps[1]) + img_shape[1] / 2)),
            int(round(rect[2] / ps[0] + img_shape[0] / 2)) - 1,
            int(round(rect[3] / (-ps[1]) + img_shape[1] / 2)) - 1,
        )

    def _getTile(self, x, y, z, prev_raw_cache, prev_proj_cache):
        """
        Get a tile from a DataArrayShadow. Uses cache.
        The cache for projected tiles and the cache for raw tiles has always the same tiles
        x (int): X coordinate of the tile
        y (int): Y coordinate of the tile
        z (int): zoom level where the tile is
        prev_raw_cache (dictionary): raw tiles cache from the
            last execution of _updateImage
        prev_proj_cache (dictionary): projected tiles cache from the
            last execution of _updateImage
        return (tuple(DataArray, DataArray)): raw tile and projected tile
        """
        # the key of the tile on the cache
        tile_key = "%d-%d-%d" % (x, y, z)

        # if the raw tile has been already cached, read it from the cache
        if tile_key in prev_raw_cache:
            raw_tile = prev_raw_cache[tile_key]
        elif tile_key in self._rawTilesCache:
            raw_tile = self._rawTilesCache[tile_key]
        else:
            # The tile was not cached, so it must be read from the file
            raw_tile = self.stream._das.getTile(x, y, z)

        # if the projected tile has been already cached, read it from the cache
        if tile_key in prev_proj_cache:
            proj_tile = prev_proj_cache[tile_key]
        elif tile_key in self._projectedTilesCache:
            proj_tile = self._projectedTilesCache[tile_key]
        else:
            # The tile was not cached, so it must be projected again
            proj_tile = self._projectTile(raw_tile)

        # cache raw and projected tiles
        self._rawTilesCache[tile_key] = raw_tile
        self._projectedTilesCache[tile_key] = proj_tile
        return (raw_tile, proj_tile)

    def _projectTile(self, tile):
        """
        Project the tile
        tile (DataArray): Raw tile
        return (DataArray): Projected tile
        """
        if tile.ndim != 2:
            tile = img.ensure2DImage(tile)  # Remove extra dimensions (of length 1)
        return self._projectXY2RGB(tile, self.stream.tint.value)

    def _getTilesFromSelectedArea(self):
        """
        Get the tiles inside the region defined by .rect and .mpp
        return ((DataArray, DataArray)): Raw tiles and projected tiles
        """

        # This custom exception is used when the .mpp or .rect values changes while
        # generating the tiles. If the values changes, everything needs to be recomputed
        class NeedRecomputeException(Exception):
            pass

        # store the previous cache to use in this execution
        prev_raw_cache = self._rawTilesCache
        prev_proj_cache = self._projectedTilesCache
        # Execute at least once. If mpp and rect changed in
        # the last execution of the loops, execute again
        need_recompute = True
        while need_recompute:
            z = self._zFromMpp()
            rect = self._rectWorldToPixel(self.rect.value)
            # convert the rect coords to tile indexes
            rect = [l / (2 ** z) for l in rect]
            rect = [int(math.floor(l / self.stream._das.tile_shape[0])) for l in rect]
            x1, y1, x2, y2 = rect
            curr_mpp = self.mpp.value
            curr_rect = self.rect.value
            # the 4 lines below avoids that lots of old tiles
            # stays in instance caches
            prev_raw_cache.update(self._rawTilesCache)
            prev_proj_cache.update(self._projectedTilesCache)
            # empty current caches
            self._rawTilesCache = {}
            self._projectedTilesCache = {}

            raw_tiles = []
            projected_tiles = []
            need_recompute = False
            try:
                for x in range(x1, x2 + 1):
                    rt_column = []
                    pt_column = []

                    for y in range(y1, y2 + 1):
                        # the projected tiles cache is invalid
                        if self._projectedTilesInvalid:
                            self._projectedTilesCache = {}
                            prev_proj_cache = {}
                            self._projectedTilesInvalid = False
                            raise NeedRecomputeException()

                        # check if the image changed in the middle of the process
                        if self._im_needs_recompute.is_set():
                            self._im_needs_recompute.clear()
                            # Raise the exception, so everything will be calculated again,
                            # but using the cache from the last execution
                            raise NeedRecomputeException()

                        raw_tile, proj_tile = \
                                self._getTile(x, y, z, prev_raw_cache, prev_proj_cache)
                        rt_column.append(raw_tile)
                        pt_column.append(proj_tile)

                    raw_tiles.append(tuple(rt_column))
                    projected_tiles.append(tuple(pt_column))

            except NeedRecomputeException:
                # image changed
                need_recompute = True

        return (tuple(raw_tiles), tuple(projected_tiles))

    def _updateImage(self):
        """ Recomputes the image with all the raw data available
        """
        # logging.debug("Updating image")
        if not self.stream.raw and isinstance(self.stream.raw, list):
            return

        try:
            # if .raw is a list of DataArray, .image is a complete image
            if isinstance(self.stream.raw, list):
                raw = self.raw[0]
                self.image.value = self._projectTile(raw)
            elif isinstance(self.stream.raw, tuple):
                # .raw is an instance of DataArrayShadow, so .image is
                # a tuple of tuple of tiles
                raw_tiles, projected_tiles = self._getTilesFromSelectedArea()
                self.image.value = projected_tiles
                self.raw = raw_tiles
            else:
                raise AttributeError(".raw must be a list of DA/DAS or a tuple of tuple of DA")

        except Exception:
            logging.exception("Updating %s %s image", self.__class__.__name__, self.name.value)
