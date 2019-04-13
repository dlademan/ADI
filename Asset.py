import logging
import pickle
import re
import shutil
from datetime import datetime
from pathlib import Path

from zipfile import ZipFile
import os
import xml.etree.ElementTree as etree


class AssetList(object):

    def __init__(self, parent, name='assets.pkl'):
        self.name = name
        self.path = parent.config.library / Path(self.name)
        self.list = self.load()  # list of AssetItems

    def append(self, name, path, installed=False):
        """ Appends an asset to the list of imported assets
        :args: name, path, installed=False
        :rtype: AssetItem
        """
        entry = AssetItem(path, installed)
        for item in self.list:
            if entry.fileName == item.fileName:
                #logging.info(entry.productName + " already in asset list, item not added.")
                return entry
        self.list.append(entry)
        self.list.sort()
        self.save()
        return entry

    def load(self):
        if self.path.exists():
            logging.info("Loading " + self.name + " from: " + str(self.path))
            with open(self.path, 'rb') as f:
                return pickle.load(f)
        else:
            logging.info("Could not find assets.pkl, empty list returned")
            return []  # return empty list if not found

    def save(self):
        with open(self.path, 'wb') as out:
            pickle.dump(self.list, out)

    def remove(self, name):
        for item in self.list:
            if name == item.asset.fileName:
                self.list.remove(item)
        self.save()

    def getIndex(self, asset):
        i = 0  # find index of item in assets list
        for item in self.list:
            if item.fileName == asset.fileName:
                break
            i += 1
        return i

    def getItem(self, fileName):
        for item in self.list:
            if item.fileName == fileName:
                return item

        logging.error("Could not find item in assets")

    def update(self, i, installed=False, time=datetime.now()):
        self.list[i].installed = installed
        self.list[i].installedTime = time
        self.save()


class AssetItem(object):
    """Class of a basic asset item
    :args: name=None, path=None, installed=False"""

    def __init__(self, path=None, installed=False):
        self.path = path
        self.zip = path.with_suffix('.zip')
        self.pkl = path.with_suffix('.pkl')

        if self.zip.exists():
            self.fileName = self.zip.name
        else:
            self.fileName = self.pkl.name

        if self.pkl.exists():
            with open(self.pkl, 'rb') as f:
                self.fileList = pickle.load(f)
        elif self.zip.exists():
            self.fileList = self.createFileList()
        else:
            self.fileList = []

        if self.zip.exists():
            self.productName = self._parseProductName()
        else:
            self.productName = path.stem

        self._sizeExt = 'MB'  # default suffix
        self._size = self._calcSize()  # use self.size property to get string with units on size

        self.installed = installed
        self.installedTime = None

    def __lt__(self, other):
        return self.fileName < other.fileName

    def _calcSize(self, places=2):
        if not self.path.exists() and self.path.suffix == '':
            self.path.mkdir()
            return 0

        size = self.path.stat().st_size
        rnd = places * 10

        if size > 2 ** 30:
            size /= 2 ** 30
            self._sizeExt = 'GB'
        else:
            size /= 2 ** 20
            self._sizeExt = 'MB'

        return int(size * rnd) / rnd  #

    def _parseProductName(self):
        productName = self.path.stem

        zf = ZipFile(self.zip, 'r')
        if 'Supplement.dsx' in zf.namelist():
            zf = ZipFile(self.zip, 'r')
            zf.extract("Supplement.dsx", path='.')
            Tree = etree.parse("Supplement.dsx")
            supplement = Tree.getroot()
            productName = supplement.find('ProductName').get('VALUE')
            os.remove("Supplement.dsx")
        elif productName[:2] == 'IM' and productName[10] == '-' and productName[13] == '_':
            temp = productName[14:]
            temp = re.findall('[\dA-Z]+(?=[A-Z])|[\dA-Z][^\dA-Z]+', temp)
            productName = ' '.join(temp)
        elif '-' in productName:
            productName = productName.replace('-', ' ')
        elif '_' in productName:
            productName = productName.replace('_', ' ')
        elif productName.islower():
            pass
        elif ' ' in productName:
            pass
        else:
            temp = re.findall('[\dA-Z]+(?=[A-Z])|[\dA-Z][^\dA-Z]+', productName)
            productName = ' '.join(temp)
        zf.close()

        return productName

    def createFileList(self):
        if not self.zip.exists():
            logging.warning("Cannot open " + self.zip.name + " in " + self.zip.parent)
            return

        zfile = ZipFile(self.zip)
        namelist = zfile.namelist()
        zfile.close()
        fileList = []  # reset if anything inside

        for member in namelist:
            if "Manifest" in member or "Supplement" in member: continue
            member = self._cleanPath(member)
            fileList.append(member)

        with open(self.pkl, 'wb') as out:
            pickle.dump(fileList, out)

        return fileList

    def install(self, parent, installPath):
        file = ZipFile(self.zip)
        memberList = []

        parent.gaugeAsset.SetRange(len(file.namelist()))
        parent.gaugeAsset.SetValue(0)

        for i, member in enumerate(file.namelist()):
            if "Manifest" in member or "Supplement" in member:
                continue

            source = file.open(member)
            member = self._cleanPath(member)
            dest = installPath / Path(member)
            memberList.append(member)

            if not dest.parent.exists():
                dest.parent.mkdir()

            if dest.suffix:
                try:
                    with source, open(dest, 'wb') as out:
                        shutil.copyfileobj(source, out)
                except OSError as e:
                    logging.error("Could not extract file " + dest.name)
                    logging.error(e)
            parent.gaugeAsset.SetValue(i + 1)

        self.installed = True

    def uninstall(self, parent, installPath):
        err = False
        parent.gaugeAsset.SetRange(len(self.fileList))
        parent.gaugeAsset.SetValue(0)

        for i, member in enumerate(self.fileList):
            member = installPath / Path(member)
            try:
                if not member.is_dir():
                    os.unlink(member)
            except OSError:
                err = True
            parent.gaugeAsset.SetValue(i + 1)

        if err: logging.warning("One or more files could not be found to be deleted")
        self._removeEmptyDirs(installPath)

    def detectInstalled(self, parent):
        fileCount = 0
        totalCount = len(self.fileList)

        for member in self.fileList:
            member = parent.config.library / Path(member)
            if member.exists():
                fileCount += 1

        logging.debug(str(fileCount) + "/" + str(totalCount) + " of " +
                      self.productName + "'s files were found")

        if fileCount == totalCount:
            self.installed = True
            self.installedTime = datetime.now()
            logging.debug(self.productName + " set to installed")
        else:
            self.installed = False
            self.installedTime = None
            logging.debug(self.productName + " set to not installed")

        parent.assets.save()
        parent.GUIUpdate()

    @property
    def size(self):
        return str(self._size) + ' ' + self._sizeExt

    @property
    def zipStr(self):
        if self.zip.exists():
            return "Exists"
        else:
            return "DNE"

    @property
    def pklStr(self):
        if self.pkl.exists():
            return "Exists"
        else:
            return "DNE"

    @property
    def installedStr(self):
        if self.installed:
            return "Installed"
        else:
            return "Not"

    @property
    def installedTimeStr(self):
        return f"{self.installedTime:%Y-%m-%d %H:%M}"

    @staticmethod
    def _cleanPath(path):
        if path[:8] == "Content/":
            path = path[8:]
        elif path[:11] == "My Library/":
            path = path[11:]
        return path

    @staticmethod
    def _removeEmptyDir(path):
        try:
            os.rmdir(path)
        except Exception as e:
            e

    def _removeEmptyDirs(self, path):
        for root, dirnames, filenames in os.walk(path, topdown=False):
            for dirname in dirnames:
                self._removeEmptyDir(os.path.realpath(os.path.join(root, dirname)))