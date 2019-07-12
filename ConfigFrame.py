import wx
import logging
from pathlib import Path


class ConfigFrame(wx.Frame):

    instance = None
    init = False

    def __new__(self, *args, **kwargs):
        if self.instance is None:
            self.instance = wx.Frame.__new__(self)
        elif not self.instance:
            self.instance = wx.Frame.__new__(self)
        return self.instance

    def __init__(self, parent=None):
        if self.init:
            logging.warning("Configuration window already shown")
            return
        wx.Frame.__init__(self, parent, -1,
                          "ADI Configuration",
                          wx.DefaultPosition,
                          size=(600, 250),
                          style=wx.SYSTEM_MENU |
                                wx.CLIP_CHILDREN)

        PADDING = 20
        SPACING = 10

        icon = wx.Icon()
        icon.CopyFromBitmap(wx.Bitmap("icons/adi_logo.png", wx.BITMAP_TYPE_ANY))
        self.SetIcon(icon)

        self.make_modal()
        self.parent = parent
        self.panel = wx.Panel(self)
        self.Bind(wx.EVT_CLOSE, self.on_close)

        text_title = wx.StaticText(self.panel, label='Configuration')
        font_title = wx.Font(wx.FontInfo(16))
        text_title.SetFont(font_title)

        text_archive = wx.StaticText(self.panel, label='Zip Archive')
        self.picker_archive = wx.DirPickerCtrl(self.panel, path=str(parent.config.archive))

        box_archive = wx.BoxSizer(wx.HORIZONTAL)
        box_archive.Add(text_archive, 0, wx.EXPAND, 5)
        box_archive.Add(10, 0, 0)
        box_archive.Add(self.picker_archive, 3, wx.EXPAND, 5)

        text_library = wx.StaticText(self.panel, label='DAZ Library')
        self.picker_library = wx.DirPickerCtrl(self.panel, path=str(parent.config.library))
        self.picker_library.SetTextCtrlGrowable(True)

        box_library = wx.BoxSizer(wx.HORIZONTAL)
        box_library.Add(text_library, 0, wx.EXPAND, 5)
        box_library.Add(8, 0, 0)
        box_library.Add(self.picker_library, 3, wx.EXPAND, 5)

        self.checkbox_clear_queue = wx.CheckBox(self.panel, label='Clear queue on program close')
        self.checkbox_clear_queue.SetValue(self.parent.config.clear_queue)

        box_clear = wx.BoxSizer(wx.HORIZONTAL)
        box_clear.Add(self.checkbox_clear_queue, 0, wx.EXPAND, 5)

        self.checkbox_expand_tree = wx.CheckBox(self.panel, label='Expand tree fully on start')
        self.checkbox_expand_tree.SetValue(self.parent.config.expand)

        box_expand = wx.BoxSizer(wx.HORIZONTAL)
        box_expand.Add(self.checkbox_expand_tree, 0, wx.EXPAND, 5)

        self.checkbox_close_queue = wx.CheckBox(self.panel, label='Close queue dialog upon completion')
        self.checkbox_close_queue.SetValue(self.parent.config.close_dialog)

        box_close_queue = wx.BoxSizer(wx.HORIZONTAL)
        box_close_queue.Add(self.checkbox_close_queue, 0, wx.EXPAND, 5)

        cancelButton = wx.Button(self.panel, label='Close', size=wx.DefaultSize)
        cancelButton.Bind(wx.EVT_BUTTON, self.on_close)

        acceptButton = wx.Button(self.panel, label='Save', size=wx.DefaultSize)
        acceptButton.Bind(wx.EVT_BUTTON, self.save_close)

        box_buttons = wx.BoxSizer(wx.HORIZONTAL)
        box_buttons.Add((0, 0), 1, wx.EXPAND)
        box_buttons.Add(acceptButton, 0, wx.EXPAND, 20)
        box_buttons.Add(SPACING, 0, 0)
        box_buttons.Add(cancelButton, 0, wx.EXPAND, 20)
        box_buttons.Add((0, 0), 1, wx.EXPAND)

        box_vert = wx.BoxSizer(wx.VERTICAL)
        box_vert.Add(0, PADDING, 0)
        box_vert.Add(text_title, 0, wx.EXPAND, 20)
        box_vert.Add(0, SPACING, 0)
        box_vert.Add(box_archive, 0, wx.EXPAND, 20)
        box_vert.Add(0, SPACING, 0)
        box_vert.Add(box_library, 0, wx.EXPAND, 20)
        box_vert.Add(0, SPACING, 0)
        box_vert.Add(box_clear, 0, wx.EXPAND, 20)
        box_vert.Add(0, SPACING, 0)
        box_vert.Add(box_expand, 0, wx.EXPAND, 20)
        box_vert.Add(0, SPACING, 0)
        box_vert.Add(box_close_queue, 0, wx.EXPAND, 20)
        box_vert.Add(0, SPACING, 0)
        box_vert.Add(box_buttons, 0, wx.EXPAND, 20)
        box_vert.Add(0, PADDING, 0)

        box_main = wx.BoxSizer(wx.HORIZONTAL)
        box_main.Add(50, 0, 0)
        box_main.Add(box_vert, 1, wx.EXPAND, 20)
        box_main.Add(50, 0, 0)

        self.panel.SetSizer(box_main)
        self.panel.Fit()
        self.Fit()
        w, h = self.GetSize().Get()
        self.SetSize((650, h))

        self.Center()
        self.Show()

    def save_close(self, event):
        self.parent.config.archive = Path(self.picker_archive.GetPath())
        self.parent.config.library = Path(self.picker_library.GetPath())
        self.parent.config.clear_queue = self.checkbox_clear_queue.GetValue()
        self.parent.config.expand = self.checkbox_expand_tree.GetValue()
        self.parent.config.win_size = self.parent.GetSize()
        self.parent.config.close_dialog = self.checkbox_close_queue.GetValue()

        if self.parent.config.first:
            self.parent.show_main()
        self.parent.config.first = False

        self.parent.config.save_config()
        self.on_close(event)
        self.parent.on_refresh()

    def on_close(self, event=None):
        if hasattr(self, '_disabler'):
            logging.info("Deleting Config Disabler")
            del self._disabler
        logging.info("Closing Settings Frame")
        self.Destroy()

    def make_modal(self, modal=True):
        if modal and not hasattr(self, '_disabler'):
            self._disabler = wx.WindowDisabler(self)
        if not modal and hasattr(self, '_disabler'):
            del self._disabler
