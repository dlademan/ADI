import wx


class MessageDialog(wx.Frame):

    def __init__(self, parent=None, id=wx.ID_ANY,
                 title="Test Message Dialog",
                 message="Test Message"):

        wx.Frame.__init__(self, parent, id, title,
                          wx.DefaultPosition,
                          size=(350, 180),
                          style=wx.SYSTEM_MENU | wx.CLIP_CHILDREN | wx.FRAME_NO_TASKBAR | wx.FRAME_FLOAT_ON_PARENT)
        icon = wx.Icon()
        icon.CopyFromBitmap(wx.Bitmap("icons/adi_logo.png", wx.BITMAP_TYPE_ANY))
        self.SetIcon(icon)

        PAD = 20
        self.parent = parent

        self.make_modal()
        self.panel = wx.Panel(self)
        self.Bind(wx.EVT_CLOSE, self.on_close)

        ####################

        self.text_message = wx.StaticText(self.panel, label=message)
        font_message = wx.Font(wx.FontInfo(12))
        self.text_message.SetFont(font_message)

        ####################

        box_vert = wx.BoxSizer(wx.VERTICAL)
        box_vert.Add(0, PAD, 0)
        box_vert.Add(self.text_message, 1, wx.EXPAND)
        # box_vert.Add(1, 20)
        # box_vert.Add(box_button, 1, wx.EXPAND)
        box_vert.Add(0, PAD, 0)

        ####################

        box_main = wx.BoxSizer()
        box_main.Add(PAD, 0, 0, 0)
        box_main.Add(box_vert, 1, 0, 0)
        box_main.Add(PAD, 0, 0, 0)

        self.panel.SetSizer(box_main)
        self.panel.Fit()
        self.Fit()
        w, h = self.GetSize().Get()
        self.SetSize((300, h))
        self.Center()
        self.Show()

    def on_close(self, event=None):
        if hasattr(self, '_disabler'):
            del self._disabler
        self.Destroy()

    def make_modal(self, modal=True):

        if modal and not hasattr(self, '_disabler'):
            self._disabler = wx.WindowDisabler(self)
        if not modal and hasattr(self, '_disabler'):
            del self._disabler
