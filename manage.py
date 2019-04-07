from zipfile import ZipFile
from pathlib import Path
import shutil, os, pickle, logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')


def installAsset(self, path):
    z = ZipFile(path)

    infolist = z.infolist()
    namelist = z.namelist()
    asset = []

    self.gaugeAsset.SetRange(len(namelist))
    self.gaugeAsset.SetValue(0)
    i = 1
    for member in namelist:
        self.gaugeAsset.SetValue(i)
        i += 1
        if "Manifest" in member or "Supplement" in member: continue
        source = z.open(member)
        member = cleanPath(member)
        dest = self.config.library / member
        asset.append(member)

        if not Path.exists(dest.parent):  # if folder does not exist
            Path.mkdir(dest.parent)  # create folder

        if dest.suffix:
            try:
                with source, open(dest, 'wb') as out:
                    shutil.copyfileobj(source, out)
            except:
                print("Could not extract file " + dest.name)
        try:
            self.queueWindow.incrementAssetGauge()
        except:
            True

    pickleDest = Path(str(path.parent) + "/" + path.stem + ".pkl")
    logging.debug(path.stem + ".pkl created in " + str(path.parent))
    with open(pickleDest, 'wb') as out:
        pickle.dump(asset, out)
    z.close()


def cleanPath(path):
    if path[:8] == "Content/":
        path = path[8:]
    elif path[:11] == "My Library/":
        path = path[11:]
    return path


def uninstallAsset(self, path):
    err = False
    with open(path.with_suffix(".pkl"), 'rb') as f:
        pickList = pickle.load(f)
    self.gaugeAsset.SetRange(len(pickList))
    self.gaugeAsset.SetValue(0)
    i = 1
    for local in pickList:
        self.gaugeAsset.SetValue(i)
        full = self.config.library / Path(local)
        try:
            if not full.is_dir():
                os.unlink(full)
            elif os.path.isdir(path):
                shutil.rmtree(path)
        except OSError as e:
            err = True
        i += 1
    if err: logging.warning("One or more files could not be found to be deleted")
    removeEmptyDirs(self.config.library)


def resetLibrary(self):
    libraryPath = self.config.getLibraryRoot()
    for file in os.listdir(libraryPath):
        path = Path.joinpath(libraryPath, file)
        try:
            if os.path.isfile(path):
                os.unlink(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
        except Exception as e:
            logging.debug(e)


def removeEmptyDir(path):
    try:
        os.rmdir(path)
    except Exception as e:
        e


def removeEmptyDirs(path):
    for root, dirnames, filenames in os.walk(path, topdown=False):
        for dirname in dirnames:
            removeEmptyDir(os.path.realpath(os.path.join(root, dirname)))


def setInstalled(self, installed):
    installedLoc = self.config.getLibraryRoot() / Path("installed.pickle")
    logging.debug("Saving installed.pickle to: " + str(installedLoc))
    with open(installedLoc, 'wb') as out:
        pickle.dump(installed, out)


def getInstalled(self):
    installed = []
    installedLoc = self.config.getLibraryRoot() / Path("installed.pickle")

    if installedLoc.exists():
        logging.debug("Reading installed.pickle from: " + str(installedLoc))
        with open(installedLoc, 'rb') as f:
            installed = pickle.load(f)

    return installed
