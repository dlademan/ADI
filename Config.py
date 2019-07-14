from pathlib import Path
from configobj import ConfigObj
import logging
import platform
import pickle
import os
import wx


class Config:

    def __init__(self, parent, other=None):
        self.parent = parent

        logging.info("Loading Config")
        config_path = self.get_config_path()
        self.config_path = config_path / Path('config.ini')
        self.debug_path = config_path / Path('debug.ini')
        self.dimensions_path = config_path / Path('dimensions.pkl')
        self.backup_path = config_path / Path('backup')

        if other is not None:
            self.copy_constructor(other)
            return

        if not self.backup_path.exists():
            self.backup_path.mkdir(parents=True)

        if self.debug_path.exists() and self.dimensions_path.exists():
            self.load_debug()
            self.load_dimensions()
        elif self.config_path.exists() and self.dimensions_path.exists():
            self.load_config()
            self.load_dimensions()
        elif self.config_path.exists():
            self.load_config()
            self.create_dimensions(False)
        else:
            self.create_config()
            self.create_dimensions()

    def copy_constructor(self, other):
        self.create_config()

        self.__dict__ = other.__dict__.copy()

        if len(self._dimensions) < 4:
            self._dimensions.append('')
            self.version = ''

        if not hasattr(self, "detect"):
            self._config['detect'] = self.detect = True

        self.save_config()
        self.save_dimensions()

    def load_debug(self):
        self._config_debug = ConfigObj(str(self.debug_path))

        self.archive = Path(self._config['archive'])
        self.library = Path(self._config['library'])
        self.clear_queue = self._config.as_bool('clear_queue')
        self.expand = self._config.as_bool('expand')
        self.close_dialog = self._config.as_bool('close_dialog')
        self.detect = self._config.as_bool('detect')

    def load_config(self):
        logging.info("Loading config")
        self._config = ConfigObj(str(self.config_path))

        if "archive" in self._config.keys():
            self.archive = Path(self._config['archive'])
        else:
            self._config['archive'] = self.archive = self.get_default_archive_path()

        if "library" in self._config.keys():
            self.library = Path(self._config['library'])
        else:
            self._config['library'] = self.library = self.get_default_library_path()

        if "clear_queue" in self._config.keys():
            self.clear_queue = self._config.as_bool('clear_queue')
        else:
            self._config['clear_queue'] = self.clear_queue = True

        if "expand" in self._config.keys():
            self.expand = self._config.as_bool('expand')
        else:
            self._config['expand'] = self.expand = True

        if "close_dialog" in self._config.keys():
            self.close_dialog = self._config.as_bool('close_dialog')
        else:
            self._config['close_dialog'] = self.close_dialog = True

        if "detect" in self._config.keys():
            self.detect = self._config.as_bool('detect')
        else:
            self._config['detect'] = self.detect = True

    def save_config(self):
        logging.info("Saving config")
        if not self.config_path.parent.exists():
            Path.mkdir(self.config_path.parent, parents=True)

        self._config['archive'] = self.archive
        self._config['library'] = self.library
        self._config['clear_queue'] = self.clear_queue
        self._config['expand'] = self.expand
        self._config['close_dialog'] = self.close_dialog
        self._config['detect'] = self.detect
        self._config.write()

    def create_config(self):
        self._config = ConfigObj()
        self._config.filename = self.config_path

        self._config['archive'] = self.archive = self.get_default_archive_path()
        self._config['library'] = self.library = self.get_default_library_path()
        self._config['clear_queue'] = self.clear_queue = True
        self._config['expand'] = self.expand = True
        self._config['close_dialog'] = self.close_dialog = False
        self._config['detect'] = self.detect = False

        # create dimensions if config is wiped #
        self.create_dimensions()

    def load_dimensions(self):
        logging.info("Loading dimensions")
        with open(self.dimensions_path, "rb") as f:
            self._dimensions = pickle.load(f)

        if len(self._dimensions) > 0:
            self.win_size = self._dimensions[0]
        else:
            self.win_size = (1300, 800)
            self._dimensions.append(self.win_size)

        self.win_pos = self._dimensions[1]
        if len(self._dimensions) > 1:
            self.win_pos = self._dimensions[1]
        else:
            self.win_pos = self.parent.GetPosition().Get()
            self._dimensions.append(self.win_pos)

        self.first = self._dimensions[2]
        if len(self._dimensions) > 2:
            self.first = self._dimensions[2]
        else:
            self.first = True
            self._dimensions.append(self.first)

        if len(self._dimensions) > 3:
            self.version = self._dimensions[3]
        else:
            self.version = ""
            self._dimensions.append(self.version)

    def save_dimensions(self):
        logging.info("Saving dimensions")
        self._dimensions[0] = self.win_size
        self._dimensions[1] = self.win_pos
        self._dimensions[2] = False
        self._dimensions[3] = self.version

        with open(self.dimensions_path, 'wb') as out:
            pickle.dump(self._dimensions, out)

        root_file_path = self.archive / Path('root.pkl')
        with open(root_file_path, 'wb') as out:
            pickle.dump(None, out)

    def create_dimensions(self, first=True):
        self._dimensions = []
        self.win_size = (1300, 800)
        self._dimensions.append(self.win_size)

        self.win_pos = self.parent.GetPosition().Get()
        self._dimensions.append(self.win_pos)

        self.first = first
        self._dimensions.append(self.first)

        self.version = ''
        self._dimensions.append(self.first)

    @staticmethod
    def get_config_path():
        sys = platform.system()

        if sys == 'Windows':
            return Path(os.getenv('APPDATA') + '/ADI/')
        elif sys == 'Darwin':  # mac
            return Path(os.path.expanduser('~/Library/Application Support/ADI/'))
        else:  # linux
            return Path(os.path.expanduser('~/.ADI/'))

    @staticmethod
    def get_default_library_path():
        sys = platform.system()

        if sys == 'Windows':
            return Path('C:/Users/Public/Documents/My DAZ 3D Library/')
        elif sys == 'Darwin':  # mac
            return Path(os.path.expanduser('~/Studio3D/DazStudio/Content/'))
        else:  # linux
            return Path(os.path.expanduser('~/Daz3D Library/'))

    @staticmethod
    def get_default_archive_path():
        system = platform.system()

        if system == 'Windows':
            return Path('C:/Users/Public/Documents/DAZ 3D/InstallManager/Downloads')
        elif system == 'Darwin':  # mac
            return Path(os.path.expanduser('~/Studio3D/DazStudio/InstallManager/Download/'))
        else:  # linux
            return Path(os.path.expanduser('~/Daz3D Zips/'))
