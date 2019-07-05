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

    def __init__(self, parent, name='assets.pkl', clear=False):
        self.parent = parent
        self.name = name
        self.clear = clear
        self.path = parent.config.library / Path(self.name)
        self.list = self.load()  # list of AssetItems

    def load(self):
        if self.clear or self.parent.config.first:
            return []
        elif self.path.exists():
            logging.info("Loading " + self.name + " from: " + str(self.path))
            with open(self.path, 'rb') as f:
                return pickle.load(f)
        else:
            logging.info("Could not find assets.pkl, empty list returned")
            return []  # return empty list if not found

    def save(self):
        if not self.path.parent.exists():
            Path.mkdir(self.path.parent, parents=True)

        with open(self.path, 'wb') as out:
            pickle.dump(self.list, out)

    def append(self, path, installed=False):
        """ Appends an asset to the list of imported assets
        :args: path, installed=False
        :rtype: AssetItem
        """
        entry = AssetItem(path, installed)
        for item in self.list:
            if entry.file_name == item.file_name:
                item.tags = entry.tags
                item.path = entry.path
                item.zip = item.path.with_suffix('.zip')
                return item
        i = 0
        suffix = 2
        temp = entry.product_name
        while i < len(self.list):
            if temp == self.list[i].product_name:
                temp = entry.product_name + ' ' + str(suffix)
                suffix += 1
                i = 0
                continue
            i += 1
        entry.product_name = temp
        self.list.append(entry)
        self.list.sort()
        self.save()
        return entry

    def remove(self, name):
        for item in self.list:
            if name == item.asset.fileName:
                self.list.remove(item)
        self.save()

    def clean(self):
        for asset in self.list:
            if not asset.installed and not asset.zip.exists():
                self.list.remove(asset)

        self.parent.update_all()
        self.save()

    def get_index(self, asset):
        i = 0  # find index of item in assets list
        for item in self.list:
            if item.file_name == asset.file_name:
                break
            i += 1
        return i

    def get_item(self, file_name=None, product_name=None):
        if file_name is not None:
            for asset in self.list:
                if asset.file_name == file_name:
                    return asset
        elif product_name is not None:
            for asset in self.list:
                if asset.product_name == product_name:
                    return asset
        elif product_name is None and file_name is None:
            logging.warning("Please pass an arg when using get_item")

        return None

    def update(self, i, installed=False, time=datetime.now()):
        self.list[i].installed = installed
        self.list[i].installed_time = time
        self.save()


class AssetItem(object):
    """Class of a basic asset item
    :args: name=None, path=None, installed=False"""

    def __init__(self, path=None, installed=False):
        self.path = path
        self.zip = path.with_suffix('.zip')

        self.file_name = self.zip.name

        if self.zip.exists():
            self.file_list = self.create_file_list()
        else:
            self.file_list = []

        if self.zip.exists():
            self.product_name = self._parse_product_name()
        else:
            self.product_name = path.stem

        self._size_ext = 'MB'  # default suffix
        self.size_raw, self.size_display = self._calc_size()  # use self.size property to get string with units on size

        self.installed = installed
        self.installed_time = None

        self.tags = self._create_tags()

    def __lt__(self, other):
        return self.product_name < other.product_name

    def _calc_size(self, places=2):
        if not self.path.exists() and self.path.is_dir():
            Path.mkdir(self.path.parent, parents=True)
            return 0

        size = self.path.stat().st_size
        rnd = places * 10

        if size > 2 ** 30:
            size /= 2 ** 30
            self._size_ext = 'GB'
        else:
            size /= 2 ** 20
            self._size_ext = 'MB'

        return self.path.stat().st_size, str(int(size * rnd) / rnd) + ' ' + self._size_ext

    def _parse_product_name(self):
        product_name = self.path.stem

        try:
            zf = ZipFile(self.zip, 'r')
        except:
            logging.error("Error occurred while opening zip file: " + str(self.file_name))
            return "INVALID ZIP"

        if 'Supplement.dsx' in zf.namelist():
            zf = ZipFile(self.zip, 'r')
            zf.extract("Supplement.dsx", path='.')
            Tree = etree.parse("Supplement.dsx")
            supplement = Tree.getroot()
            product_name = supplement.find('ProductName').get('VALUE')
            os.remove("Supplement.dsx")
        elif product_name[:2] == 'IM' and product_name[10] == '-' and product_name[13] == '_':
            temp = product_name[14:]
            temp = re.findall('[\dA-Z]+(?=[A-Z])|[\dA-Z][^\dA-Z]+', temp)
            product_name = ' '.join(temp)
        elif '-' in product_name:
            product_name = product_name.replace('-', ' ')
        elif '_' in product_name:
            product_name = product_name.replace('_', ' ')
        elif product_name.islower():
            pass
        elif ' ' in product_name:
            pass
        else:
            temp = re.findall('[\dA-Z]+(?=[A-Z])|[\dA-Z][^\dA-Z]+', product_name)
            product_name = ' '.join(temp)
        zf.close()

        return product_name

    def _create_tags(self):
        path = str(self.path)
        root = self._get_root()
        tags = []

        path = path.replace(str(root), '')
        temp = path.split('\\')
        temp = temp[:-1]
        temp = temp[1:]

        for tag in temp:
            tag = tag.lower().replace(' ', '')
            tags.append(tag)

        return tags

    def _get_root(self):
        if self.path.is_dir():
            things = [x for x in self.path.iterdir()]
            for thing in things:
                if thing.name == "root.pkl":
                    return self.path

        for member in self.path.parents:
            things = [x for x in member.iterdir()]
            for thing in things:
                if thing.name == "root.pkl":
                    return member

    def create_file_list(self):
        try:
            zfile = ZipFile(self.zip)
        except:
            logging.error("Error occurred while opening zip file: " + str(self.file_name))
            return []

        namelist = zfile.namelist()
        zfile.close()
        file_list = []  # reset if anything inside

        for member in namelist:
            if "Manifest" in member or "Supplement" in member: continue
            member = self._clean_path(member)
            file_list.append(member)

        return file_list

    def install(self, parent, install_path, queue_index=None, gauge=None):
        logging.info("Installing " + self.product_name)
        file = ZipFile(self.zip)
        if gauge is not None:
            gauge.Pulse()
            gauge.SetRange(len(file.namelist()))
            gauge.SetValue(0)

        for i, member in enumerate(file.namelist()):
            if "Manifest" in member or "Supplement" in member:
                continue

            source = file.open(member)
            is_dir = file.getinfo(member).is_dir()
            member = self._clean_path(member)
            dest = install_path / Path(member)

            if not dest.parent.exists():
                try:
                    Path.mkdir(dest.parent)
                except OSError as e:
                    logging.error("Parent folder creation - " + str(e))

            if not is_dir:
                try:
                    with source, open(dest, 'wb') as out:
                        shutil.copyfileobj(source, out)
                except OSError as e:
                    logging.error("File creation - " + str(e))
            if gauge is not None:
                gauge.SetValue(i + 1)

        if queue_index is not None:
            parent.queue.update_status(queue_index, 2)

        self.installed = True
        self.installed_time = datetime.now()
        logging.info(self.product_name + " installed")

    def uninstall(self, parent, installPath, queueIndex=None, gauge=None):
        logging.info("Uninstalling " + self.product_name)

        if gauge is not None:
            gauge.SetRange(len(self.file_list))
            gauge.SetValue(0)

        for i, member in enumerate(self.file_list):
            member = installPath / Path(member)
            try:
                if not member.is_dir():
                    os.unlink(member)
            except OSError as e:
                logging.error("Could not delete file " + member.name + " - " + str(e))

            if gauge is not None:
                gauge.SetValue(i + 1)

        self._remove_empty_dirs(installPath)

        if queueIndex is not None:
            parent.queue.update_status(queueIndex, 2)

        if gauge is not None:
            gauge.Pulse()

        self.installed = False
        self.installed_time = None
        logging.info(self.product_name + " uninstalled")

    def detect(self, parent, update=False):
        fileCount = 0
        totalCount = len(self.file_list)

        for member in self.file_list:
            member = parent.config.library / Path(member)
            if member.exists():
                fileCount += 1

        if fileCount == totalCount:
            self.installed = True
            self.installed_time = datetime.now()
            logging.debug("Set to installed:     " + self.product_name + " " +
                          str(fileCount) + "/" + str(totalCount) + " files were found")
        else:
            self.installed = False
            self.installed_time = None
            logging.debug("Set to not installed: " + self.product_name + " " +
                          str(fileCount) + "/" + str(totalCount) + " files were found")

        parent.assets.save()
        if update:
            parent.update_all()


    @property
    def size(self):
        return str(self.size_raw) + ' ' + self._size_ext

    @property
    def zip_str(self):
        if self.zip.exists():
            return "Exists"
        else:
            return "DNE"

    @property
    def pkl_str(self):
        if self.pkl.exists():
            return "Y"
        else:
            return "N"

    @property
    def installed_str(self):
        if self.installed:
            return "Installed"
        else:
            return "Not"

    @property
    def installed_time_str(self):
        if isinstance(self.installed_time, datetime):
            return f"{self.installed_time:%Y-%m-%d %H:%M}"
        else:
            return ""

    @staticmethod
    def _clean_path(path):
        if path[:8] == "Content/":
            path = path[8:]
        elif path[:11] == "My Library/":
            path = path[11:]
        elif path[:19] == "My DAZ 3D Library/":
            path = path[19:]
        return path

    @staticmethod
    def _remove_empty_dir(path):
        try:
            os.rmdir(path)
        except Exception as e:
            e

    def _remove_empty_dirs(self, path):
        for root, dirnames, filenames in os.walk(path, topdown=False):
            for dirname in dirnames:
                self._remove_empty_dir(os.path.realpath(os.path.join(root, dirname)))