from zipfile import ZipFile
from pathlib import Path

import wx
import os
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
            treeThread = threading.Thread(target=self.populate(), args=[])
            treeThread.start()

    def populate(self):
        self.DeleteAllItems()
        root = self.main.config.archive
        logging.info('Building library tree')
        term = self._strip_product_name(self.main.textctrl_filter.GetLineText(0))
        dict_nodes = dict()
        list_paths = []

        path_root = root
        node_root = self.AddRoot(text=self.path.name, data=AssetItem(path_root))
        dict_nodes[''] = node_root

        for dirpath, dirnames, filenames in os.walk(path_root):
            for name in filenames:
                path = Path(dirpath) / Path(name)
                list_paths.append(path)

        for path in list_paths:
            parts = str(path)
            if str(root) in parts: parts = parts[len(str(root)):]
            parts = str(parts).split('\\')
            node_current = ''

            asset = self.main.assets.get_item(file_name=path.name)
            if asset is None: asset = AssetItem(path)

            if term not in asset.product_name and term not in asset.tags: continue
            if self.filter_installed and not asset.installed: continue
            if self.filter_not_installed and asset.installed: continue
            if self.filter_zip and not asset.zip.exists(): continue

            for part in parts:
                if part == '' or (not path.with_suffix('.zip').exists() and not path.is_dir()): continue

                node_parent = node_current
                node_current += '/' + part

                product_name = part
                if path.with_suffix('.zip').exists() and part == parts[-1]:
                    product_name = AssetItem.parse_product_name(path.with_suffix('.zip'))

                if node_current not in dict_nodes:
                    dict_nodes[node_current] = self.AppendItem(dict_nodes[node_parent], product_name, data=path)

        for node in dict_nodes.values(): self.SortChildren(node)
        if self.main.config.expand: self.ExpandAll()
        logging.info('Library tree built')

    def OnCompareItems(self, item1, item2):
        text1 = self.GetItemText(item1)
        text2 = self.GetItemText(item2)
        isDir1 = self.GetChildrenCount(item1) > 0
        isDir2 = self.GetChildrenCount(item2) > 0

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
        node_root = self.AddRoot('zipRoot')

        self.populate(node_root)
        self.file.close()

    def populate(self, node_root):
        list_info = self.file.infolist()
        dict_nodes = dict()
        dict_nodes[''] = node_root

        for item in list_info:
            parts = item.filename.split('/')
            node_current = ''

            for part in parts:
                if part == '': continue

                node_parent = node_current
                node_current += '/' + part

                if node_current not in dict_nodes:
                    dict_nodes[node_current] = self.AppendItem(dict_nodes[node_parent], part)

        for item in dict_nodes.values():
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
