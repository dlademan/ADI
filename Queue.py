import logging
import pickle
from datetime import datetime
from pathlib import Path
import os


class QueueList(object):
    """ADI Queue Class"""

    def __init__(self, parent, name='queue.pkl', clear=False):
        self.name = name
        self.parent = parent
        self.path = parent.config.library / Path(self.name)

        self.clear = clear
        self.list = self.load()
        self.inProgress = False
        self.save()

    def append(self, asset, process, queuedTime=datetime.now(), status=0, finishedTime=None):
        item = Item(asset, process, queuedTime, status, finishedTime)
        self.list.append(item)
        self.save()

    def load(self):
        if self.clear:
            return []
        elif self.path.exists():
            logging.debug("Loading " + self.name + " from: " + str(self.path))
            with open(self.path, 'rb') as f:
                return pickle.load(f)
        else:
            return []  # return empty list if not found

    def save(self):
        if not self.path.parent.exists():
            os.mkdir(self.path.parent)
        with open(self.path, 'wb') as out:
            pickle.dump(self.list, out)

    def remove(self, name=False, asset=False):
        if asset:
            self.list.remove(asset)
            return

        for item in self.list:
            if name == item.asset.name:
                self.list.remove(item)

        self.parent.GUIQueue()

        self.save()

    def getIndex(self, name):
        i = 0  # find index of item in assets list
        for item in self.list:
            if item.name == name:
                break
            i += 1
        return i

    def updateStatus(self, i, status):
        self.list[i].status = status
        if status == 2:
            self.list[i].finishedTime = datetime.now()
        self.list[i].updateText()
        self.save()


class Item(object):

    def __init__(self, asset, process, queuedTime=datetime.now(), status=0, finishedTime=None):
        # required
        self.asset = asset
        self.process = process
        self.status = status
        self.statusText = "Queued"
        self.processText = "Install"
        self.updateText()

        # defaulted
        self.queuedTime = queuedTime
        self.finishedTime = finishedTime

    def updateText(self):
        if self.process:
            self.processText = "Install"
        else:
            self.processText = "Uninstall"

        statusList = ['Queued', 'In Progress', 'Finished', 'Failed']
        self.statusText = statusList[self.status]
