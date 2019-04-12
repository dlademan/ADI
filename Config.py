from pathlib import Path
from configobj import ConfigObj
import logging
import platform
import os
import wx


class Config():

    def __init__(self, parent, filename='config.ini'):
        self.path = self._getConfigPath(filename)
        self.parent = parent

        if self.path.exists():
            self._confObj = ConfigObj(str(self.path))

            self.archive = Path(self._confObj['archive'])
            self.library = Path(self._confObj['library'])
            self.clearQueue = self._confObj.as_bool('clearQueue')
            self.winSize = wx.Size((int(self._confObj['winSize'][0]),
                                    int(self._confObj['winSize'][1])))
            self.firstTime = self._confObj.as_bool('firstTime')

        else:
            self._confObj = ConfigObj()
            self._confObj.filename = self.path

            self._confObj['archive'] = 'C:/Daz3D Zips/'
            self.archive = Path(self._confObj['archive'])

            self._confObj['library'] = 'C:/Users/Public/Documents/My DAZ 3D Library/'
            self.library = Path(self._confObj['library'])

            self._confObj['clearQueue'] = True
            self.clearQueue = True

            self._confObj['winSize'] = wx.Size(950, 800)
            self.winSize = wx.Size(950, 800)

            self._confObj['firstTime'] = True
            self.firstTime = True

        self.save()

    def save(self):

        self._confObj['archive'] = self.archive
        self._confObj['library'] = self.library
        self._confObj['clearQueue'] = self.clearQueue
        self._confObj['winSize'] = self.winSize.Get()
        self._confObj['firstTime'] = self.firstTime

        if not self.path.parent.exists():
            os.mkdir(self.path.parent)

        self._confObj.write()

    @staticmethod
    def _getConfigPath(filename):
        sys = platform.system()

        if sys == 'Windows':
            root = Path(os.getenv('APPDATA'))
            path = Path('ADI/' + filename)
        elif sys == 'Darwin':  # mac
            root = Path('~/Library/Application Support/')
            path = Path('ADI/' + filename)
        else:  # linux
            root = Path('~/.ADI/')
            path = Path(filename)

        return root / path
