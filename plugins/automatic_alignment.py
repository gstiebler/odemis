# -*- coding: utf-8 -*-
'''
Created on 10 April 2017

@author: Guilherme Stiebler

Gives ability to automatically change the overlay-metadata.

Copyright © 2017 Éric Piel, Delmic

This file is part of Odemis.

Odemis is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License version 2 as published by the Free Software Foundation.

Odemis is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even
the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
Public License for more details.

You should have received a copy of the GNU General Public License along with Odemis. If not,
see http://www.gnu.org/licenses/.
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
from odemis.gui.util import call_in_wx_main

class AlignmentAcquisitionDialog(AcquisitionDialog):

    @call_in_wx_main
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


def preprocess(ima, invert, flip, crop, gaussian_sigma):
    '''
    invert(bool)
    gaussian_sigma: sigma for the gaussian processing
    '''
    metadata_a = ima.metadata
    if ima.ndim > 2:
        ima = cv2.cvtColor(ima, cv2.COLOR_RGB2GRAY)

    flip_x, flip_y = flip
    # flip on X axis
    if flip_x:
        ima = ima[:, ::-1]

    # flip on Y axis
    if flip_y:
        ima = ima[::-1, :]

    # Invert the image brightness
    if invert:
        mn = ima.min()
        mx = ima.max()
        ima = mx - (ima - mn)

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
        grayscale_im = preprocess(raw, self._invert, self._flip, self._crop, self._gaussian_sigma)
        rgb_im = cv2.cvtColor(grayscale_im, cv2.COLOR_GRAY2RGB)
        rgb_im = model.DataArray(rgb_im, metadata)
        self.image.value = rgb_im

class AutomaticOverlayPlugin(Plugin):
    name = "Automatic Overlay"
    __version__ = "1.0"
    __author__ = "Guilherme Stiebler"
    __license__ = "GPLv2"

        # Describe how the values should be displayed
    # See odemis.gui.conf.data for all the possibilities
    vaconf = OrderedDict((
        ("blur", {
            "label": "Blur window size"
        }),
        ("crop_top", {
            "label": "Crop top"
        }),
        ("crop_bottom", {
            "label": "Crop bottom"
        }),
        ("crop_left", {
            "label": "Crop left"
        }),
        ("crop_right", {
            "label": "Crop right"
        }),
        ("invert", {
            "label": "Invert brightness"
        }),
        ("flip_x", {
            "label": "Flip on X axis"
        }),
        ("flip_y", {
            "label": "Flip on Y axis"
        }),
    ))

    def __init__(self, microscope, main_app):
        super(AutomaticOverlayPlugin, self).__init__(microscope, main_app)
        self.addMenu("Overlay/Automatic alignment corrections", self.start)

        self.blur = model.IntContinuous(10, range=(0, 20), unit="pixels")
        # TODO set the limits of the crop VAs based on the size of the image
        self.crop_top = model.IntContinuous(0, range=(0, 100), unit="pixels")
        self.crop_bottom = model.IntContinuous(0, range=(0, 100), unit="pixels")
        self.crop_left = model.IntContinuous(0, range=(0, 100), unit="pixels")
        self.crop_right = model.IntContinuous(0, range=(0, 100), unit="pixels")
        self.invert = model.BooleanVA(True)
        self.flip_x = model.BooleanVA(False)
        self.flip_y = model.BooleanVA(True)

        # Any change on the VAs should update the stream
        self.blur.subscribe(self._update_stream)
        self.crop_top.subscribe(self._update_stream)
        self.crop_bottom.subscribe(self._update_stream)
        self.crop_left.subscribe(self._update_stream)
        self.crop_right.subscribe(self._update_stream)
        self.invert.subscribe(self._update_stream)
        self.flip_x.subscribe(self._update_stream)
        self.flip_y.subscribe(self._update_stream)


    def start(self):
        dlg = AlignmentAcquisitionDialog(self, "Automatically change the alignment",
                                text="Automatically change the alignment")

        # removing the play overlay from the viewports
        dlg.viewport_l.canvas.remove_view_overlay(dlg.viewport_l.canvas.play_overlay)
        dlg.viewport_r.canvas.remove_view_overlay(dlg.viewport_r.canvas.play_overlay)

        sem_stream = self._get_sem_stream()
        sem_projection = AlignmentProjection(sem_stream)
        crop = (self.crop_top.value, self.crop_bottom.value,\
                self.crop_left.value, self.crop_right.value)
        sem_projection.setPreprocessingParams(False, (False, False), (0, 0, 0, 0), 5)
        self._semStream = sem_projection
        dlg.addStream(sem_projection, 1)

        dlg.addSettings(self, self.vaconf)
        dlg.addButton("Align", self.align, face_colour='blue')
        dlg.addButton("Cancel", None)
        dlg.pnl_gauge.Hide()
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
        tem_projection = AlignmentProjection(s)
        crop = (self.crop_top.value, self.crop_bottom.value,\
                self.crop_left.value, self.crop_right.value)
        flip = (self.flip_x.value, self.flip_y.value)
        tem_projection.setPreprocessingParams(self.invert.value, flip, crop, self.blur.value)
        dlg.addStream(tem_projection, 0)
        self._temStream = tem_projection

    def align(self, dlg):
        crop = (self.crop_top.value, self.crop_bottom.value,\
                self.crop_left.value, self.crop_right.value)
        flip = (self.flip_x.value, self.flip_y.value)
        tem_img = preprocess(self._temStream.raw[0], self.invert.value, flip, crop,
                self.blur.value)
        sem_img = preprocess(self._semStream.raw[0], False, (False, False), (0, 0, 0, 0), 2)
        tmat, kp_tem, kp_sem = keypoint.FindTransform(tem_img, sem_img)

        transf_md = get_img_transformation_md(tmat, tem_img)
        logging.debug(tmat)
        logging.debug(transf_md)

        orig_tem_ps = tem_img.metadata.get(model.MD_PIXEL_SIZE, (1e-9, 1e-9))
        orig_sem_ps = sem_img.metadata.get(model.MD_PIXEL_SIZE, (1e-9, 1e-9))
        ps_prop = (orig_sem_ps[0] / orig_tem_ps[0], orig_sem_ps[1] / orig_tem_ps[1])
        ps_cor = transf_md[model.MD_PIXEL_SIZE]
        new_pixel_size = (orig_tem_ps[0] * ps_prop[0] * ps_cor[0],\
                orig_tem_ps[1] * ps_prop[1] * ps_cor[1])

        orig_pos_sem = sem_img.metadata.get(model.MD_POS, (0.0, 0.0))
        orig_pos_tem = tem_img.metadata.get(model.MD_POS, (0.0, 0.0))
        orig_centers_diff_phys = (orig_pos_tem[0] - orig_pos_sem[0], orig_pos_tem[1] - orig_pos_sem[1])

        pos_cor = transf_md[model.MD_POS]
        pos_cor_phys = (pos_cor[0] * new_pixel_size[0], pos_cor[1] * new_pixel_size[1])

        flip = True
        tem_metadata = self._temStream.raw[0].metadata
        tem_metadata[model.MD_POS] = (orig_pos_tem[0] - orig_centers_diff_phys[0] + pos_cor_phys[0],\
                orig_pos_tem[1] - orig_centers_diff_phys[1] + pos_cor_phys[1])
        tem_metadata[model.MD_PIXEL_SIZE] = new_pixel_size
        # tem_metadata[model.MD_SHEAR] = transf_md[model.MD_SHEAR]
        if flip:
            self._temStream.raw[0] = self._temStream.raw[0][::-1, :]
            tem_metadata[model.MD_ROTATION] = -transf_md[model.MD_ROTATION]
        else:
            tem_metadata[model.MD_ROTATION] = transf_md[model.MD_ROTATION]
        logging.debug(tem_metadata)
        self._temStream.raw[0].metadata = tem_metadata
        self._temStream._shouldUpdateImage()

        crop_top, crop_bottom, crop_left, crop_right = crop
        # remove the bar
        raw = self._temStream.stream.raw[0]
        raw = raw[crop_top:raw.shape[0] - crop_bottom, crop_left:raw.shape[1] - crop_right]

        analysis_tab = self.main_app.main_data.getTabByName('analysis')
        aligned_stream = stream.StaticSEMStream("TEM", raw)
        wx.CallAfter(analysis_tab.stream_bar_controller.addStream, aligned_stream, add_to_view=True)

    def _update_stream(self, value):
        crop = (self.crop_top.value, self.crop_bottom.value,
                self.crop_left.value, self.crop_right.value)
        flip = (self.flip_x.value, self.flip_y.value)
        self._temStream.setPreprocessingParams(self.invert.value, flip, crop, self.blur.value)
        self._temStream._shouldUpdateImage()
