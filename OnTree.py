import wx, os, logging


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

    self.tree.Expand(self.item)
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
