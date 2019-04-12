import wx, os, logging
from pathlib import Path


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

    for i in self.assets.list:
        if item.GetText() == i.productName:
            asset = i

    if asset is None:
        logging.error("Could not find asset in list, no menu to be made")
        return

    z = asset.zip
    p = asset.pkl

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


def OnQueueContext(self, event):
    item = event.GetItem()
    popupMenu = wx.Menu()

    logging.debug(item.GetText())

    self.createMenuOption(event, popupMenu, 'Remove from queue', self.queue.remove, item.GetText())
    self.PopupMenu(popupMenu, event.GetPoint())