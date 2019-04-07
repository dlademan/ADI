from pathlib import Path
import pickle
import os
import logging


class Config():

    def __init__(self, filename='config.pkl'):
        self.path = Path(filename)

        if self.path.exists():
            logging.debug("config.pkl found")
            with open(self.path, 'rb') as f:
                self.file = pickle.load(f)
            self.archive = self.file[0]
            self.library = self.file[1]
        else:
            logging.warning("config.pkl not found, creating new")
            rootPath = os.path.abspath(os.sep)
            self.archive = rootPath / Path("Asset Archive")
            self.library = rootPath / Path("Daz3D Library")
            self.file = [self.archive, self.library]

        self.saveConfig(self.archive, self.library)

    def saveConfig(self, archive, library):
        self.file = [archive, library]

        with open(self.path, 'wb') as out:
            pickle.dump(self.file, out)
