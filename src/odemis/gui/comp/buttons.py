#-*- coding: utf-8 -*-
'''
@author: Rinze de Laat

Copyright © 2012 Rinze de Laat, Delmic

This file is part of Odemis.

Odemis is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 2 of the License, or (at your option) any later version.

Odemis is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Odemis. If not, see http://www.gnu.org/licenses/.
'''

# This module contains various custom button classes used throughout the odemis
# project.
#
# All these classes are supported within XRCED as long as the xmlh/delmic.py
# and xmlh/xh_delmic.py modules are available (e.g. through a symbolic link)
# in XRCED's plugin directory.


import wx

from wx.lib.buttons import GenBitmapButton, GenBitmapToggleButton, \
    GenBitmapTextToggleButton, GenBitmapTextButton

import odemis.gui.img.data as img
from odemis.gui.log import log

def resize_bmp(btn_size, bmp):
    """ Resize the given image so it will match the size of the button """

    if btn_size:
        btn_width, _ = btn_size
        img_width, img_height = bmp.GetSize()

        if btn_width > 0 and img_width != btn_width:
            log.debug("Resizing button bmp from %s to %s",
                      bmp.GetSize(),
                      btn_size)
            new_img = bmp.ConvertToImage()
            return new_img.Rescale(btn_width, img_height).ConvertToBitmap()

    return bmp

class ImageButton(GenBitmapButton):
    """ Graphical button with hover effect.

    The background colour is set to that of its parent, or to the background
    colour of an explicitly defined window called background_parent.
    """

    labelDelta = 0

    def __init__(self, *args, **kwargs):
        """ If the background_parent keyword argument is provided, it will be
        used to determine the background colour of the button. Otherwise, the
        direct parent will be used.
        """
        if kwargs.has_key('style'):
            kwargs['style'] |= wx.NO_BORDER
        else:
            kwargs['style'] = wx.NO_BORDER

        self.background_parent = kwargs.pop('background_parent', None)
        self.labelDelta = kwargs.pop('label_delta', 0)

        # Fit the bmp if needed
        # Resizing should always be minimal, so distortion is minimum

        # If the bmp arg is provided (which is the 3rd one: parent, id, bmp)

        bmp = args[2] if len(args) >= 3 else kwargs.get('bitmap', None)
        size = args[4] if len(args) >= 5 else kwargs.get('size', None)

        if bmp:
            if size and size != (-1, -1):
                args = list(args)
                # Resize and replace original bmp
                if len(args) >= 3:
                    args[2] = resize_bmp(size, bmp)
                else:
                    kwargs['bitmap'] = resize_bmp(size, bmp)
            else:
                # Set the size of the button to match the bmp
                if len(args) >= 5:
                    args[4] = bmp.GetSize()
                else:
                    kwargs['size'] = bmp.GetSize()

        GenBitmapButton.__init__(self, *args, **kwargs)

        if self.background_parent:
            self.SetBackgroundColour(self.background_parent.GetBackgroundColour())
        else:
            self.SetBackgroundColour(self.GetParent().GetBackgroundColour())

        self.bmpHover = None
        self.hovering = False

        self.Bind(wx.EVT_ENTER_WINDOW, self.OnEnter)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeave)

    def OnEnter(self, evt):
        if self.bmpHover:
            self.hovering = True
            self.Refresh()

    def OnLeave(self, evt):
        if self.bmpHover:
            self.hovering = False
            self.Refresh()

    def SetBitmaps(self, bmp_h=None):
        """ This method sets additional bitmaps for hovering and selection """
        if bmp_h:
            bmp_h = resize_bmp(self.GetSize(), bmp_h)
            self.SetBitmapHover(bmp_h)

    def GetBitmapHover(self):
        return self.bmpHover

    def SetBitmapHover(self, bitmap):
        """Set bitmap to display when the button is hovered over"""
        self.bmpHover = bitmap

    def DrawLabel(self, dc, width, height, dx=0, dy=0):
        bmp = self.bmpLabel
        if self.hovering and self.bmpHover:
            bmp = self.bmpHover
        if self.bmpDisabled and not self.IsEnabled():
            bmp = self.bmpDisabled
        if self.bmpFocus and self.hasFocus:
            bmp = self.bmpFocus
        if self.bmpSelected and not self.up:
            bmp = self.bmpSelected
        bw, bh = bmp.GetWidth(), bmp.GetHeight()
        if not self.up:
            dx = dy = self.labelDelta

        hasMask = bmp.GetMask() != None
        dc.DrawBitmap(bmp, (width - bw) / 2 + dx, (height - bh) / 2 + dy, hasMask)

    def InitColours(self):
        GenBitmapButton.InitColours(self)
        if self.background_parent:
            self.faceDnClr = self.background_parent.GetBackgroundColour()
        else:
            self.faceDnClr = self.GetParent().GetBackgroundColour()

    def SetLabelDelta(self, delta):
        self.labelDelta = delta

class ImageTextButton(GenBitmapTextButton):
    """ Graphical button with text and hover effect.

    rescale: if the rescale keyword argument is True and the button has a size,
    the background image will be scaled to fit.

    The text can be align using the following styles:
    wx.ALIGN_LEFT, wx.ALIGN_CENTER, wx.ALIGN_RIGHT.

    Left alignment is the default.
    """
    # The displacement of the button content when it is pressed down, in pixels
    labelDelta = 1
    padding_x = 8
    padding_y = 1

    def __init__(self, *args, **kwargs):

        kwargs['style'] = kwargs.get('style', 0) | wx.NO_BORDER

        self.labelDelta = kwargs.pop('label_delta', 0)
        self.rescale = kwargs.pop('rescale', False)

        self.background_parent = kwargs.pop('background_parent', None)

        # Fit the bmp if needed
        # Resizing should always be minimal, so distortion is minimum

        # If the bmp arg is provided (which is the 3rd one: parent, id, bmp)

        bmp = args[2] if len(args) >= 3 else kwargs.get('bitmap', None)
        size = args[4] if len(args) >= 5 else kwargs.get('size', None)

        if bmp:
            if size and size != (-1, -1):
                args = list(args)
                # Resize and replace original bmp
                if len(args) >= 3:
                    args[2] = resize_bmp(size, bmp)
                else:
                    kwargs['bitmap'] = resize_bmp(size, bmp)
            else:
                # Set the size of the button to match the bmp
                if len(args) >= 5:
                    args[4] = bmp.GetSize()
                else:
                    kwargs['size'] = bmp.GetSize()

        GenBitmapTextButton.__init__(self, *args, **kwargs)

        self.bmpHover = None
        self.hovering = False

        self.Bind(wx.EVT_ENTER_WINDOW, self.OnEnter)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeave)

    def SetBitmaps(self, bmp_h=None, bmp_sel=None):
        """ This method sets additional bitmaps for hovering and selection """

        if bmp_h:
            bmp_h = resize_bmp(self.GetSize(), bmp_h)
            self.SetBitmapHover(bmp_h)
        if bmp_sel:
            bmp_sel = resize_bmp(self.GetSize(), bmp_sel)
            self.SetBitmapSelected(bmp_sel)

    def GetBitmapHover(self):
        return self.bmpHover

    def SetBitmapHover(self, bitmap):
        """Set bitmap to display when the button is hovered over"""
        self.bmpHover = bitmap

    def OnEnter(self, evt):
        if self.bmpHover:
            self.hovering = True
            self.Refresh()

    def OnLeave(self, evt):
        if self.bmpHover:
            self.hovering = False
            self.Refresh()

    def DrawLabel(self, dc, width, height, dx=0, dy=0):

        bmp = self.bmpLabel

        # If one or more bitmaps are defined...
        if bmp is not None:
            if self.hovering and self.bmpHover:
                bmp = self.bmpHover
            if self.bmpDisabled and not self.IsEnabled():
                bmp = self.bmpDisabled
            if self.bmpFocus and self.hasFocus:
                bmp = self.bmpFocus
            if self.bmpSelected and not self.up:
                bmp = self.bmpSelected
            bw, bh = bmp.GetWidth(), bmp.GetHeight()
            if not self.up:
                dx = dy = self.labelDelta
            hasMask = bmp.GetMask() is not None
        # no bitmap -> size is zero
        else:
            bw = bh = 0

        # Determine font and font colour
        dc.SetFont(self.GetFont())
        if self.IsEnabled():
            dc.SetTextForeground(self.GetForegroundColour())
        else:
            dc.SetTextForeground(wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT))

        # Get the label text
        label = self.GetLabel()

        # Determine the size of the text
        tw, th = dc.GetTextExtent(label) # size of text
        if not self.up:
            dx = dy = self.labelDelta

        # Calculate the x position for the given background bitmap
        # The bitmap will be center within the button.
        pos_x = (width - bw) / 2 + dx
        if bmp is not None:
            #Background bitmap is centered
            dc.DrawBitmap(bmp, (width - bw) / 2, (height - bh) / 2, hasMask)


        if self.HasFlag(wx.ALIGN_CENTER):
            pos_x = pos_x + (bw - tw) / 2
        elif self.HasFlag(wx.ALIGN_RIGHT):
            pos_x = pos_x + bw - tw - self.padding_x
        else:
            pos_x = pos_x + self.padding_x

        dc.DrawText(label, pos_x, (height - th) / 2 + dy + self.padding_y)      # draw the text

    def InitColours(self):
        GenBitmapTextButton.InitColours(self)
        if self.background_parent:
            self.faceDnClr = self.background_parent.GetBackgroundColour()
        else:
            self.faceDnClr = self.GetParent().GetBackgroundColour()

class ImageToggleButton(GenBitmapToggleButton):  #pylint: disable=R0901
    """ Graphical toggle button with a hover effect. """

    # The displacement of the button content when it is pressed down, in pixels
    labelDelta = 0

    def __init__(self, *args, **kwargs):

        kwargs['style'] = wx.NO_BORDER
        self.labelDelta = kwargs.pop('label_delta', 0)
        self.background_parent = kwargs.pop('background_parent', None)

        # Fit the bmp if needed
        # Resizing should always be minimal, so distortion is minimum

        # If the bmp arg is provided (which is the 3rd one: parent, id, bmp)

        bmp = args[2] if len(args) >= 3 else kwargs.get('bitmap', None)
        size = args[4] if len(args) >= 5 else kwargs.get('size', None)

        if bmp:
            if size and size != (-1, -1):
                args = list(args)
                # Resize and replace original bmp
                if len(args) >= 3:
                    args[2] = resize_bmp(size, bmp)
                else:
                    kwargs['bitmap'] = resize_bmp(size, bmp)
            else:
                # Set the size of the button to match the bmp
                if len(args) >= 5:
                    args[4] = bmp.GetSize()
                else:
                    kwargs['size'] = bmp.GetSize()

        GenBitmapToggleButton.__init__(self, *args, **kwargs)

        if self.background_parent:
            self.SetBackgroundColour(self.background_parent.GetBackgroundColour())
        else:
            self.SetBackgroundColour(self.GetParent().GetBackgroundColour())

        self.bmpHover = None
        self.bmpSelectedHover = None
        self.hovering = False

        self.Bind(wx.EVT_ENTER_WINDOW, self.OnEnter)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeave)

    def SetBitmaps(self, bmp_h=None, bmp_sel=None, bmp_sel_h=None):
        """ This method sets additional bitmaps for hovering and selection """
        if bmp_h:
            bmp_h = resize_bmp(self.GetSize(), bmp_h)
            self.SetBitmapHover(bmp_h)
        if bmp_sel:
            bmp_sel = resize_bmp(self.GetSize(), bmp_sel)
            self.SetBitmapSelected(bmp_sel)
        if bmp_sel_h:
            bmp_sel_h = resize_bmp(self.GetSize(), bmp_sel_h)
            self.SetBitmapSelectedHover(bmp_sel_h)

    def GetBitmapHover(self):
        return self.bmpHover

    def SetBitmapHover(self, bitmap):
        """Set bitmap to display when the button is hovered over"""
        self.bmpHover = bitmap

    def GetBitmapSelectedHover(self):
        return self.bmpSelectedHover

    def SetBitmapSelectedHover(self, bitmap):
        self.bmpSelectedHover = bitmap

    def OnEnter(self, evt):
        if self.bmpHover:
            self.hovering = True
            self.Refresh()

    def OnLeave(self, evt):
        if self.bmpHover:
            self.hovering = False
            self.Refresh()

    def DrawLabel(self, dc, width, height, dx=0, dy=0):
        bmp = self.bmpLabel
        if self.hovering and self.bmpHover:
            bmp = self.bmpHover
        if self.bmpDisabled and not self.IsEnabled():
            bmp = self.bmpDisabled
        if self.bmpFocus and self.hasFocus:
            bmp = self.bmpFocus
        if self.bmpSelected and not self.up:
            if self.hovering:
                bmp = self.bmpSelectedHover
            else:
                bmp = self.bmpSelected
        bw, bh = bmp.GetWidth(), bmp.GetHeight()
        if not self.up:
            dx = dy = self.labelDelta
        hasMask = bmp.GetMask() != None
        dc.DrawBitmap(bmp,
                      (width - bw) / 2 + dx,
                      (height - bh) / 2 + dy,
                      hasMask)

    def InitColours(self):
        GenBitmapButton.InitColours(self)
        if self.background_parent:
            self.faceDnClr = self.background_parent.GetBackgroundColour()
        else:
            self.faceDnClr = self.GetParent().GetBackgroundColour()

class ImageTextToggleButton(GenBitmapTextToggleButton):
    """ Graphical toggle button with text and a hover effect. """

    # The displacement of the button content when it is pressed down, in pixels
    labelDelta = 1
    padding_x = 8
    padding_y = 1

    def __init__(self, *args, **kwargs):

        kwargs['style'] = kwargs.get('style', 0) | wx.NO_BORDER

        self.labelDelta = kwargs.pop('label_delta', 0)
        self.background_parent = kwargs.pop('background_parent', None)

        # Fit the bmp if needed
        # Resizing should always be minimal, so distortion is minimum

        # If the bmp arg is provided (which is the 3rd one: parent, id, bmp)

        bmp = args[2] if len(args) >= 3 else kwargs.get('bitmap', None)
        size = args[4] if len(args) >= 5 else kwargs.get('size', None)

        if bmp:
            if size and size != (-1, -1):
                args = list(args)
                # Resize and replace original bmp
                if len(args) >= 3:
                    args[2] = resize_bmp(size, bmp)
                else:
                    kwargs['bitmap'] = resize_bmp(size, bmp)
            else:
                # Set the size of the button to match the bmp
                if len(args) >= 5:
                    args[4] = bmp.GetSize()
                else:
                    kwargs['size'] = bmp.GetSize()

        GenBitmapTextToggleButton.__init__(self, *args, **kwargs)

        self.bmpHover = None
        self.bmpSelectedHover = None
        self.hovering = False

        self.Bind(wx.EVT_ENTER_WINDOW, self.OnEnter)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeave)

    def SetBitmaps(self, bmp_h=None, bmp_sel=None, bmp_sel_h=None):
        """ This method sets additional bitmaps for hovering and selection """
        if bmp_h:
            bmp_h = resize_bmp(self.GetSize(), bmp_h)
            self.SetBitmapHover(bmp_h)
        if bmp_sel:
            bmp_sel = resize_bmp(self.GetSize(), bmp_sel)
            self.SetBitmapSelected(bmp_sel)
        if bmp_sel_h:
            bmp_sel_h = resize_bmp(self.GetSize(), bmp_sel_h)
            self.SetBitmapSelectedHover(bmp_sel_h)

    def GetBitmapHover(self):
        return self.bmpHover

    def SetBitmapHover(self, bitmap):
        """Set bitmap to display when the button is hovered over"""
        self.bmpHover = bitmap

    def GetBitmapSelectedHover(self):
        return self.bmpSelectedHover

    def SetBitmapSelectedHover(self, bitmap):
        self.bmpSelectedHover = bitmap

    def OnEnter(self, evt):
        if self.bmpHover:
            self.hovering = True
            self.Refresh()

    def OnLeave(self, evt):
        if self.bmpHover:
            self.hovering = False
            self.Refresh()

    def DrawLabel(self, dc, width, height, dx=0, dy=0):
        bmp = self.bmpLabel
        if bmp is not None:     # if the bitmap is used
            if self.hovering and self.bmpHover:
                bmp = self.bmpHover
            if self.bmpDisabled and not self.IsEnabled():
                bmp = self.bmpDisabled
            if self.bmpFocus and self.hasFocus:
                bmp = self.bmpFocus
            if self.bmpSelected and not self.up:
                bmp = self.bmpSelected
            bw, bh = bmp.GetWidth(), bmp.GetHeight()
            if not self.up:
                dx = dy = self.labelDelta
            hasMask = bmp.GetMask() is not None
        else:
            bw = bh = 0     # no bitmap -> size is zero

        dc.SetFont(self.GetFont())
        if self.IsEnabled():
            dc.SetTextForeground(self.GetForegroundColour())
        else:
            dc.SetTextForeground(wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT))

        label = self.GetLabel()
        tw, th = dc.GetTextExtent(label) # size of text
        if not self.up:
            dx = dy = self.labelDelta

        pos_x = (width - bw) / 2 + dx
        if bmp is not None:
            #dc.DrawBitmap(bmp, (width - bw) / 2 + dx, (height - bh) / 2 + dy, hasMask)
            dc.DrawBitmap(bmp, (width - bw) / 2, (height - bh) / 2, hasMask)

        if self.HasFlag(wx.ALIGN_CENTER):
            pos_x = pos_x + (bw - tw) / 2
        elif self.HasFlag(wx.ALIGN_RIGHT):
            pos_x = pos_x + bw - tw - self.padding_x
        else:
            pos_x = pos_x + self.padding_x

        dc.DrawText(label, pos_x, (height - th) / 2 + dy + 1) # draw the text

    def InitColours(self):
        GenBitmapButton.InitColours(self)
        if self.background_parent:
            self.faceDnClr = self.background_parent.GetBackgroundColour()
        else:
            self.faceDnClr = self.GetParent().GetBackgroundColour()

class ViewButton(ImageTextToggleButton):
    """ The ViewButton class describes a toggle button that has an image overlay
    that depicts a thumbnail view of one of the view panels.

    Since the aspect ratio of views is dynamic, the ratio of the ViewButton will
    also need to be dynamic, but it will be limited to the height only, so the
    width will remain static.

    """

    def __init__(self, *args, **kwargs):
        ImageTextToggleButton.__init__(self, *args, **kwargs)

        # The image to use as an overlay. It needs to be set using the
        # `set_overlay` method.
        self.overlay_image = None

        # The number of pixels from the right that need to be kept clear so the
        # 'arrow pointer' is visible.
        self.pointer_offset = 16

        # The border that will be kept clear.
        self.overlay_border = 5

        self._calc_overlay_size()

    def _calc_overlay_size(self, ):
        width, height = self.GetSize()
        self.overlay_width = width - self.overlay_border * 2 - self.pointer_offset
        self.overlay_height = height - self.overlay_border * 2

    def OnLeftDown(self, event):

        if not self.IsEnabled() or not self.up:
            log.debug("ViewButton already active")
            return
        self.saveUp = self.up
        self.up = not self.up
        self.CaptureMouse()
        self.SetFocus()
        self.Refresh()

    def set_overlay(self, image):
        """
        Changes the image (preview) of the button
        image (wx.Image or None): new image. If None, a stock image is used
        """
        log.debug("Setting overlay")

        # Calculate the needed height
        # if image:
        #     img_w, img_h = [float(v) for v in image.GetSize()]
        #     width, height = self.GetSize()
        #     # ratio = self.GetSize()[0] - self.pointer_offset - self.overlay_border * 2
        #     self.SetBestSize((width, height * 0.5))
        #     self.Parent.Layout()
        #     self._calc_overlay_size()

        if image is None:
            # black image
            small_image = wx.EmptyImage(self.overlay_width, self.overlay_height)
        else:
            # FIXME: what's the right size?
            # FIXME: not all the thumbnails have the right aspect ratio => truncate
            # was 70, 70... but let's avoid constants

            # NOTE: The next values are cast to float, because they are going to
            # be used to calculate ratios and the default behaviour for Python
            # 2.x it to floor integer divisions. Another way of dealing with
            # this, is to use the "from __future__ import division" statement
            # which will make integer division result in a float value. The
            # advantage of this approach is that the code will be compatible
            # with Python 3.x
            img_w, img_h = [float(v) for v in image.GetSize()]

            log.debug("Image size is %s %s ", img_w, img_h)
            log.debug("Button size is %s %s ",
                      self.overlay_width,
                      self.overlay_height)

            if img_w / self.overlay_width < img_h / self.overlay_height:
                img_w = int(img_w * (self.overlay_height / img_h))
                img_h = self.overlay_height
            else:
                img_h = int(img_h * (self.overlay_width / img_w))
                img_w = self.overlay_width

            log.debug("New image size is %s %s", img_w, img_h)
            small_image = image.Scale(img_w,
                                      img_h,
                                      wx.IMAGE_QUALITY_HIGH)

        self.overlay_image = wx.BitmapFromImage(small_image)
        self.Refresh()

    def DrawLabel(self, dc, width, height, dx=0, dy=0):
        ImageTextToggleButton.DrawLabel(self, dc, width, height, dx, dy)

        if self.overlay_image is not None:
            #log.debug("Painting overlay")
            dc.DrawBitmap(self.overlay_image,
                          self.overlay_border,
                          self.overlay_border,
                          True)


class TabButton(ImageTextToggleButton):

    def OnLeftDown(self, event):
        if not self.IsEnabled() or not self.up:
            return
        self.saveUp = self.up
        self.up = not self.up
        self.CaptureMouse()
        self.SetFocus()
        self.Refresh()


class GraphicRadioButton(ImageTextToggleButton):

    def __init__(self, *args, **kwargs):
        self.value = kwargs.pop('value')
        if not kwargs.get('label', False):
            kwargs['label'] = u"%g" % self.value
        ImageTextToggleButton.__init__(self, *args, **kwargs)

    def OnLeftDown(self, event):
        if not self.IsEnabled() or not self.up:
            return
        self.saveUp = self.up
        self.up = not self.up
        self.CaptureMouse()
        self.SetFocus()
        self.Refresh()

class ColourButton(ImageButton):
    """ An ImageButton that uses a single-colour bitmap
    that will be dynamically generated, allowing it to change colour during the
    buttons life time.
    """

    # The default colour for the colour button
    DEFAULT_COLOR = "#88BA38"

    def __init__(self, *args, **kwargs):

        colour = kwargs.pop('colour', None)
        self.use_hover = kwargs.pop('use_hover', False)
        ImageButton.__init__(self, *args, **kwargs)
        self.set_colour(colour)

    def set_colour(self, colour=None):
        """ Update the colour button to reflect the provided colour """

        self.colour = colour or self.DEFAULT_COLOR

        BMP_EMPTY = img.getemptyBitmap()

        brush = wx.Brush(self.colour)
        pen = wx.Pen(self.colour)
        bmp = BMP_EMPTY.GetSubBitmap(
                    wx.Rect(0, 0, BMP_EMPTY.GetWidth(), BMP_EMPTY.GetHeight()))
        mdc = wx.MemoryDC()
        mdc.SelectObject(bmp)
        mdc.SetBrush(brush)
        mdc.SetPen(pen)
        mdc.DrawRectangle(4, 4, 10, 10)
        mdc.SelectObject(wx.NullBitmap)

        self.SetBitmapLabel(bmp)

        if self.use_hover:
            BMP_EMPTY_H = img.getempty_hBitmap()
            bmp = BMP_EMPTY_H.GetSubBitmap(
                        wx.Rect(0, 0, BMP_EMPTY.GetWidth(), BMP_EMPTY.GetHeight()))
            mdc = wx.MemoryDC()
            mdc.SelectObject(bmp)
            mdc.SetBrush(brush)
            mdc.SetPen(pen)
            mdc.DrawRectangle(4, 4, 10, 10)
            mdc.SelectObject(wx.NullBitmap)

            self.SetBitmaps(bmp)

        self.Refresh()

    def get_colour(self):
        return self.colour

class PopupImageButton(ImageTextButton):

    def __init__(self, *args, **kwargs):
        ImageTextButton.__init__(self, *args, **kwargs)
        self.choices = None
        self.Bind(wx.EVT_BUTTON, self.show_menu)

    def set_choices(self, choices):
        self.choices = choices

    def show_menu(self, evt):

        if not self.choices:
            return

        class MenuPopup(wx.PopupTransientWindow):
            def __init__(self, parent, style):
                wx.PopupTransientWindow.__init__(self, parent, style)
                self.lb = wx.ListBox(self, -1)

                sz = self.lb.GetBestSize()

                width = parent.GetSize().GetWidth() - 20
                height = sz.height + 10

                #sz.width -= wx.SystemSettings_GetMetric(wx.SYS_VSCROLL_X)
                self.lb.SetBackgroundColour("#DDDDDD")
                self.lb.SetSize((width, height))
                self.SetSize((width, height - 2))

                self.Bind(wx.EVT_LISTBOX, self.on_select)

            def on_select(self, evt):
                evt.Skip()
                self.Dismiss()
                self.OnDismiss()

            def ProcessLeftDown(self, evt):
                return False

            def OnDismiss(self):
                self.GetParent().hovering = False
                self.GetParent().Refresh()

            def SetChoices(self, choices):
                self.lb.Set(choices)

        win = MenuPopup(self, wx.SIMPLE_BORDER)
        win.SetChoices(self.choices)

        # Show the popup right below or above the button
        # depending on available screen space...
        btn = evt.GetEventObject()
        pos = btn.ClientToScreen((10, -5))
        sz = btn.GetSize()
        win.Position(pos, (0, sz[1]))

        win.Popup()


