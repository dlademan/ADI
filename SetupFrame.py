import wx
import logging
from pathlib import Path

class SetupFrame(wx.Frame):

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
        wx.Frame.__init__(self, parent, -1, "ADI Configuration", wx.DefaultPosition, (600, 250),
                          style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)
        # self.Bind(wx.EVT_CLOSE, self.OnClose)

        self.parent = parent

        self.panel = wx.Panel(self)

        titleText = wx.StaticText(self.panel, label='Configuration')
        titleFont = wx.Font(wx.FontInfo(16))
        titleText.SetFont(titleFont)

        archiveRootText = wx.StaticText(self.panel, label='Archive')
        self.archivePicker = wx.DirPickerCtrl(self.panel, path=str(parent.config.archive))

        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(32, 0, 0)
        hbox1.Add(archiveRootText, 0, wx.EXPAND, 5)
        hbox1.Add(10, 0, 0)
        hbox1.Add(self.archivePicker, 3, wx.EXPAND, 5)
        hbox1.Add(10, 0, 0)

        libraryRootText = wx.StaticText(self.panel, label='DAZ Library')
        self.libraryPicker = wx.DirPickerCtrl(self.panel, path=str(parent.config.library))
        self.libraryPicker.SetTextCtrlGrowable(True)

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2.Add(10, 0, 0)
        hbox2.Add(libraryRootText, 0, wx.EXPAND, 5)
        hbox2.Add(10, 0, 0)
        hbox2.Add(self.libraryPicker, 3, wx.EXPAND, 5)
        hbox2.Add(10, 0, 0)

        self.clearQueueBox = wx.CheckBox(self.panel, label='Clear queue on program close')
        self.clearQueueBox.SetValue(self.parent.config.clearQueue)

        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        hbox3.Add(10, 0, 0)
        hbox3.Add(self.clearQueueBox, 0, wx.EXPAND, 5)
        hbox3.Add(10, 0, 0)

        acceptButton = wx.Button(self.panel, label='Save', size=wx.DefaultSize)
        acceptButton.Bind(wx.EVT_BUTTON, self.saveAndClose)

        hbox4 = wx.BoxSizer(wx.HORIZONTAL)
        hbox4.Add((0, 0), 1, wx.EXPAND)
        hbox4.Add(acceptButton, 0, wx.EXPAND, 20)
        hbox4.Add((0, 0), 1, wx.EXPAND)


        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add((0, 0), 1, wx.EXPAND)
        vbox.Add(titleText, 0, wx.EXPAND, 20)
        vbox.Add((0, 0), 1, wx.EXPAND)
        vbox.Add(hbox1, 0, wx.EXPAND, 20)
        vbox.Add((0, 0), 1, wx.EXPAND)
        vbox.Add(hbox2, 0, wx.EXPAND, 20)
        vbox.Add((0, 0), 1, wx.EXPAND)
        vbox.Add(hbox3, 0, wx.EXPAND, 20)
        vbox.Add((0, 0), 1, wx.EXPAND)
        vbox.Add(hbox4, 0, wx.EXPAND, 20)
        vbox.Add((0, 0), 1, wx.EXPAND)

        hboxMain = wx.BoxSizer(wx.HORIZONTAL)
        hboxMain.Add(50, 0, 0)
        hboxMain.Add(vbox, 1, wx.EXPAND, 20)
        hboxMain.Add(50, 0, 0)

        self.panel.SetSizer(hboxMain)

        self.Show()

    def saveAndClose(self, event):
        logging.debug("saveAndClose")

        self.parent.config.archive = Path(self.archivePicker.GetPath())
        self.parent.config.library = Path(self.libraryPicker.GetPath())
        self.parent.config.clearQueue = self.clearQueueBox.GetValue()

        self.parent.config.winSize = self.parent.GetSize()

        logging.debug(self.parent.config.winSize)
        self.parent.config.firstTime = False

        self.parent.config.save()
        self.parent.UpdateLibrary(event)
        self.parent.Show()
        self.Close()

    def OnClose(self, event):
        self.parent.Close()
        event.Skip()
