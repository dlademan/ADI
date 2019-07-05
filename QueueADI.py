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

        self.list = []
        self.in_progress = False
        self.save()

    def append(self, asset, process, queuedTime=datetime.now(), status=0, finishedTime=None):
        item = Item(asset, process, queuedTime, status, finishedTime)
        self.list.append(item)
        self.save()

    def load(self):
        if self.parent.config.first:
            return []
        elif self.path.exists():
            logging.info("Loading " + self.name + " from: " + str(self.path))
            with open(self.path, 'rb') as f:
                return pickle.load(f)
        else:
            return []  # return empty list if not found

    def save(self):
        if not self.path.parent.exists():
            os.mkdir(self.path.parent)
        with open(self.path, 'wb') as out:
            pickle.dump(self.list, out)

    def clear_list(self):
        self.list = []

    def remove(self, product_name=False, asset=False):
        if asset:
            self.list.remove(asset)
            return

        for item in self.list:
            if product_name == item.asset.product_name:
                self.list.remove(item)

        self.parent.update_queue()
        self.save()

    def get_index(self, name):
        i = 0  # find index of item in assets list
        for item in self.list:
            if item.name == name:
                break
            i += 1
        return i

    def update_status(self, i, status):
        self.list[i].status = status
        if status == 2:
            self.list[i].finishedTime = datetime.now()
        self.save()


class Item(object):

    def __init__(self, asset, process, queuedTime=datetime.now(), status=0, finishedTime=None):
        # required
        self.asset = asset
        self.process = process
        self.status = status

        # defaulted
        self.queued_time = queuedTime
        self.finished_time = finishedTime

    @property
    def status_str(self):
        statusList = ['Queued', 'In Progress', 'Finished', 'Failed']
        return statusList[self.status]

    @property
    def process_str(self):
        if self.process:
            return "Install"
        else:
            return"Uninstall"
