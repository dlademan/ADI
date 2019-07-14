import wx
import logging

class InstallDialog(wx.Frame):

    def __init__(self, parent=None, id=wx.ID_ANY,
                 title="Process Dialog",
                 processes=None):

        wx.Frame.__init__(self, parent, id, title,
                          wx.DefaultPosition,
                          size=(500, 180),
                          style=wx.SYSTEM_MENU | wx.CLIP_CHILDREN | wx.FRAME_NO_TASKBAR | wx.FRAME_FLOAT_ON_PARENT)

        if processes is None:
            processes = ["Installing Test Asset 1",
                         "Uninstalling Test Asset 2",
                         "Uninstalling Test Asset 3",
                         "Uninstalling Test Asset 4",
                         "Uninstalling Test Asset 5"]

        icon = wx.Icon()
        icon.CopyFromBitmap(wx.Bitmap("icons/adi_logo.png", wx.BITMAP_TYPE_ANY))
        self.SetIcon(icon)

        PADDING = 20
        self.make_modal()
        self.parent = parent
        self.panel = wx.Panel(self)
        self.Bind(wx.EVT_CLOSE, self.on_close)

        ####################

        box_vert = wx.BoxSizer(wx.VERTICAL)
        box_vert.Add(0, PADDING, 0)

        self.gauges = []

        for asset in processes:
            # asset = [process, product_name]
            text_process = wx.StaticText(self.panel, label=asset)
            font_process = wx.Font(wx.FontInfo(12))
            text_process.SetFont(font_process)

            self.gauges.append(wx.Gauge(self.panel, size=(20, 30), ))
            self.gauges[-1].SetRange(1)
            self.gauges[-1].Pulse()

            box_asset = wx.BoxSizer(wx.HORIZONTAL)
            box_asset.Add(self.gauges[-1], 1, wx.EXPAND)

            box_vert.Add(text_process, 0, wx.EXPAND)
            box_vert.Add(box_asset, 1, wx.EXPAND)
            box_vert.Add(1, 20)

        ####################

        self.checkbox_close = wx.CheckBox(self.panel, label='Close dialog upon finish')
        self.checkbox_close.SetValue(self.parent.config.close_dialog)
        self.checkbox_close.Bind(wx.EVT_CHECKBOX, self.on_check)

        box_checkbox = wx.BoxSizer()
        box_checkbox.Add((0, 0), 1)
        box_checkbox.Add(self.checkbox_close, 0)
        box_checkbox.Add((0, 0), 1)


        ####################

        self.button_close = wx.Button(self.panel, label="Close")
        self.button_close.Bind(wx.EVT_BUTTON, self.on_close)
        self.button_close.Disable()

        box_button = wx.BoxSizer()
        box_button.Add((0, 0), 1)
        box_button.Add(self.button_close, 0)
        box_button.Add((0, 0), 1)

        ####################

        box_vert.Add(box_checkbox, 1, wx.EXPAND)
        box_vert.Add(box_button, 1, wx.EXPAND)
        box_vert.Add(0, PADDING, 0)

        box_main = wx.BoxSizer()
        box_main.Add(PADDING, 0, 0, 0)
        box_main.Add(box_vert, 1, 0, 0)
        box_main.Add(PADDING, 0, 0, 0)

        self.panel.SetSizer(box_main)
        self.panel.Fit()
        self.Fit()
        w, h = self.GetSize().Get()
        self.SetSize((500, h))


        self.Center()
        self.Show()

    def on_close(self, event=None):
        if hasattr(self, '_disabler'):
            del self._disabler
        self.Destroy()

    def on_check(self, event):
        self.parent.config.close_dialog = self.checkbox_close.GetValue()

    def make_modal(self, modal=True):
        if modal and not hasattr(self, '_disabler'):
            self._disabler = wx.WindowDisabler(self)
        if not modal and hasattr(self, '_disabler'):
            del self._disabler
