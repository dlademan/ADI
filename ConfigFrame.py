import wx, logging
from pathlib import Path


class ConfigFrame(wx.Frame):
    """frame for settings window"""

    instance = None
    init = False

    def __new__(self, *args, **kwargs):
        if self.instance is None:
            self.instance = wx.Frame.__new__(self)
        elif not self.instance:
            self.instance = wx.Frame.__new__(self)
        return self.instance

    def __init__(self, parent=None, id=wx.ID_PREFERENCES, title="ADI Settings"):
        if self.init:
            logging.warning("Settings window already shown")
            return
        logging.debug("Settings window opened")
        self.init = True
        wx.Frame.__init__(self, parent, id, title, wx.DefaultPosition, wx.Size(600, 130), style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)

        self.parent = parent
        self.initpanel()
        self.Show()
        self.parent = parent

    def initpanel(self):
        self.panel = wx.Panel(self)

        treeRootText = wx.StaticText(self.panel, label='Zips Location')
        self.archivePicker = wx.DirPickerCtrl(self.panel, path=str(self.parent.config.archive))
        self.archivePicker.Bind(wx.EVT_DIRPICKER_CHANGED, self.updateConfig)

        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(10, 0, 0)
        hbox1.Add(treeRootText, 0, wx.EXPAND, 5)
        hbox1.Add(10, 0, 0)
        hbox1.Add(self.archivePicker, 3, wx.EXPAND, 5)
        hbox1.Add(10, 0, 0)

        libraryRootText = wx.StaticText(self.panel, label='DAZ Library')
        self.libraryPicker = wx.DirPickerCtrl(self.panel, path=str(self.parent.config.library))
        self.libraryPicker.SetTextCtrlGrowable(True)
        self.libraryPicker.Bind(wx.EVT_DIRPICKER_CHANGED, self.updateConfig)

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2.Add(10, 0, 0)
        hbox2.Add(libraryRootText, 0, wx.EXPAND, 5)
        hbox2.Add(10, 0, 0)
        hbox2.Add(self.libraryPicker, 3, wx.EXPAND, 5)
        hbox2.Add(10, 0, 0)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(0, 20, 0)
        vbox.Add(hbox1, 0, wx.EXPAND, 5)
        vbox.Add(hbox2, 0, wx.EXPAND, 5)
        vbox.Add(0, 20, 0)

        self.panel.SetSizer(vbox)

    def updateConfig(self, event):
        archive = Path(self.archivePicker.GetPath())
        library = Path(self.libraryPicker.GetPath())

        self.parent.config.saveConfig(archive, library)
