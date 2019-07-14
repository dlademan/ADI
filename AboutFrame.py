import wx
import wx.lib.agw.hyperlink as hl
import logging


class AboutFrame(wx.Frame):

    instance = None
    init = False

    def __init__(self,
                 parent=None,
                 id=wx.ID_ANY,
                 title="AboutFrame",
                 splash=False):

        if self.init:
            logging.warning("About frame already shown")
            return
        wx.Frame.__init__(self, parent, id, title,
                          wx.DefaultPosition,
                          size=(200, 150),
                          style=wx.SYSTEM_MENU | wx.CLIP_CHILDREN)

        self.parent = parent
        self.panel = wx.Panel(self)
        self.splash = splash
        self.Bind(wx.EVT_CLOSE, self.on_close)

        if not self.splash:
            self.make_modal()

        icon = wx.Icon()
        icon.CopyFromBitmap(wx.Bitmap("icons/adi_logo.png", wx.BITMAP_TYPE_ANY))
        self.SetIcon(icon)

        image_about = wx.Bitmap('icons/about.png', wx.BITMAP_TYPE_PNG)
        size = image_about.GetWidth(), image_about.GetHeight()

        self.bmp = wx.StaticBitmap(parent=self, bitmap=image_about)
        self.bmp.Bind(wx.EVT_LEFT_DOWN, self.on_left)
        self.SetClientSize(size)

        self.panel.Layout()
        self.Center()
        self.Show()

    def __new__(self, *args, **kwargs):
        if self.instance is None:
            self.instance = wx.Frame.__new__(self)
        elif not self.instance:
            self.instance = wx.Frame.__new__(self)
        return self.instance

    def make_modal(self, modal=True):
        if modal and not hasattr(self, '_disabler'):
            self._disabler = wx.WindowDisabler(self)
        if not modal and hasattr(self, '_disabler'):
            del self._disabler

    def on_close(self, event=None):
        if not self.splash:
            try:
                self.make_modal(False)
            except OSError as e:
                logging.error(e)
            self.Close()
        if event is not None:
            event.Skip()

    def on_left(self, event=None):
        self.on_close(event)
