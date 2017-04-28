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
import os
import wx
import cv2

class VAHolder(object):
    pass

class AlignmentProjection(stream.RGBSpatialProjection):

    def setPreprocessingParams(self, invert, flip, crop, gaussian_ksize, gaussian_sigma):
        # gaussian_ksize must be odd
        gaussian_ksize = gaussian_ksize + 1 if gaussian_ksize % 2 == 0 else gaussian_ksize
        self._invert = invert
        self._flip = flip
        self._crop = crop
        self._gaussian_ksize = gaussian_ksize
        self._gaussian_sigma = gaussian_sigma

    def preprocess(self, ima):
        '''
        invert(bool)
        gaussian_ksize: kernel size for the gaussian processing: Must be odd and positive
        gaussian_sigma: sigma for the gaussian processing
        '''
        metadata_a = ima.metadata
        if ima.ndim > 2:
            ima = cv2.cvtColor(ima, cv2.COLOR_RGB2GRAY)

        # invert on Y axis
        if self._flip:
            ima = cv2.flip(ima, 0)

        # Invert the image brightness
        if self._invert:
            ima = 255 - ima

        ima_height = ima.shape[0]

        crop_top, crop_bottom, crop_left, crop_right = self._crop
        # remove the bar
        ima = ima[crop_top:ima.shape[0] - crop_bottom, crop_left:ima.shape[1] - crop_right]

        # equalize histogram
        ima = cv2.equalizeHist(ima)

        # blur (kernel size must be odd)
        ima = cv2.GaussianBlur(ima, (self._gaussian_ksize, self._gaussian_ksize),\
                self._gaussian_sigma)

        return  model.DataArray(ima, metadata_a)

    def _updateImage(self):
        super(AlignmentProjection, self)._updateImage()
        metadata = self.image.value.metadata
        self.grayscale_im = self.preprocess(self.image.value)
        rgb_im = cv2.cvtColor(self.grayscale_im, cv2.COLOR_GRAY2RGB)
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


    def start(self):
        dlg = AcquisitionDialog(self, "Automatically change the alignment",
                                text="Automatically change the alignment")

        # removing the play overlay from the viewports
        dlg.viewport_l.canvas.remove_view_overlay(dlg.viewport_l.canvas.play_overlay)
        dlg.viewport_r.canvas.remove_view_overlay(dlg.viewport_r.canvas.play_overlay)

        vah = VAHolder()
        vah._subscribers = []
        vaconf = OrderedDict()

        self.va_blur_window = model.IntContinuous(41, range=(1, 81), unit="pixels")
        # TODO set the limits of the crop VAs based on the size of the image
        self.va_crop_top = model.IntContinuous(0, range=(0, 100), unit="pixels")
        self.va_crop_bottom = model.IntContinuous(0, range=(0, 100), unit="pixels")
        self.va_crop_left = model.IntContinuous(0, range=(0, 100), unit="pixels")
        self.va_crop_right = model.IntContinuous(0, range=(0, 100), unit="pixels")
        self.va_invert = model.BooleanVA(False)

        sem_stream = self._get_sem_stream()
        projection = AlignmentProjection(sem_stream)
        crop = (self.va_crop_top.value, self.va_crop_bottom.value,\
                self.va_crop_left.value, self.va_crop_right.value)
        projection.setPreprocessingParams(self.va_invert.value, True, crop, self.va_blur_window.value, 10)
        self._semStream = projection
        dlg.addStream(projection, 0)

        # Add the VAs to the holder, and to the vaconf mainly to force the order
        setattr(vah, "BlurWindow", self.va_blur_window)
        setattr(vah, "CropTop", self.va_crop_top)
        setattr(vah, "CropBottom", self.va_crop_bottom)
        setattr(vah, "CropLeft", self.va_crop_left)
        setattr(vah, "CropRight", self.va_crop_right)
        setattr(vah, "Invert", self.va_invert)

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

        # We hold a reference to the listeners to prevent automatic subscription
        vah._subscribers.append(va_on_blur_window)
        vah._subscribers.append(va_on_crop)
        vah._subscribers.append(va_on_invert)

        self.va_blur_window.subscribe(va_on_blur_window)
        self.va_crop_top.subscribe(va_on_crop)
        self.va_crop_bottom.subscribe(va_on_crop)
        self.va_crop_left.subscribe(va_on_crop)
        self.va_crop_right.subscribe(va_on_crop)
        self.va_invert.subscribe(va_on_invert)

        dlg.fp_streams.Hide()
        dlg.addSettings(vah, vaconf)
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
        stream = data_to_static_streams(data)
        projection = AlignmentProjection(stream[0])
        projection.setPreprocessingParams(False, False, (0, 100, 0, 0), 21, 5)
        dlg.addStream(projection, 1)
        # after addStream
        dlg.fp_streams.Hide()
        self._temStream = projection

    def align(self, dlg):
        ima = self._semStream.grayscale_im
        imb = self._temStream.grayscale_im
        # TODO Preprocess not needed here
        ima, imb = keypoint.Preprocess(ima, imb)
        tmat = keypoint.FindTransform(ima, imb)
        # warped_im = cv2.warpPerspective(ima, tmat, (imb.shape[1], imb.shape[0]))
        # merged_im = cv2.addWeighted(imb, 0.5, warped_im, 0.5, 0.0)
        # cv2.imwrite(imgs_folder + 'warped.jpg', merged_im)

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
        stream.setPreprocessingParams(self.va_invert.value, True, crop, self.va_blur_window.value, 10)
        stream._shouldUpdateImage()
