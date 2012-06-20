# This file was automatically generated by pywxrc.
# -*- coding: UTF-8 -*-

import wx
import wx.xrc as xrc

__res = None

def get_resources():
    """ This function provides access to the XML resources in this module."""
    global __res
    if __res == None:
        __init_resources()
    return __res




class xrcfpb_frame(wx.Frame):
#!XRCED:begin-block:xrcfpb_frame.PreCreate
    def PreCreate(self, pre):
        """ This function is called during the class's initialization.
        
        Override it for custom setup before the window is created usually to
        set additional window styles using SetWindowStyle() and SetExtraStyle().
        """
        pass
        
#!XRCED:end-block:xrcfpb_frame.PreCreate

    def __init__(self, parent):
        # Two stage creation (see http://wiki.wxpython.org/index.cgi/TwoStageCreation)
        pre = wx.PreFrame()
        self.PreCreate(pre)
        get_resources().LoadOnFrame(pre, parent, "fpb_frame")
        self.PostCreate(pre)

        # Define variables for the controls, bind event handlers
        self.scrwin = xrc.XRCCTRL(self, "scrwin")
        self.fpb = xrc.XRCCTRL(self, "fpb")
        self.panel_1 = xrc.XRCCTRL(self, "panel_1")
        self.panel_2 = xrc.XRCCTRL(self, "panel_2")
        self.panel_3 = xrc.XRCCTRL(self, "panel_3")



class xrcstream_frame(wx.Frame):
#!XRCED:begin-block:xrcstream_frame.PreCreate
    def PreCreate(self, pre):
        """ This function is called during the class's initialization.
        
        Override it for custom setup before the window is created usually to
        set additional window styles using SetWindowStyle() and SetExtraStyle().
        """
        pass
        
#!XRCED:end-block:xrcstream_frame.PreCreate

    def __init__(self, parent):
        # Two stage creation (see http://wiki.wxpython.org/index.cgi/TwoStageCreation)
        pre = wx.PreFrame()
        self.PreCreate(pre)
        get_resources().LoadOnFrame(pre, parent, "stream_frame")
        self.PostCreate(pre)

        # Define variables for the controls, bind event handlers
        self.scrwin = xrc.XRCCTRL(self, "scrwin")
        self.fpb = xrc.XRCCTRL(self, "fpb")
        self.fsp_1 = xrc.XRCCTRL(self, "fsp_1")
        self.fsp_2 = xrc.XRCCTRL(self, "fsp_2")
        self.fsp_3 = xrc.XRCCTRL(self, "fsp_3")
        self.csp_1 = xrc.XRCCTRL(self, "csp_1")
        self.csp_2 = xrc.XRCCTRL(self, "csp_2")
        self.csp_3 = xrc.XRCCTRL(self, "csp_3")





# ------------------------ Resource data ----------------------

def __init_resources():
    global __res
    __res = xrc.EmptyXmlResource()

    wx.FileSystem.AddHandler(wx.MemoryFSHandler())

    test_gui_xrc = '''\
<?xml version="1.0" ?><resource class="">
  <object class="wxFrame" name="fpb_frame">
    <object class="wxBoxSizer">
      <object class="sizeritem">
        <object class="wxScrolledWindow" name="scrwin">
          <object class="wxBoxSizer">
            <orient>wxVERTICAL</orient>
            <object class="sizeritem">
              <object class="odemis.gui.comp.foldpanelbar.FoldPanelBar" name="fpb">
                <object class="odemis.gui.comp.foldpanelbar.FoldPanelItem" name="panel_1">
                  <object class="wxStaticText">
                    <label>LABEL</label>
                  </object>
                  <object class="wxStaticText">
                    <label>LABEL</label>
                  </object>
                  <label>Test Panel 1</label>
                  <bg>#1E90FF</bg>
                  <font>
                    <size>13</size>
                    <style>normal</style>
                    <weight>normal</weight>
                    <underlined>0</underlined>
                    <family>default</family>
                    <face>Ubuntu</face>
                    <encoding>UTF-8</encoding>
                  </font>
                  <XRCED>
                    <assign_var>1</assign_var>
                  </XRCED>
                </object>
                <object class="odemis.gui.comp.foldpanelbar.FoldPanelItem" name="panel_2">
                  <object class="wxStaticText">
                    <label>LABEL</label>
                  </object>
                  <object class="wxStaticText">
                    <label>LABEL</label>
                  </object>
                  <object class="wxStaticText">
                    <label>LABEL</label>
                  </object>
                  <object class="wxStaticText">
                    <label>LABEL</label>
                  </object>
                  <object class="wxStaticText">
                    <label>LABEL</label>
                  </object>
                  <object class="wxStaticText">
                    <label>LABEL</label>
                  </object>
                  <object class="wxStaticText">
                    <label>LABEL</label>
                  </object>
                  <object class="wxStaticText">
                    <label>LABEL</label>
                  </object>
                  <object class="wxStaticText">
                    <label>LABEL</label>
                  </object>
                  <object class="wxStaticText">
                    <label>LABEL</label>
                  </object>
                  <label>Test Panel 2</label>
                  <collapsed>1</collapsed>
                  <bg>#A9D25E</bg>
                  <XRCED>
                    <assign_var>1</assign_var>
                  </XRCED>
                </object>
                <object class="odemis.gui.comp.foldpanelbar.FoldPanelItem" name="panel_3">
                  <object class="wxStaticText">
                    <label>LABEL</label>
                  </object>
                  <object class="wxStaticText">
                    <label>LABEL</label>
                  </object>
                  <object class="wxStaticText">
                    <label>LABEL</label>
                  </object>
                  <object class="wxStaticText">
                    <label>LABEL</label>
                  </object>
                  <object class="wxStaticText">
                    <label>LABEL</label>
                  </object>
                  <object class="wxStaticText">
                    <label>LABEL</label>
                  </object>
                  <label>Test Panel 3</label>
                  <bg>#D08261</bg>
                  <XRCED>
                    <assign_var>1</assign_var>
                  </XRCED>
                </object>
                <spacing>0</spacing>
                <bg>#4D4D4D</bg>
                <XRCED>
                  <assign_var>1</assign_var>
                </XRCED>
              </object>
              <flag>wxEXPAND</flag>
            </object>
          </object>
          <bg>#A52A2A</bg>
          <XRCED>
            <assign_var>1</assign_var>
          </XRCED>
        </object>
        <option>1</option>
        <flag>wxEXPAND</flag>
        <minsize>100,100</minsize>
      </object>
      <orient>wxVERTICAL</orient>
    </object>
    <title>Fold Panel Bar Test Frame</title>
  </object>
  <object class="wxFrame" name="stream_frame">
    <object class="wxBoxSizer">
      <orient>wxVERTICAL</orient>
      <object class="sizeritem">
        <object class="wxScrolledWindow" name="scrwin">
          <object class="wxBoxSizer">
            <orient>wxVERTICAL</orient>
            <object class="sizeritem">
              <object class="odemis.gui.comp.foldpanelbar.FoldPanelBar" name="fpb">
                <object class="odemis.gui.comp.foldpanelbar.FoldPanelItem">
                  <object class="wxPanel" name="test_panel">
                    <object class="wxBoxSizer">
                      <orient>wxVERTICAL</orient>
                      <object class="sizeritem">
                        <object class="odemis.gui.comp.stream.FixedStreamPanel" name="fsp_1">
                          <label>Fixed Stream panel</label>
                          <collapsed>1</collapsed>
                          <fg>#FFFFFF</fg>
                          <bg>#4D4D4D</bg>
                          <font>
                            <size>9</size>
                            <style>normal</style>
                            <weight>normal</weight>
                            <underlined>0</underlined>
                            <family>default</family>
                            <face>Ubuntu</face>
                            <encoding>UTF-8</encoding>
                          </font>
                          <XRCED>
                            <assign_var>1</assign_var>
                          </XRCED>
                        </object>
                        <flag>wxBOTTOM|wxEXPAND</flag>
                        <border>1</border>
                      </object>
                      <object class="sizeritem">
                        <object class="odemis.gui.comp.stream.FixedStreamPanel" name="fsp_2">
                          <label>Fixed Stream panel</label>
                          <fg>#FFFFFF</fg>
                          <bg>#4D4D4D</bg>
                          <font>
                            <size>9</size>
                            <style>normal</style>
                            <weight>normal</weight>
                            <underlined>0</underlined>
                            <family>default</family>
                            <face>Ubuntu</face>
                            <encoding>UTF-8</encoding>
                          </font>
                          <XRCED>
                            <assign_var>1</assign_var>
                          </XRCED>
                        </object>
                        <flag>wxBOTTOM|wxEXPAND</flag>
                        <border>1</border>
                      </object>
                      <object class="sizeritem">
                        <object class="odemis.gui.comp.stream.FixedStreamPanel" name="fsp_3">
                          <label>Fixed Stream panel</label>
                          <collapsed>1</collapsed>
                          <fg>#FFFFFF</fg>
                          <bg>#4D4D4D</bg>
                          <font>
                            <size>9</size>
                            <style>normal</style>
                            <weight>normal</weight>
                            <underlined>0</underlined>
                            <family>default</family>
                            <face>Ubuntu</face>
                            <encoding>UTF-8</encoding>
                          </font>
                          <XRCED>
                            <assign_var>1</assign_var>
                          </XRCED>
                        </object>
                        <flag>wxBOTTOM|wxEXPAND</flag>
                        <border>1</border>
                      </object>
                      <object class="sizeritem">
                        <object class="odemis.gui.comp.stream.CustomStreamPanel" name="csp_1">
                          <label>Custom Stream panel</label>
                          <collapsed>1</collapsed>
                          <fg>#FFFFFF</fg>
                          <bg>#4D4D4D</bg>
                          <font>
                            <size>9</size>
                            <style>normal</style>
                            <weight>normal</weight>
                            <underlined>0</underlined>
                            <family>default</family>
                            <face>Ubuntu</face>
                            <encoding>UTF-8</encoding>
                          </font>
                          <XRCED>
                            <assign_var>1</assign_var>
                          </XRCED>
                        </object>
                        <flag>wxBOTTOM|wxEXPAND</flag>
                        <border>1</border>
                      </object>
                      <object class="sizeritem">
                        <object class="odemis.gui.comp.stream.CustomStreamPanel" name="csp_2">
                          <label>Custom Stream panel</label>
                          <collapsed>1</collapsed>
                          <fg>#FFFFFF</fg>
                          <bg>#4D4D4D</bg>
                          <font>
                            <size>9</size>
                            <style>normal</style>
                            <weight>normal</weight>
                            <underlined>0</underlined>
                            <family>default</family>
                            <face>Ubuntu</face>
                            <encoding>UTF-8</encoding>
                          </font>
                          <XRCED>
                            <assign_var>1</assign_var>
                          </XRCED>
                        </object>
                        <flag>wxBOTTOM|wxEXPAND</flag>
                        <border>1</border>
                      </object>
                      <object class="sizeritem">
                        <object class="odemis.gui.comp.stream.CustomStreamPanel" name="csp_3">
                          <label>Custom Stream panel</label>
                          <collapsed>1</collapsed>
                          <fg>#FFFFFF</fg>
                          <bg>#4D4D4D</bg>
                          <font>
                            <size>9</size>
                            <style>normal</style>
                            <weight>normal</weight>
                            <underlined>0</underlined>
                            <family>default</family>
                            <face>Ubuntu</face>
                            <encoding>UTF-8</encoding>
                          </font>
                          <XRCED>
                            <assign_var>1</assign_var>
                          </XRCED>
                        </object>
                        <flag>wxBOTTOM|wxEXPAND</flag>
                        <border>1</border>
                      </object>
                      <object class="sizeritem">
                        <object class="odemis.gui.comp.buttons.PopupImageButton" name="">
                          <bitmap>___img_stream_add_png</bitmap>
                          <hover>___img_stream_add_h_png</hover>
                          <bitmap>___img_stream_add_png</bitmap>
                        </object>
                      </object>
                    </object>
                    <bg>#333333</bg>
                  </object>
                  <label>STREAMS</label>
                  <XRCED>
                    <assign_var>1</assign_var>
                  </XRCED>
                </object>
                <spacing>0</spacing>
                <leftspacing>0</leftspacing>
                <rightspacing>0</rightspacing>
                <bg>#4D4D4D</bg>
                <XRCED>
                  <assign_var>1</assign_var>
                </XRCED>
              </object>
              <flag>wxEXPAND</flag>
            </object>
          </object>
          <bg>#A52A2A</bg>
          <XRCED>
            <assign_var>1</assign_var>
          </XRCED>
        </object>
        <option>1</option>
        <flag>wxEXPAND</flag>
        <minsize>400,400</minsize>
      </object>
    </object>
    <size>400,400</size>
    <title>Stream panel test frame</title>
  </object>
</resource>'''

    ___img_stream_add_png = '''\
\x89PNG\x0d
\x1a
\x00\x00\x00\x0dIHDR\x00\x00\x00v\x00\x00\x00\x1f\x08\x06\x00\x00\x002\
\\9\x83\x00\x00\x00\x01sRGB\x00\xae\xce\x1c\xe9\x00\x00\x00\x06bKGD\x00\
\x00\x00\x00\x00\x00\xf9C\xbb\x00\x00\x00\x09pHYs\x00\x00\x0b\x13\x00\x00\
\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x07tIME\x07\xdc\x06\x14\x0c\x09\
,\x13\x13mR\x00\x00\x02\xf6IDATh\xde\xed\x96KhTg\x14\xc7\xb1\xc6d5\x84\
6\x98\x84`+.Bv\xc1\x80H7\xffB6\xa5\x81,J\x09}\x05\xb11UW\xb5\x01\x17\xb6\
M\x88\xf4AP\xaa\x90E\x91.D\xe8"\x8b\xb6\xb4\x85n\xb2\xa8\x05\x0f\xd2 \x06\
[\x14e\xd0T)\x96\x9aLCK#-\xd1H\xc7E\xcf\x84\xcb0\x8f\x9b\x91\xd8Y\x9c\x1f\
|\xdc{\xcf9\xdfw\xbf\xf3\xf8\x1e\x10\x04A\x10\x04A\x10\x04A\x10\x04A\x10\
\x04\x1bAC\xad\x1d\xb3\xd9l\xbe\xf0\xde\xdd\xdd\xdd\x10\xa1\xac/6\xd7\xda\
1\x97\xcb\xd5\xd4\xcf\xcc\xda\x80_\x80aI\xd3.\xeb\x04\xae\x01\xab^l\x17\
\x81\x0f%\x9dO\xa3/\xf1\x8f\x01\xe0\x18\xb0\x15\xf8\x078
t\x02\x87\x80M@\x0b\xf0\x87\x9b\x8f\x01\xc7}\xec\xbf\x81Y\xe0mIw\xccl;\
p3a\x0bpB\xd2d9_\\\xfe-0/i\xb4h^\xdf\x01\xb3\x92\xc67:\xb1\x9b\xfe\x87b\
:\x08\\\x01\xdeJ\xc8\x1a\x81\xbc\xa4V\xa0\x03\xf8\x14\xf8\xca\xcc\x9eM\xa9\
O\x06o\x0b0\x0d\xecq\xfb\x1e`F\xd2\x07\xfe\xdd\x0b,Kj\xf5\xef\x19\xe0_I\
O\x01;<\x91\xa7\x12C\xae\xd9z\x9b\xac\xe2\x0b\xc0\xd3\xc0\x013\xebH\xcc\
\xab\x0f\xe8\xf3b\xa3\xae\x12\x9b\xcdf\xf3\x85\x96F^"\xe8O\x00#\xc0\xeb\
@\xa7\x99\xf5\x14\xdbH\xba/\xe9k`\x12xo\xbdz\xa0\x09h.\xac2IJ\xfa-\x8d\
\x92\x1exQ\xecJ\xb1\xf3T\xf2\xa5\xd3\xc79\x9c\x90\x8d\x01\xa7\x81\xb6\xba\
Kl.\x97[ki\xe4%x\x01\xf8Y\xd2u\xe03\xe0\xcd
\xb6\xe7\x80\x9d\xeb\xd5K\xba\xeb[\xef%3\x9b2\xb3\xaeu\x1c\x13[\x80\x97\
}\x15\x16\xc8\x98\xd9B\xa2m\xab\xe4\x8b\x995\x02O\xfa\x1c^3\xb3\x8c\x99\
\xf5zB\xcf\xd4eb\x17\x17\x17\xd7Z\x1ay\x09\xf6z%\xe3\xcfW<\x98\xb5^\xee\
\x1a\xca\xac\xbc\x8f<\xe9w\x81\x1f\xcc\xec\x8d*\xe3d\xccl\x01X\x06\x9e\x07\
\xf6\x15m\xc5\xed\x89v\xbb\x8a/\x19`E\xd2\xaf\xc0\x97\xbe\xaaG\x81\x93\xc0\
\x92\xeb\xeb\xeb\xf2488\xd8\x90\xa8\xee|)y\x85\xd5\xd0\x02\xf4\x03\xbb\xcd\
\xec\xddB@]\xf6S\x89.\xcf\x01?V\x18\xb2\xa2^\xd2-`\xcc\xcc\x0c\xf8\xc4W\
K9\x96%\xb5\xfb\x99\xfd\xb9_\xb8j\xf5e\x0e\xb8\xef\xb2)\xe0{/\xc0\x11\xbf\
\x1f4\xd7\xf5\xad\xb8\x06^\x02\xceJ\x1aH\x04\xe8\x080\x94L\xacW}?\xf0\x0e\
\xf0b\x99\xed\xb2\x9a\xbe\x17\xb8 )\x0f<\x03\xfc\x95\xf2\x8c\x9d5\xb3o\xfc\
F\xbd\xffQ}\x914\xef\x85uU\xd2\xbd\xff^i\xaa\xeb\xc4\xa6\xd8v\x8by\xd5\xcf\
\xa2$_\x00\x13\xc0\xb8\x07\xe7w`\x05\xb8\x0c\xf4K\x9as\xbb\xd5*\xfa$\x1d\
\xc0\xc7@\x97\xef*Y`x\x1d\xf3\x9c\x00n\x98\xd9I\xffW\xc6\xcc\x96\x12\xfa\
B\xe2\xca\xf9\xf2~Q\xb1\x0c\x15\xd95\x13\x04A\x10\x04A\x10\x04A\x10\x04\
A\x10\x04A\x10\x04\x8f\x81\x87!\xfem\xd4\x80\x9e\x97\xd0\x00\x00\x00\x00\
IEND\xaeB`\x82'''

    ___img_stream_add_h_png = '''\
\x89PNG\x0d
\x1a
\x00\x00\x00\x0dIHDR\x00\x00\x00v\x00\x00\x00\x1f\x08\x06\x00\x00\x002\
\\9\x83\x00\x00\x00\x01sRGB\x00\xae\xce\x1c\xe9\x00\x00\x00\x06bKGD\x00\
\xc2\x00\xc2\x00\xc2\x8d\xd7\xe1v\x00\x00\x00\x09pHYs\x00\x00\x0b\x13\x00\
\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x07tIME\x07\xdc\x06\x14\x0c\
\x18\x11\x18\xa2\x02S\x00\x00\x06\x06IDATh\xde\xed\x9bkH[g\x18\xc7\xff\x27\
Ws\xa2\xb66\xab\xda\x1a7\xe6\x073\xc1\xce\xcdHe\xb56\xe0\xadQ\x06\xa6\xdd\
d\xd5i\xa0 \xd3vma\xe2\xd8\x9aN\xa8\x8cahp\xad(\xa5\xc2V\x98\x1f
\xed,Z5\x9dK\x8atPoi\xec
-M\xd7\x19\x99d\xa1\xf1\x12M\x8a\xcb\x1as\xdb\x87$.\xb8\x18c\xa0\xce\xc8\
\xf9\xc1\x0b9\xef\xf3\x9e\xe4<\xcf?\xef\xe5\x9c\xe7=\x04\xc2\x83\x06`\x17\
\x80\x14_\xe1\x01`\xfb\xea)^\x1dn\x00v\x00f\x00F_Y\xf0\xd5\x87\x84X\xc7\
\xce\x02\x90\x01 \x97\x8a\xf1\x96b\x1c\x80\x0e\xc0r$\xc2\xa6\x01(\xa2b\xb8\
\xa5\xb9\x03`*\x98\x81\xbe\xc6\xb0{\x08\xc0~*n[\x9e4\x00\xb1\x00\x0c\x00\
<\xa1\x84\xa5\x01\x10\xfbN\xa0\x88\x0e^\x03\x90\x08@\x1f(\xeeja\x0fQ\xa2\
F%\xf1\x00\xb8\x00\xa6\x83\x09\x9bF\x0d\xbfQ\xdfs\x17}e\xe5v\x85E-\x94\xb6\
\x05E>-W\x84\xcd\xa0b\xb2m\xc8\xf0\x0bK\xa3\xeeS\xb7\x15\xb9\x00h\x0cx\x9f\
(m\x1c\x03:W>\xa7\xa2\x8e\x8a\xe7\x96b\x17\x03\xdeG\x84\x1b\xc7\x18\xd9\
/\xa6\xa7\xa7\xc7wvv\xb6\xf4\xf6\xf6\xfe\xd0\xd6\xd6\xa6\x01\x80\xcc\xcc\
\xcc\x9dmmm\xcdn\xb7\xdbE\x10\x04\xe6\xe7\xe7\xff\xe8\xee\xee\xbe\xdd\xdd\
\xdd=\x19\x8e}5\xb5\xb5\xb5oK$\x92\xa3l6;\xde\xe5r-\x0f\x0d\x0d\xf5\xf3\
x\xbc\x9d\xd9\xd9\xd9\x85\x04A\x10,\x16\x8bc\xb7\xdbm\x00p\xf7\xee\xdd\xde\
\xc2\xc2\xc2\x0f\xdcn\xb7\xcb\xe9t.\xcf\xcc\xcc\xe8\xe5r\xf9\x0d\x9dNg\x15
\x85\xbc\x8b\x17/~\xe3o\x0b\x00\xf7\xef\xdfW\xcbd\xb2\x9f\xd6\xf2\x05\x00\
\xae]\xbb\xf6\xa9\xd9l\x9e;}\xfa\xf4\x8d\xc0\xeb\xba~\xfd\xfag\x06\x83a\
\xaa\xb1\xb1\xf1\xd6+\x166%ra#\xa4\xb6\xb6\xf6\x90\xc5b1\x8aD\xa2\x020\
\xd8l6\x1d\x80\xa7\xb8\xb8\xb8\x81$I\x86T*\xddWWWW\xefr\xb9.\xf7\xf4\xf4\
L\xadg\x0f\xfc~\x92$\x19UUU\xb5\xad\xad\xad\xadJ\xa5r:55\x95\x8c\x8b\x8b\
c=y\xf2\xc4\x02@)\x14
y\x17.\\h*..n\x00\x00\xa1P\xc8+((8ZTT\xd4\xc0f\xb3ir\xb9\xbc\xfc\xdc\xb9\
s\x1fWWW_\x06\x00\x87\xc3\xf1\xd2\xdf6\x1c_\x00 66vWrrrFFF\xc6\xcf:\x9d\
\xce
\x00UUUo\xed\xd9\xb3G`\xb1X\xe66!\xcc)4x\x1f\xe8\x87?\xfc\xfaK8\xf5\xab\
`2\x99\xb4\xac\xac\xac\x83
\x85\xe2{.\x97\xbb\xb3\xa4\xa4\x84\xbf\xba\x8d\xcdfs^\xb9r\xe5\xd7\xe1\
\xe1\xe1\xc1\x8a\x8a\x8a\xb2\x8d\xdaccc\x194\x1a\x8d977\xf7\x17\x00\x18\
\x0c\x06\x9bO\xd4u\xb1\xdb\xed\xee\x81\x81\x01\xcd\xee\xdd\xbb\xdfX\xaf\
m(_8\x1cN\xc2\xe4\xe4\xa4\xe6\xc4\x89\x13%\xfe:\x89DR\xf6\xf4\xe9\xd3a.\
\x97\x1b\xbf\x09\xc2\xf2h\xf0fi\xc2\x1f~\x8dA\x86\xe1\xb5\xeaW!\x95J3_\xbc\
x17222\xf3\xf8\xf1\xe31\x89D\x92\xbfV\xdb\xf1\xf1\xf1g<\x1e/u\xa3\xf6\xd9\
\xd9\xd9\x97\xa3\xa3\xa3\xfd---_utt|t\xe0\xc0\x81\xa4p\xdd#I\x92QVV\x96\
\xb3\xb8\xb8h\x0c\x100F\xa5R)\xfc%+++!\x94/\x1c\x0e\x87\xcef\xb3\xc9\xf6\
\xf6\xf6~\x81@\xb0?999\xa6\xb4\xb4\xf4u\x0e\x87\x13?888B\x92d\xdc&\x08\xcb\
f\xc0\x9b\x16\xe2\x84\xd9c\x11\xb0`
^\x1f\x02\x91H\xf4\xde\x83\x07\x0f4\x00000\xa0\x91\xc9d\x8d$I\xfe\x18\xe2\
\x94\xf5\xb2OA\xedg\xcf\x9e\xbd\x9d\x93\x93\xa3\xa9\xac\xac\xccknn\xfeB\
\xa5Ru+\x14\x8a\x91\x10\xbd/F\xa5R)\x98L&i\xb1X\x8cMMM\x97\xfd6\x87\xc3\
\xf1\xb2\xa4\xa4\xe4\xf3p}ILLd;\x9dN\xe7\xa3G\x8f\x16\xf5z\xfd\xc4\xc9\x93\
\x27\x0f\xf2\xf9\xfc\xd7\xef\xdd\xbb\xa76\x99LKL&\x93\xb3\x09\xc2\xda\x19\
\xf0\xe6\xfa\xf8a5\xaf\x08X\xfd\x8e\x05\x0c\xbb\x15\xeb\xaf\x8aSRRH>\x9f\
\xbf/))\xe9M\x91HT\xea\x0fhMMM\xa6V\xab\xfd\xcf_#777\xddl6\xaf\xf9\x97Y\
\xcf\xae\xd5j\xe7\xb5Z\xed-\xa9T\xfa\xfb\xb1c\xc7*C\x09\xeb\x17\xef\xc8\
\x91#i\xf5\xf5\xf5\x9fX\xad\xd6\xe5H}\x19\x19\x19\x99\xf6x<N\x00\xe8\xea\
\xea\x1a:\xfe|\x03A\x108s\xe6L\x97@ \xd8A\xa7\xd3\x99\x9b \xac\x99\x16\
\xf9\xfavcTWW\xbfk2\x99t\x87\x0f\x1f\xfeR,\x16\xcb\xc4b\xb1lxx\xb8////w\
\xf5pXWW\xf7N^^\x9e\xf8\xe6\xcd\x9b\xb7\x83\x0d\x97\xeb\xd9\xcb\xcb\xcb\
\xd3\x08\x82 \x00`\xef\xde\xbd\xbc\xe5\xe5\xe5\xbf\xc3\xb9\xc6\x9e\x9e\x9e\
)\xbd^\xff\xb0\xa9\xa9\xe9h\xa4\xbe\xb0X\xac\x95\xcd\x07ccc\xb3\xcf\x9f\
?611\xf1\xcb\xd2\xd2\x92\x13\x00\xe8t:c\x13\xc2mdD,\xacac\xcd\xb3\xb3\xb3\
\xf7k4\x9a\xd1\xc0\xba\xbe\xbe\xbe\x09\xb9\\\xfe>\x97\xcb\xed\x03\x00\xb5\
Z\xdd\xeav\xbb\x1df\xb3\xd9x\xe9\xd2\xa5v\xa5R9\xed[\xd4\xb8B\xd9\x03\x11\
\x08\x04;jjj><u\xeaT\xa2\xc7\xe3\x81\xd5j5uttt\x85{\x9dr\xb9\xbc\xff\xea\
\xd5\xab_\xe7\xe7\xe7\xdf\xb1\xd9l\x0e&\x93\x19\xa3V\xab\xbf\xf5\xdb\x17\
\x16\x16\x0c\x00\xb0\x96/\x09\x09\x09\xca\xc0\xfa\xe3\xc7\x8f_\x0d<\xa6\
\xd1h\x9b\xd1c\x8d\x84\xef\xc9S-uO\xbf\xad\xf8\x8e\x0eo\x0e\xcf\x19\xf6\
<K\xb1\xd5\x19\x07`\xf2\xcf\x07:*\x1e\xdb\x06\x1d\xf0o>\xd6\x05o\x1e\x8f\
J\xb2G7w\x00\xcc\x07
\x0b\x9f\xb0\xb1\xf0&l)\xa2\x8f\xdf\x00<\xf4\x1f\xd0\x83\xacu\x13\xe1\xdd\
jA\x11=\xfc\x09`\x08!\xf6<y\xe0\xdd\x14\xc5\xa5znT\xf5\xd4!\xac\xdaD\x1e\
l\xfb\xa9\x07\xdeMQ\xd4\x9c\x1b\x1ds\xeaC\xac\xdaz
Po\x02D\xf3-M\xc4o\x02\x04B\xbd\xbb\xf3\xff\x10\xf1\xbb;\x14\x14\x14\xd1\
\xc4?,\xfa\xa4\x9d\xe4_\x198\x00\x00\x00\x00IEND\xaeB`\x82'''

    wx.MemoryFSHandler.AddFile('XRC/test_gui/test_gui_xrc', test_gui_xrc)
    wx.MemoryFSHandler.AddFile('XRC/test_gui/___img_stream_add_png', ___img_stream_add_png)
    wx.MemoryFSHandler.AddFile('XRC/test_gui/___img_stream_add_h_png', ___img_stream_add_h_png)
    __res.Load('memory:XRC/test_gui/test_gui_xrc')

