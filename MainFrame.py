from datetime import datetime
import threading
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

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    def __init__(self, parent, id, title):

        wx.Frame.__init__(self, parent, id, title, wx.DefaultPosition, (950, 800), style=wx.DEFAULT_FRAME_STYLE)
        self.Bind(wx.EVT_IDLE, self.OnIdle)

        self.config = Config(self)
        self.initLogger(self.logger)

        logging.info("------------ ADI Started ------------")

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
            self.SetPosition(self.config.winPos)
            self.Show()

    def SaveCurrentDimensions(self, event):
        self.config.winSize = self.GetSize()
        self.config.winPos = self.GetPosition()
        self.config.save()

    def OnIdle(self, event):
        self.SaveCurrentDimensions(event)
        event.Skip()

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
            self.AddToQueue(self.selAsset, True)
        elif self.button1.GetLabel() == "Queue Uninstall":
            self.AddToQueue(self.selAsset, False)
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
        logging.info("Installing " + asset.productName)

        installThread = threading.Thread(target=asset.install, args=[self, self.config.library])
        installThread.start()

        i = self.assets.getIndex(asset)
        self.assets.update(i, True, datetime.now())

        self.GUIUpdate()

    def uninstallAsset(self, event, asset):
        logging.info("Uninstalling " + asset.productName)

        uninstallThread = threading.Thread(target=asset.uninstall, args=[self, self.config.library])
        uninstallThread.start()

        i = self.assets.getIndex(asset)
        self.assets.update(i, False, None)
        self.GUIUpdate()

    def queueAll(self, directory, process):
        self.rightNotebook.SetSelection(1)
        for asset in self.assets.list:
            if str(directory) in str(asset.path.parent):
                if process and not asset.installed:
                    self.AddToQueue(asset, process)
                elif not process and asset.installed:
                    self.AddToQueue(asset, process)

    def detectAll(self, event, directory=None):
        if directory is None:
            directory = self.config.archive
        for asset in self.assets.list:

            if asset.installed:
                logging.info(asset.productName + " already installed, skipping detection")
                continue
            if str(directory) in str(asset.path):
                detectThread = threading.Thread(target=asset.detectInstalled, args=[self])
                detectThread.start()

    # todo threading here
    def QueueThreadStart(self, event):
        queueThread = threading.Thread(target=self.StartQueue, args=[event])
        queueThread.start()

    def StartQueue(self, event):
        self.queue.inProgress = True
        self.queue.save()
        self.rightNotebook.SetSelection(1)
        logging.info("Starting Queued Processes")
        i = 0
        queueLength = 0
        for item in self.queue.list:
            if item.status != 2:
                queueLength += 1
        self.gaugeQueue.SetRange(queueLength)
        self.gaugeQueue.SetValue(0)
        for i, qItem in enumerate(self.queue.list):
            if self.queue.list[i].status == 2:  # skip finished queue items
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
        logging.info("Queued Processes Finished")

    def ClearQueue(self, event):
        self.queueCtrl.DeleteAllItems()
        self.queue = QueueList(self, clear=True)

    def AddToQueue(self, asset, process):
        self.rightNotebook.SetSelection(1)
        for queueItem in self.queue.list:
            if asset.fileName == queueItem.asset.fileName and queueItem.status == 0:
                logging.warning(asset.productName + " already queued for process, nothing added to queue")
                return

        if process:
            logging.info("Added " + asset.productName + " to queue to be installed.")
        else:
            logging.info("Added " + asset.productName + " to queue to be uninstalled.")

        self.queue.append(asset, process)
        self.GUIQueue()

    def AddListToQueue(self, assetList, process):
        for asset in assetList:
            self.AddToQueue(asset, process)

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
        logging.info('Updating Library Tree')
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

        fileQuit = wx.MenuItem(fileMenu, wx.ID_EXIT, '&Quit')
        self.Bind(wx.EVT_MENU, self.OnIdle, fileQuit)

        fileMenu.Append(fileQuit)

        dataMenu = wx.Menu()

        dataDetect = wx.MenuItem(dataMenu, -1, '&Detect All Assets')
        self.Bind(wx.EVT_MENU, self.detectAll, dataDetect)
        dataUpdate = wx.MenuItem(fileMenu, wx.ID_ANY, '&Update Library')
        self.Bind(wx.EVT_MENU, self.UpdateLibrary, dataUpdate)

        dataMenu.Append(dataDetect)
        dataMenu.Append(dataUpdate)

        viewMenu = wx.Menu()  # view
        viewSettings = wx.MenuItem(viewMenu, wx.ID_ANY, '&Settings\tCtrl+S')
        self.Bind(wx.EVT_MENU, self.LaunchSettings, viewSettings)
        viewMenu.Append(viewSettings)

        menubar = wx.MenuBar()
        menubar.Append(fileMenu, '&File')
        menubar.Append(dataMenu, '&Data')
        menubar.Append(viewMenu, '&View')
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
        self.Bind(wx.EVT_TOOL, self.QueueThreadStart, startTool)
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

    def initLogger(self, logger):
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        if not self.config.getConfigPath().exists():
            self.config.getConfigPath().mkdir(parents=True)

        fh = logging.FileHandler(str(self.config.getConfigPath()) + '/log.txt')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    def OnListSel(self, event):
        item = event.GetItem()
        for i in self.assets.list:
            if item.GetText() == i.productName:
                self.selAsset = i

        p = self.selAsset.pkl
        z = self.selAsset.zip

        if z.exists():
            self.size.SetLabel('Size: ' + self.selAsset.size)
            self.zipExists.SetLabel('Zip: Exists')
            self.button3.Enable()
        else:
            self.size.SetLabel('Size: N/A')
            self.zipExists.SetLabel('Zip: N/A')
            self.button3.Disable()

        if p.exists():
            self.pickleExists.SetLabel('Pickle: Exists')
            self.button1.Enable()
            self.button2.Enable()
        else:
            self.pickleExists.SetLabel('Pickle: N/A')
            self.button1.Disable()
            self.button2.Disable()

        if p.exists() and self.selAsset.installed:
            self.button1.SetLabel("Queue Uninstall")
            self.button2.SetLabel("Uninstall")
        elif z.exists() and not self.selAsset.installed:
            self.button1.SetLabel("Queue Install")
            self.button2.SetLabel("Install")

        self.name.SetLabel(item.GetText())
        self.curPath.SetLabel(str(self.selAsset.path.parent))
        self.installedText.SetLabel('Installed: True')

    def OnListContext(self, event):
        item = event.GetItem()
        popupMenu = wx.Menu()

        count = self.assetCtrl.GetSelectedItemCount()
        logging.debug(str(count) + " items selected")
        logging.debug(range(count))

        for i in self.assets.list:
            if item.GetText() == i.productName:
                asset = i

        if asset is None:
            logging.error("Could not find asset in list, no menu to be made")
            return

        z = asset.zip
        p = asset.pkl

        if count == 1:
            for asset in self.assets.list:
                if item.GetText() == asset.productName:
                    if p.exists() and asset.installed:
                        self.createMenuOption(event, popupMenu, 'Uninstall', self.uninstallAsset, event, asset)
                        self.createMenuOption(event, popupMenu, 'Queue Uninstall', self.AddToQueue, asset, False)
                        popupMenu.AppendSeparator()

                    elif not asset.installed and z.exists():
                        self.createMenuOption(event, popupMenu, 'Install', self.installAsset, event, asset)
                        self.createMenuOption(event, popupMenu, 'Queue Install', self.AddToQueue, asset, True)
                        popupMenu.AppendSeparator()

                    if z.exists() and not p.exists():
                        self.createMenuOption(event, popupMenu, 'Create Pickle', self.button3Action, event, asset)

                    if p.exists() or z.exists():
                        self.createMenuOption(event, popupMenu, 'Open Location', self.OnOpenLibrary, event, asset.path)

                    if p.exists() and not asset.installed:
                        self.createMenuOption(event, popupMenu, 'Check if Installed',
                                              asset.detectInstalled, self)

                    self.PopupMenu(popupMenu, event.GetPoint())
        else:
            selectedAssets = [self.assetCtrl.GetFirstSelected()]
            queuedAssets = []
            for i in range(count - 1):
                selectedAssets.append(self.assetCtrl.GetNextSelected(selectedAssets[i]))
            for item in selectedAssets:
                productName = self.assetCtrl.GetItemText(item, 0)
                for asset in self.assets.list:
                    if productName == asset.productName:
                        queuedAssets.append(asset)

            self.createMenuOption(event, popupMenu, 'Queue selected to be Installed',
                                  self.AddListToQueue, queuedAssets, True)
            self.createMenuOption(event, popupMenu, 'Queue selected to be Uninstalled',
                                  self.AddListToQueue, queuedAssets, False)

            self.PopupMenu(popupMenu, event.GetPoint())

    def OnTreeSel(self, event):
        # Get the selected item object
        self.item = event.GetItem()
        productName = self.tree.GetItemText(self.item)
        asset = None
        for member in self.assets.list:
            if member.productName == productName:
                asset = member
                break
        if asset is None:
            asset = self.tree.GetItemData(self.item)
        self.selAsset = asset

        for i in self.assets.list:
            if asset.fileName == i.fileName:
                asset = i

        self.name.SetLabel(asset.productName)
        self.curPath.SetLabel(str(asset.path.parent))
        if asset.zip.exists():
            self.zipTree.remake(asset.zip)
        else:
            self.zipTree.remake()

        ###
        if asset.path.is_dir():
            self.curPath.SetLabel(str(asset.path.parent))
            self.size.Hide()
            self.installedText.Hide()
            self.zipExists.Hide()
            self.pickleExists.Hide()
            self.button1.Disable()
            self.button2.Disable()
            self.button3.Disable()
            return
        else:
            self.size.Show()
            self.installedText.Show()
            self.zipExists.Show()
            self.pickleExists.Show()

        ####
        if asset.zip.exists():
            self.size.SetLabel('Size: ' + asset.size)
            self.zipExists.SetLabel('Zip: Exists')
            self.button3.Enable()
        else:
            self.size.SetLabel('Size: N/A')
            self.zipExists.SetLabel('Zip: N/A')
            self.button3.Disable()

        if asset.installed:
            self.installedText.SetLabel('Installed: True')
        else:
            self.installedText.SetLabel('Installed: False')
        ####
        if asset.pkl.exists():
            self.pickleExists.SetLabel('Pickle: Exists')
        else:
            self.pickleExists.SetLabel('Pickle: False')
        ####
        if asset.installed and asset.pkl.exists():
            self.button1.SetLabel('Queue Uninstall')
            self.button1.Enable()
            self.button2.SetLabel('Uninstall')
            self.button2.Enable()
        elif not asset.installed and asset.zip.exists():
            self.button1.SetLabel('Queue Install')
            self.button1.Enable()
            self.button2.SetLabel('Install')
            self.button2.Enable()
        else:
            self.button1.Disable()
            self.button2.Disable()

    def OnTreeContext(self, event):
        # Get TreeItemData
        self.item = event.GetItem()
        asset = self.tree.GetItemData(self.item)
        # for asset in self.assets.list:
        #     if tempAsset.fileName == asset.fileName:
        #         asset =
        self.selAsset = asset

        # Create menu
        popupmenu = wx.Menu()
        forcemenu = wx.Menu()

        if not asset.path.is_dir():
            index = self.assets.getIndex(asset)
            installed = self.assets.list[index].installed
            path = self.assets.list[index].path
            z = self.assets.list[index].zip
            p = self.assets.list[index].pkl

            if installed and p.exists():
                self.createMenuOption(event, popupmenu, 'Uninstall', self.uninstallAsset, event, asset)
                self.createMenuOption(event, popupmenu, 'Queue Uninstall', self.AddToQueue, asset, False)

            elif not installed and z.exists():
                self.createMenuOption(event, popupmenu, 'Install', self.installAsset, event, asset)
                self.createMenuOption(event, popupmenu, 'Queue Install', self.AddToQueue, asset, True)

            if not path.is_dir():
                self.createMenuOption(event, forcemenu, 'Install', self.installAsset, event, asset)
                self.createMenuOption(event, forcemenu, 'Uninstall', self.uninstallAsset, event, asset)
                popupmenu.AppendSubMenu(forcemenu, '&Force')

            if p.exists() and not installed:
                self.createMenuOption(event, popupmenu, 'Check if Installed',
                                      asset.detectInstalled, self)
        elif asset.path.is_dir():
            self.createMenuOption(event, popupmenu, 'Queue all to be installed',
                                  self.queueAll, asset.path, True)
            self.createMenuOption(event, popupmenu, 'Queue all to be uninstalled',
                                  self.queueAll, asset.path, False)
            self.createMenuOption(event, popupmenu, 'Detect assets in directory',
                                  self.detectAll, event, asset.path)

        self.createMenuOption(event, popupmenu, 'Open Location', self.OnOpenLibrary, event, asset.path)

        self.PopupMenu(popupmenu, event.GetPoint())  # show menu at cursor

    def OnQueueContext(self, event):
        item = event.GetItem()
        popupMenu = wx.Menu()

        logging.debug(item.GetText())

        self.createMenuOption(event, popupMenu, 'Remove from queue', self.queue.remove, item.GetText())
        self.PopupMenu(popupMenu, event.GetPoint())