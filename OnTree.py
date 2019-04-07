import wx, os, logging


def OnTreeSel(self, event):
    # Get the selected item object
    self.item = event.GetItem()
    asset = self.tree.GetItemData(self.item)
    self.selAsset = asset

    for i in self.assets.list:
        if asset.name == i.name:
            asset = i

    self.tree.Expand(self.item)
    self.name.SetLabel(asset.name)
    self.curPath.SetLabel(str(asset.path.parent))
    if asset.zip:
        self.zipTree.remake(asset.zip)
    else:
        self.zipTree.remake()

    ###
    if asset.path.is_dir():
        self.name.SetLabel(asset.path.stem)
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
    if asset.zip:
        self.size.SetLabel('Size: ' + asset.getSize())
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
    if asset.pkl:
        self.pickleExists.SetLabel('Pickle: Exists')
    else:
        self.pickleExists.SetLabel('Pickle: False')
    ####
    if asset.installed and asset.pkl:
        self.button1.SetLabel('Queue Uninstall')
        self.button1.Enable()
        self.button2.SetLabel('Uninstall')
        self.button2.Enable()
    elif not asset.installed and asset.zip:
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
            self.createMenuOption(event, popupmenu, 'Queue Uninstall', self.AddToQueue, event, asset, False)

        elif not installed and z.exists():
            self.createMenuOption(event, popupmenu, 'Install', self.installAsset, event, asset)
            self.createMenuOption(event, popupmenu, 'Queue Install', self.AddToQueue, event, asset, True)

        if z.exists() and not p.exists():
            self.createMenuOption(event, popupmenu, 'Create Pkl', self.createPkl, event, asset)

        if not path.is_dir():
            self.createMenuOption(event, forcemenu, 'Install', self.installAsset, event, asset)
            self.createMenuOption(event, forcemenu, 'Uninstall', self.uninstallAsset, event, asset)
            self.createMenuOption(event, forcemenu, 'Create Pkl', self.createPkl, event, asset)
            popupmenu.AppendSubMenu(forcemenu, '&Force')

    self.createMenuOption(event, popupmenu, 'Open Location', self.OnOpenLibrary, event, asset.path)

    self.PopupMenu(popupmenu, event.GetPoint())  # show menu at cursor
