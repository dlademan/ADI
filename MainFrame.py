from datetime import datetime
from pathlib import Path
import logging
import subprocess
import wx

from Asset import AssetList
from QueueADI import QueueList
from Config import Config
from SetupFrame import SetupFrame
from OnTree import OnTreeSel, OnTreeContext
from OnList import OnListSel, OnListContext, OnQueueContext
from Tree import FolderTree, ZipTree


class MainFrame(wx.Frame):
    """
    Main frame window of ADI

    parent, id, title
    """

    def __init__(self, parent, id, title):
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
        logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
        logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
        logging.debug("Logging Started")

        wx.Frame.__init__(self, parent, id, title, wx.DefaultPosition, (950, 800), style=wx.DEFAULT_FRAME_STYLE)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self.config = Config(self)
        self.assets = AssetList(self)
        self.queue = QueueList(self)
        if not self.queue.inProgress:
            self.queue = QueueList(self, clear=self.config.clearQueue)

        self.initMenubar()
        self.initToolbar()
        self.initSplitter()

        self.GUIUpdate()

        self.Centre()

        if self.config.firstTime:
            self.setupWindow = SetupFrame(self)
        else:
            self.SetSize(size=self.config.winSize)
            self.Show()

    def SaveCurrentSize(self, event):
        self.config.winSize = self.GetSize()
        self.config.save()

    def OnClose(self, event):
        self.SaveCurrentSize(event)
        event.Skip()

    def OnLeftClick(self, event):
        item = event.GetItem()
        self.zipTree.Expand(item)  # expand item

    def OnListSel(self, event):
        OnListSel(self, event)

    def OnListContext(self, event):
        OnListContext(self, event)

    def OnTreeSel(self, event):
        OnTreeSel(self, event)

    def OnTreeContext(self, event):
        OnTreeContext(self, event)

    def OnQueueContext(self, event):
        OnQueueContext(self, event)

    def InProgressDialog(self):
        pass

    def button1Action(self, event):
        if self.button1.GetLabel() == "Queue Install":
            self.AddToQueue(event, self.selAsset, True)
        elif self.button1.GetLabel() == "Queue Uninstall":
            self.AddToQueue(event, self.selAsset, False)
        else:
            logging.warning("No Action performed on button1 press")

    def button2Action(self, event):
        if self.button2.GetLabel() == "Install":
            self.installAsset(event, self.selAsset)
        elif self.button2.GetLabel() == "Uninstall":
            self.uninstallAsset(event, self.selAsset)
        else:
            logging.warning("No Action performed on button2 press")

    def button3Action(self, event, asset=None):
        if asset is not None:
            self.createPkl(asset)
        else:
            self.createPkl(self.selAsset)

    @staticmethod
    def createPkl(asset):
        asset.createFileList()

    def OnOpenLibrary(self, event, path=None):
        if not path:
            path = self.config.archive
        subprocess.Popen(r'explorer /select, ' + str(path))

    def LaunchAbout(self, event):
        logging.debug("launch about")

    def LaunchSettings(self, event):
        logging.debug("Config window opened")
        self.setupWindow = SetupFrame(self)

    # installation/uninstallation
    def installAsset(self, event, asset):
        logging.debug("Installing " + asset.productName)
        asset.install(self, self.config.library)

        i = self.assets.getIndex(asset)
        self.assets.update(i, True, datetime.now())

        self.GUIUpdate()

    def uninstallAsset(self, event, asset):
        logging.debug("Uninstalling " + asset.productName)
        asset.uninstall(self, self.config.library)

        i = self.assets.getIndex(asset)
        self.assets.update(i, False, None)
        self.GUIUpdate()

    def StartQueue(self, event):
        self.queue.inProgress = True
        self.queue.save()
        self.rightNotebook.SetSelection(1)
        logging.debug("Starting Queued Processes")
        i = 0
        queueLength = 0
        for item in self.queue.list:
            if item.status != 3:
                queueLength += 1
        self.gaugeQueue.SetRange(queueLength)
        self.gaugeQueue.SetValue(0)
        # TODO determine why gaugeQueue is set to max after one iteration
        for i, qItem in enumerate(self.queue.list):
            if self.queue.list[i].status == 3:  # skip finished queue items
                continue
            # ['Queued', 'In Progress', 'Finished', 'Failed']
            self.queue.list[i].status = 1
            self.queue.save()
            self.GUIQueue()

            if qItem.process:
                self.installAsset(event, qItem.asset)
            else:
                self.uninstallAsset(event, qItem.asset)
            self.queue.updateStatus(i, 2)
            self.gaugeQueue.SetValue(i + 1)
            self.GUIQueue()

        self.queue.inProgress = False
        logging.debug("Queued Processes Finished")

    def ClearQueue(self, event):
        self.queueCtrl.DeleteAllItems()
        self.queue = QueueList(self, clear=True)

    def AddToQueue(self, event, asset, process):
        for queueItem in self.queue.list:
            if asset.fileName == queueItem.asset.fileName and queueItem.status == 0:
                logging.warning(asset.productName + " already queued for process, nothing added to queue")
                return

        if process:
            logging.debug("Add " + asset.productName + " to queue to be installed.")
        else:
            logging.debug("Add " + asset.productName + " to queue to be uninstalled.")

        self.queue.append(asset, process)
        self.GUIQueue()

    def GUIUpdate(self):
        self.GUIInstalled()
        self.GUIAssets()
        self.GUIQueue()

    def GUIInstalled(self):
        self.installedCtrl.DeleteAllItems()
        i = 0
        for item in self.assets.list:
            if item.installed:
                self.installedCtrl.InsertItem(i, item.productName)
                self.installedCtrl.SetItem(i, 1, item.zipStr)
                self.installedCtrl.SetItem(i, 2, item.pklStr)
                self.installedCtrl.SetItem(i, 3, item.installedTimeStr)
                i += 1

    def GUIAssets(self):
        self.assetCtrl.DeleteAllItems()
        for i, item in enumerate(self.assets.list):
            self.assetCtrl.InsertItem(i, item.productName)
            self.assetCtrl.SetItem(i, 1, item.zipStr)
            self.assetCtrl.SetItem(i, 2, item.pklStr)
            self.assetCtrl.SetItem(i, 3, item.installedStr)
            self.assetCtrl.SetItem(i, 4, item.size)

    def GUIQueue(self):
        self.queueCtrl.DeleteAllItems()
        for i, item in enumerate(self.queue.list):
            self.queueCtrl.InsertItem(i, item.asset.productName)
            self.queueCtrl.SetItem(i, 1, item.processStr)
            self.queueCtrl.SetItem(i, 2, item.asset.installedStr)
            self.queueCtrl.SetItem(i, 3, item.statusStr)

    def UpdateLibrary(self, event):
        logging.debug('Updating Library Tree')
        self.tree.make()

    def createMenuOption(self, event, parentmenu, label, method, arg1=None, arg2=None, arg3=None, arg4=None):
        """event, parentmenu, label, method, arg1, arg2, arg3"""
        menuItem = parentmenu.Append(-1, label)

        if None not in [arg1, arg2, arg3, arg4]:
            wrapper = lambda event: method(arg1, arg2, arg3, arg4)
        elif None not in [arg1, arg2, arg3]:
            wrapper = lambda event: method(arg1, arg2, arg3)
        elif None not in [arg1, arg2]:
            wrapper = lambda event: method(arg1, arg2)
        elif arg1 is not None:
            wrapper = lambda event: method(arg1)
        else:
            wrapper = lambda event: method()

        self.Bind(wx.EVT_MENU, wrapper, menuItem)

    def initMenubar(self):
        fileMenu = wx.Menu()  # file

        fileUpdate = wx.MenuItem(fileMenu, wx.ID_ANY, '&Update Library')
        # self.Bind(wx.EVT_MENU, self.UpdateLibrary, fileUpdate)

        fileQuit = wx.MenuItem(fileMenu, wx.ID_EXIT, '&Quit')
        # self.Bind(wx.EVT_MENU, self.OnQuit, fileQuit)

        fileMenu.Append(fileUpdate)
        fileMenu.AppendSeparator()
        fileMenu.Append(fileQuit)

        viewMenu = wx.Menu()  # view
        viewSettings = wx.MenuItem(viewMenu, wx.ID_ANY, '&Settings\tCtrl+S')
        self.Bind(wx.EVT_MENU, self.LaunchSettings, viewSettings)
        viewMenu.Append(viewSettings)

        #helpMenu = wx.Menu()  # help
        #helpAbout = wx.MenuItem(viewMenu, wx.ID_ANY, '&About\tCtrl+A')
        # self.Bind(wx.EVT_MENU, self.LaunchAbout, helpAbout)
        #helpMenu.Append(helpAbout)

        menubar = wx.MenuBar()
        menubar.Append(fileMenu, '&File')
        menubar.Append(viewMenu, '&View')
        #menubar.Append(helpMenu, '&Help')
        self.SetMenuBar(menubar)

    def initToolbar(self):
        toolbar = self.CreateToolBar()

        updateTool = toolbar.AddTool(wx.ID_ANY, 'Update Library', wx.Bitmap('icons/libraryRefresh.png'),
                                     'Refresh the library for new zips')

        startTool = toolbar.AddTool(wx.ID_ANY, 'Start Queue', wx.Bitmap('icons/queueStart.png'),
                                    'Start the process queue')

        clearTool = toolbar.AddTool(wx.ID_ANY, 'Clear Queue', wx.Bitmap('icons/queueClear.png'),
                                    'Remove all items from the queue')

        openToolLibrary = toolbar.AddTool(wx.ID_ANY, 'Open Root Directory', wx.Bitmap('icons/folderZips.png'), 'Open library in explorer')

        # openToolZips = toolbar.AddTool(wx.ID_ANY, 'Open Root Archive Directory', wx.Bitmap('icons/open.png'), 'Open library in explorer')

        settingsTool = toolbar.AddTool(wx.ID_PREFERENCES, 'Settings', wx.Bitmap('icons/settings.png'), 'Open settings')

        self.Bind(wx.EVT_TOOL, self.UpdateLibrary, updateTool)
        self.Bind(wx.EVT_TOOL, self.StartQueue, startTool)
        self.Bind(wx.EVT_TOOL, self.ClearQueue, clearTool)
        self.Bind(wx.EVT_TOOL, self.OnOpenLibrary, openToolLibrary)
        self.Bind(wx.EVT_TOOL, self.LaunchSettings, settingsTool)

        toolbar.Realize()

    def initSplitter(self):
        # splitter
        self.splitterVert = wx.SplitterWindow(self, -1)
        self.splitterVert.SetSashGravity(0.5)
        self.splitterVert.SetSashInvisible()

        # left panel for tree
        self.leftPanel = wx.Panel(self.splitterVert, -1)

        # notebook
        self.leftNotebook = wx.Notebook(self.leftPanel)
        # tree tab
        self.tree = FolderTree(self.leftNotebook, self.config.archive, 1, wx.DefaultPosition, (-1, -1),
                               wx.TR_HAS_BUTTONS | wx.TR_MULTIPLE | wx.TR_HIDE_ROOT, self)
        # installed tab
        self.installedCtrl = wx.ListCtrl(self.leftNotebook, style=wx.LC_REPORT)
        self.installedCtrl.InsertColumn(0, "Asset", width=248)
        self.installedCtrl.InsertColumn(1, "Zip", width=50)
        self.installedCtrl.InsertColumn(2, "Pickle", width=50)
        self.installedCtrl.InsertColumn(3, "Installed Time", width=100)

        self.assetCtrl = wx.ListCtrl(self.leftNotebook, style=wx.LC_REPORT)
        self.assetCtrl.InsertColumn(0, "Asset", width=221)
        self.assetCtrl.InsertColumn(1, "zip", width=50)
        self.assetCtrl.InsertColumn(2, "pkl", width=50)
        self.assetCtrl.InsertColumn(3, "Status", width=60)
        self.assetCtrl.InsertColumn(4, "Size", width=65)

        self.leftNotebook.AddPage(self.tree, "Library")
        self.leftNotebook.AddPage(self.installedCtrl, "Installed")
        self.leftNotebook.AddPage(self.assetCtrl, "Assets")

        self.GUIInstalled()

        leftBox = wx.BoxSizer(wx.VERTICAL)
        leftBox.Add(self.leftNotebook, 1, wx.EXPAND | wx.ALL, border=5)  # add self.tree to leftBox

        # bind on actions
        self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnTreeSel)
        self.tree.Bind(wx.EVT_TREE_ITEM_MENU, self.OnTreeContext)
        #
        self.installedCtrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnListSel)
        self.installedCtrl.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnListContext)

        self.assetCtrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnListSel)
        self.assetCtrl.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnListContext)

        self.leftPanel.SetSizer(leftBox)

        # right panel
        self.rightPanel = wx.Panel(self.splitterVert, -1)

        ##################
        titleFont = wx.Font(wx.FontInfo(16))
        dataFont = wx.Font(wx.FontInfo(11))

        self.name = wx.StaticText(self.rightPanel, label='')
        self.name.SetFont(titleFont)

        self.size = wx.StaticText(self.rightPanel, label='')
        self.size.SetFont(dataFont)

        self.curPath = wx.StaticText(self.rightPanel, label='')
        self.curPath.SetFont(dataFont)

        self.installedText = wx.StaticText(self.rightPanel, label='')
        self.installedText.SetFont(dataFont)

        self.zipExists = wx.StaticText(self.rightPanel, label='')
        self.zipExists.SetFont(dataFont)

        self.pickleExists = wx.StaticText(self.rightPanel, label='')
        self.pickleExists.SetFont(dataFont)

        vboxDetails = wx.BoxSizer(wx.VERTICAL)
        vboxDetails.Add(self.name, proportion=0, flag=wx.EXPAND | wx.ALL, border=2)
        vboxDetails.Add(self.curPath, proportion=0, flag=wx.EXPAND | wx.ALL, border=2)
        vboxDetails.Add(self.size, proportion=0, flag=wx.EXPAND | wx.ALL, border=2)
        vboxDetails.Add(self.installedText, proportion=0, flag=wx.EXPAND | wx.ALL, border=2)
        vboxDetails.Add(self.zipExists, proportion=0, flag=wx.EXPAND | wx.ALL, border=2)
        vboxDetails.Add(self.pickleExists, proportion=0, flag=wx.EXPAND | wx.ALL, border=2)

        ##################

        self.button1 = wx.Button(self.rightPanel, label='Add to Queue')
        self.button1.Bind(wx.EVT_BUTTON, self.button1Action)

        self.button2 = wx.Button(self.rightPanel, label='Install')
        self.button2.Bind(wx.EVT_BUTTON, self.button2Action)

        self.button3 = wx.Button(self.rightPanel, label='Create Pickle')
        self.button3.Bind(wx.EVT_BUTTON, self.button3Action)

        hboxButtons = wx.BoxSizer()
        hboxButtons.Add(self.button1, proportion=1, flag=wx.LEFT, border=5)
        hboxButtons.Add(self.button2, proportion=1, flag=wx.LEFT, border=5)
        hboxButtons.Add(self.button3, proportion=1, flag=wx.LEFT, border=5)

        self.gaugeAsset = wx.Gauge(self.rightPanel)
        self.gaugeQueue = wx.Gauge(self.rightPanel)

        ##################
        self.rightNotebook = wx.Notebook(self.rightPanel)

        # zip page
        self.zipTree = ZipTree(self.rightNotebook, 1, wx.DefaultPosition, (-1, -1),
                               wx.TR_HAS_BUTTONS | wx.TR_MULTIPLE | wx.TR_HIDE_ROOT, False)
        self.rightNotebook.AddPage(self.zipTree, "Zip")

        # queue page
        self.queueCtrl = wx.ListCtrl(self.rightNotebook, style=wx.LC_REPORT)
        self.queueCtrl.InsertColumn(0, "Asset", width=225)
        self.queueCtrl.InsertColumn(1, "Process", width=60)
        self.queueCtrl.InsertColumn(2, "State", width=85)
        self.queueCtrl.InsertColumn(3, "Status", width=75)

        self.queueCtrl.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnQueueContext)

        self.rightNotebook.AddPage(self.queueCtrl, "Queue")
        #self.zipTree.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnLeftClick)

        ##################

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(vboxDetails, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)
        self.vbox.Add(hboxButtons, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)
        self.vbox.Add(self.gaugeAsset, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)
        self.vbox.Add(self.gaugeQueue, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)
        self.vbox.Add(self.rightNotebook, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.BOTTOM | wx.RIGHT, border=5)

        ##################

        self.rightPanel.SetSizer(self.vbox)

        # Put the left and right panes into the split window
        self.splitterVert.SplitVertically(self.leftPanel, self.rightPanel)
