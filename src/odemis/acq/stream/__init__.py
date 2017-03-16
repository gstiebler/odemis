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

        self.stream.image.subscribe(self._onStreamImageUpdated)

        # TODO: We need to reorganise everything so that the
        # image display is done via a dataflow (in a separate thread), instead
        # of a VA.
        self._im_needs_recompute = threading.Event()
        weak = weakref.ref(self)
        self._imthread = threading.Thread(target=self._image_thread2,
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
            self.rect = model.TupleContinuous(full_rect, rect_range, setter=self._set_rect)

            self.mpp.subscribe(self._onMpp)
            self.rect.subscribe(self._onRect)

    def _onStreamImageUpdated(self, image):
        self.image.value = image

    #def _onImageUpdated(self, image):
    #    self.stream.image.value = image

    def _onMpp(self, mpp):
        self.stream.mpp.value = mpp

    def _onRect(self, rect):
        self.stream.rect.value = rect

    def _set_mpp(self, mpp):
        ps0 = self.mpp.range[0]
        exp = math.log(mpp / ps0, 2)
        exp = round(exp)
        # TODO check line below
        self.stream.mpp.value = mpp
        return ps0 * 2 ** exp

    def _set_rect(self, rect):
        self.stream.rect.value = rect
        return rect

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
    def _image_thread2(wprojection):
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
                stream._updateImage()
        except Exception:
            logging.exception("image update thread failed")

        gc.collect()
