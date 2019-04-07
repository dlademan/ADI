import logging
import pickle
from datetime import datetime
from pathlib import Path


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
        entry = AssetItem(name, path, installed)
        for item in self.list:
            if name == item.name:
                logging.warning(entry.name + " already in asset list, item not added.")
                return entry
        self.list.append(entry)
        self.list.sort()
        self.save()
        return entry

    def load(self):
        if self.path.exists():
            logging.debug("Loading " + self.name + " from: " + str(self.path))
            with open(self.path, 'rb') as f:
                return pickle.load(f)
        else:
            logging.debug("Could not find assets.pkl, empty list returned")
            return []  # return empty list if not found

    def save(self):
        with open(self.path, 'wb') as out:
            pickle.dump(self.list, out)

    def remove(self, name):
        for item in self.list:
            if name == item.asset.name:
                self.list.remove(item)
        self.save()

    def getIndex(self, asset):
        i = 0  # find index of item in assets list
        for item in self.list:
            if item.name == asset.name:
                break
            i += 1
        return i

    def getItem(self, name):
        for item in self.list:
            if item.name == name:
                return item

        logging.error("Could not find item in assets")

    def update(self, i, installed=False, time=datetime.now()):
        self.list[i].installed = installed
        if installed:
            self.list[i].installedText = "Installed"
        else:
            self.list[i].installedText = "Not"
        self.list[i].installedTime = time
        self.list[i].updateText()
        self.save()


class AssetItem(object):
    """description of class"""

    def __init__(self, name, path=None, installed=False):
        self.name = name
        if path is None:  # end construction if path is not supplied,
            return  # empty AssetItem with a name only
        self.path = path
        if self.path.is_dir():
            self.zip = False
            self.pkl = False
        else:
            self.zip = Path(path).with_suffix('.zip')
            self.pkl = Path(path).with_suffix('.pkl')
        self.suffix = 'MB'
        self.size = self.calcSize()
        self.installed = installed
        self.installedText = 'Not'
        self.installedTime = None
        self.updateText()

    def __lt__(self, other):
        return self.name < other.name

    def calcSize(self, places=2):
        if not self.path.exists() and self.path.suffix == '':
            os.mkdir(self.path)
            return 0

        size = self.path.stat().st_size
        rnd = places * 10

        if size > 2 ** 30:
            size /= 2 ** 30
            self.suffix = 'GB'
        else:
            size /= 2 ** 20
            self.suffix = 'MB'

        return int(size * rnd) / rnd  #

    def getSize(self):
        return str(self.size) + ' ' + self.suffix

    def createPkl(self):
        if not self.zip.exists():
            logging.debug("Cannot open " + self.zip.name + " in " + self.zip.parent)
            return

        zfile = ZipFile(self.zip)
        namelist = zfile.namelist()
        pkl = []

        for member in namelist:
            if "Manifest" in member or "Supplement" in member: continue
            member = manage.cleanPath(member)
            pkl.append(member)

        with open(self.pkl, 'wb') as out:
            pickle.dump(pkl, out)
        logging.debug(self.name + ".pkl created in " + str(self.path.parent))

    def updateText(self):
        if self.installed:
            self.installedText = "Installed"
        else:
            self.installedText = "Not"