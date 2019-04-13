from pathlib import Path
from configobj import ConfigObj
import logging
import platform
import os
import wx


class Config():

    def __init__(self, parent, filename='config.ini'):
        self.path = self.getConfigPath() / Path(filename)
        self.parent = parent

        if self.path.exists():
            self._confObj = ConfigObj(str(self.path))

            self.archive = Path(self._confObj['archive'])
            self.library = Path(self._confObj['library'])
            self.clearQueue = self._confObj.as_bool('clearQueue')
            self.winSize = wx.Size((int(self._confObj['winSize'][0]),
                                    int(self._confObj['winSize'][1])))
            self.firstTime = self._confObj.as_bool('firstTime')
            self.save()

        else:
            self._confObj = ConfigObj()
            self._confObj.filename = self.path

            self._confObj['archive'] = self.getDefaultArchivePath()
            self.archive = Path(self._confObj['archive'])

            self._confObj['library'] = self.getDefaultLibraryPath()
            self.library = Path(self._confObj['library'])

            self._confObj['clearQueue'] = True
            self.clearQueue = True

            self._confObj['winSize'] = wx.Size(950, 800)
            self.winSize = wx.Size(950, 800)

            self._confObj['firstTime'] = True
            self.firstTime = True

    def save(self):

        self._confObj['archive'] = self.archive
        self._confObj['library'] = self.library
        self._confObj['clearQueue'] = self.clearQueue
        self._confObj['winSize'] = self.winSize.Get()
        self._confObj['firstTime'] = self.firstTime

        if not self.path.parent.exists():
            Path.mkdir(self.path.parent, parents=True)

        self._confObj.write()

    @staticmethod
    def getConfigPath():
        sys = platform.system()

        if sys == 'Windows':
            return Path(os.getenv('APPDATA') + '/ADI/')
        elif sys == 'Darwin':  # mac
            return Path(os.path.expanduser('~/Library/Application Support/ADI/'))
        else:  # linux
            return Path(os.path.expanduser('~/.ADI/'))

    @staticmethod
    def getDefaultLibraryPath():
        sys = platform.system()

        if sys == 'Windows':
            return Path('C:/Users/Public/Documents/My DAZ 3D Library/')
        elif sys == 'Darwin':  # mac
            return Path(os.path.expanduser('~/Studio3D/DazStudio/Content/'))
        else:  # linux
            return Path(os.path.expanduser('~/Daz3D Library/'))

    @staticmethod
    def getDefaultArchivePath():
        sys = platform.system()

        if sys == 'Windows':
            return Path('C:/Users/Public/Documents/DAZ 3D/InstallManager/Downloads')
        elif sys == 'Darwin':  # mac
            return Path(os.path.expanduser('~/Studio3D/DazStudio/InstallManager/Download/'))
        else:  # linux
            return Path(os.path.expanduser('~/Daz3D Zips/'))
