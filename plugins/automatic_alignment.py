# -*- coding: utf-8 -*-
'''
Created on 10 April 2017

@author: Guilherme Stiebler

Gives ability to manually change the overlay-metadata.

This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or
distribute this software, either in source code form or as a compiled
binary, for any purpose, commercial or non-commercial, and by any
means.

In jurisdictions that recognize copyright laws, the author or authors
of this software dedicate any and all copyright interest in the
software to the public domain. We make this dedication for the benefit
of the public at large and to the detriment of our heirs and
successors. We intend this dedication to be an overt act of
relinquishment in perpetuity of all present and future rights to this
software under copyright law.

The software is provided "as is", without warranty of any kind,
express or implied, including but not limited to the warranties of
merchantability, fitness for a particular purpose and non-infringement.
In no event shall the authors be liable for any claim, damages or
other liability, whether in an action of contract, tort or otherwise,
arising from, out of or in connection with the software or the use or
other dealings in the software.
'''

from __future__ import division

from collections import OrderedDict
import functools
import logging
import math
from odemis import dataio, model
from odemis.acq import stream
from odemis.gui.plugin import Plugin, AcquisitionDialog
from odemis.util.dataio import data_to_static_streams, open_acquisition
from odemis.acq.align import keypoint
from odemis.util.conversion import get_img_transformation_md
import odemis.gui.util as guiutil
from odemis.gui.conf import get_acqui_conf
from scipy import ndimage
import os
import wx
import cv2

class AlignmentAcquisitionDialog(AcquisitionDialog):

    # TODO check if the annotation is necessary: @call_in_wx_main
    def addStream(self, stream, index):
        """
        Adds a stream to the canvas, and a stream entry to the stream panel.
        It also ensures the panel box and canvas are shown.

        Note: If this method is not called, the stream panel and canvas are hidden.
        """
        new_stream_l = index == 0 and not self.viewport_l.IsShown()
        new_stream_r = index == 1 and not self.viewport_r.IsShown()

        if index == 0:
            self.viewport_l.Show()
        else:
            self.viewport_r.Show()

        if new_stream_l or new_stream_r:
            self.Layout()
            self.Fit()
            self.Update()

        if stream:
            if index == 0:
                self.streambar_controller.addStream(stream)
                self.microscope_view.addStream(stream)
            else:
                self.microscope_view2.addStream(stream)


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
        ima = cv2.flip(ima, 0)

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


class AlignmentProjection(stream.RGBSpatialProjection):

    def setPreprocessingParams(self, invert, flip, crop, gaussian_sigma):
        self._invert = invert
        self._flip = flip
        self._crop = crop
        self._gaussian_sigma = gaussian_sigma

    def _updateImage(self):
        raw = self.stream.raw[0]
        raw = self._projectTile(raw)

        metadata = raw.metadata
        grayscale_im = preprocess(raw, self._flip, self._invert, self._crop, self._gaussian_sigma)
        rgb_im = cv2.cvtColor(grayscale_im, cv2.COLOR_GRAY2RGB)
        rgb_im = model.DataArray(rgb_im, metadata)
        self.image.value = rgb_im

class AutomaticOverlayPlugin(Plugin):
    name = "Automatic Overlay"
    __version__ = "1.0"
    __author__ = "Guilherme Stiebler"
    __license__ = "Public domain"

    def __init__(self, microscope, main_app):
        super(AutomaticOverlayPlugin, self).__init__(microscope, main_app)
        self.addMenu("Overlay/Automatic alignment corrections", self.start)

        self.va_blur_window = model.IntContinuous(5, range=(0, 20), unit="pixels")
        # TODO set the limits of the crop VAs based on the size of the image
        self.va_crop_top = model.IntContinuous(0, range=(0, 100), unit="pixels")
        self.va_crop_bottom = model.IntContinuous(0, range=(0, 100), unit="pixels")
        self.va_crop_left = model.IntContinuous(0, range=(0, 100), unit="pixels")
        self.va_crop_right = model.IntContinuous(0, range=(0, 100), unit="pixels")
        self.va_invert = model.BooleanVA(True)


    def start(self):
        dlg = AlignmentAcquisitionDialog(self, "Automatically change the alignment",
                                text="Automatically change the alignment")

        # removing the play overlay from the viewports
        dlg.viewport_l.canvas.remove_view_overlay(dlg.viewport_l.canvas.play_overlay)
        dlg.viewport_r.canvas.remove_view_overlay(dlg.viewport_r.canvas.play_overlay)

        vaconf = OrderedDict()

        sem_stream = self._get_sem_stream()
        projection = AlignmentProjection(sem_stream)
        crop = (self.va_crop_top.value, self.va_crop_bottom.value,\
                self.va_crop_left.value, self.va_crop_right.value)
        projection.setPreprocessingParams(self.va_invert.value, True, crop, self.va_blur_window.value)
        self._semStream = projection
        dlg.addStream(projection, 0)

        vaconf["BlurWindow"] = {"label": "Blur window size"}
        vaconf["CropTop"] = {"label": "Crop top"}
        vaconf["CropBottom"] = {"label": "Crop bottom"}
        vaconf["CropLeft"] = {"label": "Crop left"}
        vaconf["CropRight"] = {"label": "Crop right"}
        vaconf["Invert"] = {"label": "Invert"}

        # Create listeners with information of the stream and dimension
        va_on_blur_window = functools.partial(self._on_blur_window, projection, 0)
        va_on_crop = functools.partial(self._on_crop, projection)
        va_on_invert = functools.partial(self._on_invert, projection)

        self.va_blur_window.subscribe(va_on_blur_window)
        self.va_crop_top.subscribe(va_on_crop)
        self.va_crop_bottom.subscribe(va_on_crop)
        self.va_crop_left.subscribe(va_on_crop)
        self.va_crop_right.subscribe(va_on_crop)
        self.va_invert.subscribe(va_on_invert)

        dlg.addSettings(self, vaconf)
        dlg.addButton("Align", self.align, face_colour='blue')
        dlg.addButton("Cancel", None)
        self.open_image(dlg)
        dlg.ShowModal()

    def _get_sem_stream(self):
        """
        Finds the SEM stream in the acquisition tab
        return (SEMStream or None): None if not found
        """
        tab_data = self.main_app.main_data.tab.value.tab_data_model
        for s in tab_data.streams.value:
            if isinstance(s, stream.EMStream):
                return s

        logging.warning("No SEM stream found")
        return None

    def open_image(self, dlg):
        # Find the available formats (and corresponding extensions)
        formats_to_ext = dataio.get_available_formats(os.O_RDONLY)
        config = get_acqui_conf()
        path = config.last_path

        wildcards, formats = guiutil.formats_to_wildcards(formats_to_ext, include_all=True)
        # TODO dlg.pnl_desc?
        dialog = wx.FileDialog(dlg.pnl_desc,
                               message="Choose a file to load",
                               defaultDir=path,
                               defaultFile="",
                               style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
                               wildcard=wildcards)

        # Show the dialog and check whether is was accepted or cancelled
        if dialog.ShowModal() != wx.ID_OK:
            return False

        # Detect the format to use
        filename = dialog.GetPath()

        data = open_acquisition(filename)
        s = data_to_static_streams(data)[0]
        s = s.stream if isinstance(s, stream.DataProjection) else s
        projection = AlignmentProjection(s)
        projection.setPreprocessingParams(False, False, (0, 100, 0, 0), 5)
        dlg.addStream(projection, 1)
        self._temStream = projection

    def align(self, dlg):
        crop = (self.va_crop_top.value, self.va_crop_bottom.value,\
                self.va_crop_left.value, self.va_crop_right.value)
        ima = preprocess(self._semStream.raw[0], True, self.va_invert.value, (0, 0, 0, 0),\
                self.va_blur_window.value)
        imb = preprocess(self._temStream.raw[0], False, False, crop, 5)
        tmat = keypoint.FindTransform(ima, imb)

        transf_md = get_img_transformation_md(tmat, ima)
        logging.debug(tmat)
        logging.debug(transf_md)

        orig_sem_ps = ima.metadata.get(model.MD_PIXEL_SIZE, (0.0, 0.0))
        orig_tem_ps = imb.metadata.get(model.MD_PIXEL_SIZE, (0.0, 0.0))
        ps_prop = (orig_tem_ps[0] / orig_sem_ps[0], orig_tem_ps[1] / orig_sem_ps[1])
        ps_cor = transf_md[model.MD_PIXEL_SIZE]
        new_pixel_size = (orig_sem_ps[0] * ps_prop[0] * ps_cor[0],\
                orig_sem_ps[1] * ps_prop[1] * ps_cor[1])

        orig_pos_sem = ima.metadata.get(model.MD_POS, (0.0, 0.0))
        orig_pos_tem = imb.metadata.get(model.MD_POS, (0.0, 0.0))
        orig_centers_diff_phys = (orig_pos_sem[0] - orig_pos_tem[0], orig_pos_sem[1] - orig_pos_tem[1])

        pos_cor = transf_md[model.MD_POS]
        pos_cor_phys = (pos_cor[0] * new_pixel_size[0], pos_cor[1] * new_pixel_size[1])

        flip = True
        sem_metadata = self._semStream.raw[0].metadata
        sem_metadata[model.MD_POS] = (orig_pos_sem[0] - orig_centers_diff_phys[0] + pos_cor_phys[0],\
                orig_pos_sem[1] - orig_centers_diff_phys[1] + pos_cor_phys[1])
        sem_metadata[model.MD_PIXEL_SIZE] = new_pixel_size
        # sem_metadata[model.MD_SHEAR] = transf_md[model.MD_SHEAR]
        if flip:
            self._semStream.raw[0] = self._semStream.raw[0][::-1, :]
            sem_metadata[model.MD_ROTATION] = -transf_md[model.MD_ROTATION]
        else:
            sem_metadata[model.MD_ROTATION] = transf_md[model.MD_ROTATION]
        print sem_metadata
        self._semStream.raw[0].metadata = sem_metadata
        self._semStream._shouldUpdateImage()

        crop_top, crop_bottom, crop_left, crop_right = crop
        # remove the bar
        raw = self._temStream.stream.raw[0]
        raw = raw[crop_top:raw.shape[0] - crop_bottom, crop_left:raw.shape[1] - crop_right]

        analysis_tab = self.main_app.main_data.getTabByName('analysis')
        aligned_stream = stream.StaticSEMStream("TEM", raw)
        analysis_tab.stream_bar_controller.addStream(aligned_stream, add_to_view=True)

    def _on_blur_window(self, stream, i, value):
        logging.debug("blur value %d, va: %d", value, self.va_blur_window.value)
        self._update_stream(stream)

    def _on_crop(self, stream, value):
        logging.debug("on crop %d", value)
        self._update_stream(stream)

    def _on_invert(self, stream, value):
        logging.debug("_on_invert %d", value)
        self._update_stream(stream)

    def _update_stream(self, stream):
        crop = (self.va_crop_top.value, self.va_crop_bottom.value,\
                self.va_crop_left.value, self.va_crop_right.value)
        stream.setPreprocessingParams(self.va_invert.value, True, crop, self.va_blur_window.value)
        stream._shouldUpdateImage()
