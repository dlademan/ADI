from zipfile import ZipFile

import wx
import logging
import threading

from Asset import AssetItem


class FolderTree(wx.TreeCtrl):

    def __init__(self, parent, archive, id, position, size, style, main):
        wx.TreeCtrl.__init__(self, parent, id, position, size, style)
        self.path = archive
        self.main = main
        treeThread = threading.Thread(target=self.make(), args=[])
        treeThread.start()

    def make(self):
        self.DeleteAllItems()
        asset = AssetItem(self.main.config.archive)
        rootNode = self.AddRoot(self.path.name, data=asset)
        self.populate(rootNode)

    def populate(self, curNode):
        skip = []
        subList = self.directory(self.GetItemData(curNode).path)  # list of Path objects in current folder
        nodeList = []
        for subDir in subList:
            if subDir.stem in skip:
                continue
            elif subDir.is_dir():
                asset = AssetItem(subDir)
                nextNode = self.AppendItem(curNode, asset.productName, -1, -1, asset)
                nodeList.append(nextNode)
                self.SetItemHasChildren(nextNode, True)
                self.populate(nextNode)
            elif subDir.suffix == '.pkl' and subDir.with_suffix('.zip').exists():
                asset = self.main.assets.append(subDir.stem, subDir.with_suffix('.zip'))
                skip.append(subDir.stem)  # skip zip of same name
                nextNode = self.AppendItem(curNode, asset.productName, -1, -1, asset)
                nodeList.append(nextNode)
            elif subDir.suffix == '.pkl' or subDir.suffix == '.zip':
                asset = self.main.assets.append(subDir.stem, subDir)
                nextNode = self.AppendItem(curNode, asset.productName, -1, -1, asset)
                nodeList.append(nextNode)

        self.SortChildren(curNode)
        for node in nodeList:
            self.SortChildren(node)


    # TODO make this work
    def OnCompareItems(self, item1, item2):
        text1 = self.GetItemText(item1)
        text2 = self.GetItemText(item2)
        isDir1 = self.GetItemData(item1).path.is_dir()
        isDir2 = self.GetItemData(item2).path.is_dir()

        if isDir1 and isDir2:
            if text1 < text2:
                return -1
            elif text1 == text2:
                return 0
            else:
                return 1
        elif isDir1 and not isDir2:
            return -1
        elif not isDir1 and isDir2:
            return 1
        else:
            if text1 < text2:
                return -1
            elif text1 == text2:
                return 0
            else:
                return 1

    @staticmethod
    def directory(directory):
        """crawls the root folder of library to populate"""

        root = [x for x in directory.iterdir()]
        return root


class ZipTree(wx.TreeCtrl):

    def __init__(self, parent, id, position, size, style, path):
        wx.TreeCtrl.__init__(self, parent, id, position, size, style)
        if not path: return
        self.file = ZipFile(path)
        rootNode = self.AddRoot('zipRoot')

        self.populate(rootNode)
        self.file.close()

    def populate(self, rootNode, pick=False):
        if not pick:
            infolist = self.file.infolist()
        else:
            infolist = self.file

        if len(infolist) < 1: return

        nodeList = []
        for file in infolist:
            if not pick:
                fileName = file.filename
                fileIsDir = file.is_dir()
            else:
                fileName = file
                fileIsDir = False
            split = str(fileName).split("/")
            if len(split) <= 2:
                nodeList.append(self.AppendItem(rootNode, fileName))
            else:
                if fileIsDir:
                    offset = -2
                else:
                    offset = -1
                split = split[:offset]

                parentStr = ""
                for part in split: parentStr += part + "/"

                for i in range(len(nodeList)):
                    if pick:
                        if parentStr == infolist[i]:
                            nodeList.append(self.AppendItem(nodeList[i], str(fileName).split("/")[offset]))
                            break
                    else:
                        if parentStr == infolist[i].filename:
                            nodeList.append(self.AppendItem(nodeList[i], str(fileName).split("/")[offset]))
                            break
        for node in nodeList:
            self.SortChildren(node)

    def remake(self, path=None):
        self.DeleteAllItems()
        rootNode = self.AddRoot('zipRoot')
        if not path: return
        if path.suffix == ".zip":
            self.file = ZipFile(path)
            self.populate(rootNode, False)
            self.file.close()

    def OnCompareItems(self, item1, item2):
        text1 = self.GetItemText(item1)
        text2 = self.GetItemText(item2)
        isDir1 = self.GetChildrenCount(item1) > 1
        isDir2 = self.GetChildrenCount(item2) > 1

        if isDir1 and isDir2:
            if text1 < text2: return -1
            elif text1 == text2: return 0
            else: return 1
        elif isDir1 and not isDir2: return -1
        elif not isDir1 and isDir2: return 1

        if text1 < text2: return -1
        elif text1 == text2: return 0
        else: return 1
