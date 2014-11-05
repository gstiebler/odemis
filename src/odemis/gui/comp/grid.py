#-*- coding: utf-8 -*-
"""
:author:    Rinze de Laat
:copyright: © 2014 Rinze de Laat, Delmic

.. license::

    This file is part of Odemis.

    Odemis is free software: you can redistribute it and/or modify it under the
    terms of the GNU General Public License version 2 as published by the Free
    Software Foundation.

    Odemis is distributed in the hope that it will be useful, but WITHOUT ANY
    WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
    FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
    details.

    You should have received a copy of the GNU General Public License along with
    Odemis. If not, see http://www.gnu.org/licenses/.

"""

import logging
import wx

from odemis.gui.util import AttrDict


class ViewportGrid(wx.Panel):
    """ Display short messages and warning to the user

    TODO: Make the size of invisible viewports relate to the ViewportGrid size?

    """

    def __init__(self, *args, **kwargs):
        super(ViewportGrid, self).__init__(*args, **kwargs)

        # We need a separate attribute that contains all the child viewports, because the default
        # Children property in wx.Python does not allow for reordering.
        self.child_viewports = None
        self.grid_layout = None

        self.Bind(wx.EVT_SIZE, self.on_size)

    @property
    def visible_viewports(self):
        """ Return all the viewports that are visible """
        return [c for c in self.child_viewports if c.Shown]

    @property
    def invisible_viewports(self):
        """ Return all the viewports that are invisible """
        return [c for c in self.child_viewports if not c.Shown]

    ##### Viewport showing and hiding #####

    def set_shown(self, *show_viewports):
        """ Show the given viewports and hide the rest """
        for viewport in self.child_viewports:
            if viewport in show_viewports:
                viewport.Show()
            else:
                viewport.Hide()
        self._layout_viewports()

    def set_hidden(self, *hide_viewports):
        """ Hide the given viewports and show the rest """
        for viewport in self.child_viewports:
            if viewport in hide_viewports:
                viewport.Hide()
            else:
                viewport.Show()
        self._layout_viewports()

    def hide_all(self):
        """ Hide all viewports """
        self.show()

    def show_all(self):
        """ Hide all viewports """
        self.hide()

    def show(self, viewport):
        """ Show the given viewport """
        viewport.Show()
        self._layout_viewports()

    def hide(self, viewport):
        """ Hide the given viewport """
        viewport.Hide()
        self._layout_viewports()

    ##### END Viewport showing and hiding #####

    def on_size(self, evt):
        """ Grab the child windows and perform layout when the size changes """
        if self.child_viewports is None:
            self.child_viewports = list(self.Children)
            if len(self.child_viewports) < 4:
                logging.warn("There should be at least viewports present!")

        self.grid_layout = AttrDict({
            'tl': AttrDict({
                'pos': (0, 0),
                'size': wx.Size(self.ClientSize.x // 2,
                                self.ClientSize.y // 2)
            }),
            'tr': AttrDict({
                'pos': (self.ClientSize.x // 2, 0),
                'size': wx.Size(self.ClientSize.x - (self.ClientSize.x // 2),
                                self.ClientSize.y // 2)
            }),
            'bl': AttrDict({
                'pos': (0, self.ClientSize.y // 2),
                'size': wx.Size(self.ClientSize.x // 2,
                                self.ClientSize.y - (self.ClientSize.y // 2))
            }),
            'br': AttrDict({
                'pos': (self.ClientSize.x // 2, self.ClientSize.y // 2),
                'size': wx.Size(self.ClientSize.x - (self.ClientSize.x // 2),
                                self.ClientSize.y - (self.ClientSize.y // 2))
            }),
        })

        self._layout_viewports()

    def _layout_viewports(self):
        """ Resize, position and display the child viewports

        How the viewports are exactly layed out, depends on the their order and which ones are
        visible.

        The first 4 viewports are considered to be in the 2x2 grid. Their order corresponds to
        top left, top right, bottom left and bottom right.

        Number of visible viewports:

        0 - Set all sizes of the viewports to 400x400
        1 - Display the visible viewport 'full screen', completely covering it's parent. The other
            viewports are resized to their default hidden size of 400x400 pixels
        X - If there is more than one visible viewports, we start looking at their positions,
            because we only consider the first 4 to be in the 2x2 view.

        Number of visible viewports in the first 4 positions:

        < X - Raise an error, since when multiple viewports are visible, they should all be located
              in the first four positions of the 2x2 grid
        >=X - The rule of thumb we use is, that we iterate over the visible viewports in order and
              they will expand into the space of any invisible neighbour.

        """

        visible_vps = self.visible_viewports
        num_vis_total = len(visible_vps)

        # Everything hidden, no layout
        if num_vis_total == 0:
            # Set the size of the invisible viewport to a relative small value, so we make sure that
            # grabbing the client area for thumbnails will be relatively cheap
            for viewport in [vp for vp in self.child_viewports if vp.Size != (400, 400)]:
                viewport.SetSize((400, 400))
        # One shown, make the viewport match the size of the parent
        elif num_vis_total == 1:
            visible_vps[0].SetSize(self.ClientSize)
            visible_vps[0].SetPosition((0, 0))
        else:
            num_vis_grid = len([vp for vp in self.child_viewports[:4] if vp.Shown])

            if num_vis_grid != num_vis_total:
                raise ValueError("If multiple viewports are visible, they should all reside in"
                                 "in the 2x2 grid!")
            else:
                tl, tr, bl, br = [vp for vp in self.child_viewports[:4]]
                gl = self.grid_layout

                if tl.Shown:
                    pos = gl.tl.pos
                    size = (gl.tl.size.x + (gl.tr.size.x if not tr.Shown else 0),
                            gl.tl.size.y + (gl.bl.size.y if not bl.Shown and tr.Shown else 0))

                    tl.SetPosition(pos)
                    tl.SetSize(size)
                elif tl.Size != (400, 400):
                    tl.SetSize((400, 400))

                if tr.Shown:
                    pos = (gl.tr.pos[0] - (gl.tr.size.x if not tl.Shown else 0), 0)
                    size = (gl.tr.size.x + (gl.tl.size.x if not tl.Shown else 0),
                            gl.tr.size.y + (gl.br.size.y if not br.Shown and tl.Shown else 0))

                    tr.SetPosition(pos)
                    tr.SetSize(size)
                elif tr.Size != (400, 400):
                    tr.SetSize((400, 400))

                if bl.Shown:
                    pos = (0, gl.bl.pos[1] - (gl.tl.size.y if not tl.Shown else 0))
                    size = (gl.bl.size.x + (gl.br.size.x if not br.Shown else 0),
                            gl.bl.size.y + (gl.tl.size.y if not tl.Shown and br.Shown else 0))

                    bl.SetPosition(pos)
                    bl.SetSize(size)
                elif bl.Size != (400, 400):
                    bl.SetSize((400, 400))

                if br.Shown:
                    pos = (gl.br.pos[0] - (gl.bl.size.x if not bl.Shown else 0),
                           gl.br.pos[1] - (gl.tr.size.y if not tr.Shown and bl.Shown else 0))
                    size = (gl.br.size.x + (gl.bl.size.x if not bl.Shown else 0),
                            gl.br.size.y + (gl.tr.size.y if not tr.Shown and bl.Shown else 0))

                    br.SetPosition(pos)
                    br.SetSize(size)
                elif br.Size != (400, 400):
                    br.SetSize((400, 400))




        #
        # vp_width, vp_height = width // 2, height // 2
        # vp_x, vp_y = 0, 0
        #
        # if len(visible_vps) == 4:
        #     for vp in visible_vps:
        #         vp.SetSize((vp_width, vp_height))
        #         vp.SetPosition((vp_x, vp_y))
        #         vp_x += vp_width

    def swap(self, vpa, vpb):
        a, b = self.child_viewports.index(vpa), self.child_viewports.index(vpb)
        self.child_viewports[a], self.child_viewports[b] = self.child_viewports[b], self.child_viewports[a]
        self._layout_viewports()
