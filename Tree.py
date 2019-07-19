from zipfile import ZipFile
from pathlib import Path

import wx
import logging
import threading
import pickle

from Asset import AssetItem


class FolderTree(wx.TreeCtrl):

    def __init__(self, parent, archive, id, position, size, style, main,
                 filter_installed=False, filter_not_installed=False, filter_zip=False):
        wx.TreeCtrl.__init__(self, parent, id, position, size, style)
        self.path = archive
        self.main = main

        self.filter_installed = filter_installed
        self.filter_not_installed = filter_not_installed
        self.filter_zip = filter_zip

        if not self.main.config.first:
            treeThread = threading.Thread(target=self.make(), args=[])
            treeThread.start()

    def make(self):
        self.DeleteAllItems()
        asset = AssetItem(self.main.config.archive)
        self.root_node = self.AddRoot(self.path.name, data=asset)
        node_list = self.populate(self.root_node)
        node_list.reverse()
        for node in node_list:
            path = self.GetItemData(node).path
            children_count = self.GetChildrenCount(node)
            if path.is_dir() and children_count < 1:
                self.Delete(node)

        if self.main.config.expand:
            self.ExpandAll()

    def populate(self, curNode):
        path = self.GetItemData(curNode).path
        sub_list = [x for x in path.iterdir()]  # list of Path objects in current folder
        node_list = []
        term = self._strip_product_name(self.main.textctrl_filter.GetLineText(0))
        for sub in sub_list:

            if sub.is_dir():
                asset = AssetItem(sub)
                next_node = self.AppendItem(curNode, asset.product_name, -1, -1, asset)
                node_list.append(next_node)

                self.SetItemHasChildren(next_node, True)
                temp_list = self.populate(next_node)

                for node in temp_list:
                    node_list.append(node)

            elif sub.with_suffix('.zip').exists():
                asset = self.main.assets.append(sub.with_suffix('.zip'))
                backup_path = self.main.config.backup_path / Path(str(asset.zip.stem) + '.pkl')
                with open(backup_path, 'wb') as out:
                    pickle.dump(asset, out)

                product_name = self._strip_product_name(asset.product_name)
                if term not in product_name and term not in asset.tags: continue
                if self.filter_installed and not asset.installed: continue
                if self.filter_not_installed and asset.installed: continue
                if self.filter_zip and not asset.zip.exists(): continue

                next_node = self.AppendItem(curNode, asset.product_name, -1, -1, asset)
                node_list.append(next_node)

        self.SortChildren(curNode)
        return node_list

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
    def _strip_product_name(name):
        return name.lower().replace(' ', '').replace('-', '').replace('(', '').replace(')', '')


class ZipTree(wx.TreeCtrl):

    def __init__(self, parent, id, position, size, style, path):
        wx.TreeCtrl.__init__(self, parent, id, position, size, style)
        if not path: return
        self.file = ZipFile(path)
        rootNode = self.AddRoot('zipRoot')

        self.populate(rootNode)
        self.file.close()

    def populate(self, root_node):
        list_info = self.file.infolist()
        dict_nodes = {}

        for i, item in enumerate(list_info):
            string_filename = item.filename
            parts = string_filename.split('/')

            node_current = ""
            for j, part in enumerate(parts):
                if part == '': continue

                node_parent = node_current
                node_current += '/' + part
                if node_current not in dict_nodes and j == 0:
                    dict_nodes[node_current] = self.AppendItem(root_node, part)
                elif node_current not in dict_nodes:
                    dict_nodes[node_current] = self.AppendItem(dict_nodes[node_parent], part)

        for item in dict_nodes:
            self.SortChildren(item)

    def remake(self, path=None):
        self.DeleteAllItems()
        rootNode = self.AddRoot('zipRoot')
        if not path: return
        if path.suffix == ".zip":
            try:
                self.file = ZipFile(path)
            except:
                logging.error("Error occurred while opening zip file: " + str(path.name))
                return

            self.populate(rootNode)
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
