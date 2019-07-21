import traceback
from datetime import datetime
from pathlib import Path
from threading import Thread
import logging
import subprocess
import wx, wx.adv
import os
import sys
import platform
import winsound
import pickle

from Asset import AssetList, AssetItem
from QueueADI import QueueList
from Config import Config
from ConfigFrame import ConfigFrame
from AboutFrame import AboutFrame
from Tree import FolderTree, ZipTree
from InstallDialog import InstallDialog
from MessageDialog import MessageDialog


class MainFrame(wx.Frame):
    """
    Main frame window of ADI

    parent, id, title
    """

    version = "1.5.3"
    logger = logging.getLogger()

    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, wx.DefaultPosition, (1300, 800), style=wx.DEFAULT_FRAME_STYLE)
        self.show_splash()

        self.config = Config(self)
        self.create_logger()

        sys.excepthook = self.excepthook
        logging.info("------------ ADI V" + self.version + " Started")

        self.assets = AssetList(self)
        self.queue = QueueList(self)
        if self.config.clear_queue and not self.queue.in_progress:
            self.queue.clear_list()

        self.check_version()
        self.create_menubar()
        self.create_toolbar()
        self.create_body()

        if self.config.first:
            self.splash.Close()
            self.setup_window = ConfigFrame(self)
        else:
            self.splash.Close()
            self.show_main()

    def show_main(self):
        self.Bind(wx.EVT_CLOSE, self.on_quit)
        self.Bind(wx.EVT_IDLE, self.on_idle)

        self.SetSize(wx.Size(self.config.win_size))
        self.SetPosition(self.config.win_pos)

        if self.queue.in_progress:
            dialog_in_progress = wx.MessageDialog(self,
                                                  'ADI was closed without completing it\'s queue. '
                                                  'Would you like to keep the queue?\n\n',
                                                  style=wx.YES_NO | wx.STAY_ON_TOP)

            dialog_in_progress.Center()
            clear = dialog_in_progress.ShowModal()

            if clear == wx.ID_YES:
                self.queue.clear_list()
                self.queue.save()
                self.update_queue()

        if self.config.detect: self.detect_directory()
        else: self.update_all()
        self.Show()

    def show_splash(self):
        bmp_splash = wx.Bitmap('icons/about.png', wx.BITMAP_TYPE_PNG)
        splashStyle = wx.adv.SPLASH_CENTRE_ON_SCREEN

        # self.splash = AboutFrame(splash=True)

        self.splash = wx.adv.SplashScreen(bmp_splash, splashStyle, 2000, None, -1,
                                          wx.DefaultPosition,
                                          wx.DefaultSize,
                                          wx.BORDER_SIMPLE)

        # self.splash.Bind(wx.EVT_CLOSE, self.on_splash_close)

    def on_splash_close(self, event=None):
        self.Show()
        event.Skip()

    def check_version(self):
        if not hasattr(self.config, "version") or self.config.version != self.version:
            dialog = MessageDialog(parent=self, message="Upgrading database...")

            logging.info("Upgrading database")
            self.config = Config(self, self.config)
            for i, asset in enumerate(self.assets.list):
                self.assets.list[i] = AssetItem(other=asset)

            self.config.version = self.version

            dialog.on_close()

    def database_upgrade_worker(self, dialog):
        logging.info("Upgrading database...")
        self.Config = Config(self, self.config)
        for asset in self.assets.list:
            asset = AssetItem(other=asset)

        dialog.on_close()

    def resize_columns(self, event=None):
        w, h = self.GetSize().Get()
        self.ctrl_asset.SetColumnWidth(0, w / 2 - 209)
        self.ctrl_queue.SetColumnWidth(0, w / 2 - 250)

    def in_progress_dialog(self):
        pass

    def show_readme(self, event=None):
        logging.debug("Show Readme")

        path_readme = Path.cwd() / Path('Readme_.txt')

        if path_readme.exists():
            os.startfile(path_readme)
        else:
            os.startfile(Path.cwd().parent / 'Documents' / Path('Readme_.txt'))

    def show_log(self, event=None):
        logging.debug("Show log")
        os.startfile(str(self.config.get_config_path()) + '/log.txt')

    def show_settings(self, event=None):
        logging.info("ConfigFrame shown")
        self.setup_window = ConfigFrame(self)

    def show_about(self, event=None):
        logging.info("AboutFrame shown")
        self.about_window = AboutFrame(self)

    def disable_frame(self, event=None):
        # wx.BeginBusyCursor()
        self.splitter.Disable()

    def enable_frame(self, event=None):
        # wx.SafeYield(self)
        self.splitter.Enable()
        # wx.EndBusyCursor()

    def on_asset_install(self, event, asset):
        dialog = InstallDialog(self,
                                    title="Install Dialog",
                                    processes=["Installing " + asset.product_name])

        thread_install = Thread(target=self.asset_install_worker,
                                args=[event, asset, dialog])
        thread_install.start()

    def asset_install_worker(self, event, asset, dialog):
        self.disable_frame()
        dialog.button_close.Disable()

        asset.install(self, self.config.library, gauge=dialog.gauges[0])
        self.assets.save()
        dialog.button_close.Enable()

        if self.config.close_dialog:
            dialog.on_close(event)

        self.update_all()
        self.enable_frame()
        self.sound_action_complete()

    def on_asset_uninstall(self, event, asset):
        dialog = InstallDialog(self, title="Uninstall Dialog",
                               processes=["Uninstalling " + asset.product_name])

        thread_uninstall = Thread(target=self.asset_uninstall_worker,
                                  args=[event, asset, dialog])
        thread_uninstall.start()

    def asset_uninstall_worker(self, event, asset, dialog):
        self.disable_frame()
        dialog.button_close.Disable()
        asset.uninstall(self, self.config.library, gauge=dialog.gauges[0])
        self.assets.save()
        dialog.button_close.Enable()

        if self.config.close_dialog:
            dialog.on_close(event)

        self.update_all()
        self.enable_frame()
        self.sound_action_complete()

    def on_queue_directory(self, directory, process):
        self.right_notebook.SetSelection(1)
        for asset in self.assets.list:
            if str(directory) in str(asset.path.parent):
                if process and not asset.installed:
                    self.queue_append(asset, process)
                elif not process and asset.installed:
                    self.queue_append(asset, process)

    def on_merge_backup(self, event=None):
        logging.info("Merging backups into database")
        path = self.config.backup_path
        pkls = list(path.glob('**/*.pkl'))
        imported = 0

        for pkl in pkls:
            asset = self.assets.get_item(file_name=pkl.with_suffix('.zip').name)
            if asset is None:
                logging.info("Merging " + str(pkl.name) + " into assets database")
                with open(pkl, "rb") as f:
                    asset = pickle.load(f)
                asset.detect(self)
                self.assets.list.append(asset)
                imported += 1

        self.assets.list.sort()
        self.update_all()
        # self.detect_directory()

    def on_detect_asset(self, asset):
        detect_thread = Thread(target=asset.detect,
                               args=[self, True])
        detect_thread.start()

    def detect_directory(self, event=None, directory=None, wait=False):

        dialog = MessageDialog(parent=self, message="Detecting assets...")

        detect_thread = Thread(target=self.detect_directory_worker,
                               args=[directory, dialog])
        detect_thread.start()

    def detect_directory_worker(self, directory=None, dialog=None):
        self.disable_frame()
        if directory is None:
            directory = self.config.archive

        threads = []
        for asset in self.assets.list:
            if str(directory) in str(asset.path):
                t = Thread(target=asset.detect, args=[self])
                threads.append(t)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        logging.info("Detection complete")
        if dialog is not None:
            dialog.on_close()

        self.update_all()
        self.enable_frame()

    def queue_process(self, event):
        processes = []
        self.right_notebook.SetSelection(1)

        if len(self.queue.list) == 0:
            queue_dialog = wx.MessageDialog(self, 'Cannot Start Queue, no processes in queue.',
                                            style=wx.OK | wx.STAY_ON_TOP | wx.ICON_ERROR)
            queue_dialog.ShowModal()
            return

        for item in self.queue.list:
            if item.status != 2:
                if item.process:
                    process = "Installing"
                else:
                    process = "Uninstalling"
                processes.append(process + ' ' + item.asset.product_name)

        dialog = InstallDialog(self, processes=processes)

        queue_thread = Thread(target=self.queue_process_worker, args=[dialog])
        queue_thread.start()

    def queue_process_worker(self, dialog):
        dialog.button_close.Disable()
        self.queue.in_progress = True
        self.queue.save()
        logging.info("Starting Queued Processes")

        queue_length = 0
        for item in self.queue.list:
            if item.status != 2:
                queue_length += 1
        threads = []
        current_gauge = 0
        for queue_index, queue_item in enumerate(self.queue.list):
            if self.queue.list[queue_index].status == 2:  # skip finished queue items
                continue
            # ['Queued', 'In Progress', 'Finished', 'Failed']
            self.queue.update_status(queue_index, 1)
            self.queue.save()
            self.update_queue()

            if queue_item.process:
                queue_index = Thread(target=queue_item.asset.install,
                                     args=[self, self.config.library, queue_index, dialog.gauges[current_gauge]])
                threads.append(queue_index)
            else:
                u = Thread(target=queue_item.asset.uninstall,
                           args=[self, self.config.library, queue_index, dialog.gauges[current_gauge]])
                threads.append(u)

            current_gauge += 1

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        dialog.button_close.Enable()

        if self.config.close_dialog:
            dialog.on_close()

        self.assets.save()
        self.update_all()
        self.queue.in_progress = False
        self.sound_queue_complete()
        logging.info("Queued Processes Finished")

    def queue_clear(self, event):
        self.ctrl_queue.DeleteAllItems()
        self.queue.clear_list()

    def queue_append(self, asset, process):
        self.right_notebook.SetSelection(1)
        for queueItem in self.queue.list:
            if asset.file_name == queueItem.asset.file_name and queueItem.status == 0:
                logging.warning(asset.product_name + " already queued for process, nothing added to queue")
                return

        if process:
            logging.info("Added " + asset.product_name + " to queue to be installed.")
        else:
            logging.info("Added " + asset.product_name + " to queue to be uninstalled.")

        self.queue.append(asset, process)
        self.update_queue()

    def queue_append_list(self, assetList, process):
        for asset in assetList:
            self.queue_append(asset, process)

    def update_all(self):
        self.update_assets()
        self.update_queue()

    def update_assets(self):
        self.ctrl_asset.DeleteAllItems()
        term = self.textctrl_filter.GetLineText(0).lower().replace(' ', '')
        i = 0
        for asset in self.assets.list:
            product_name = asset.product_name.lower().replace(' ', '')
            if term in product_name and (self.filter_installed and not asset.installed):
                continue
            elif term in product_name and (self.filter_not_installed and asset.installed):
                continue
            elif term in product_name and (self.filter_zip and not asset.zip.exists()):
                continue
            elif term in product_name or term in asset.tags:
                self.ctrl_asset.InsertItem(i, asset.product_name)
                self.ctrl_asset.SetItem(i, 1, asset.zip_str)
                self.ctrl_asset.SetItem(i, 2, asset.size_display)
                self.ctrl_asset.SetItem(i, 3, asset.imported_time_str)
                self.ctrl_asset.SetItem(i, 4, asset.installed_time_str)

                i += 1

    def update_queue(self):
        self.ctrl_queue.DeleteAllItems()
        for i, item in enumerate(self.queue.list):
            self.ctrl_queue.InsertItem(i, item.asset.product_name)
            self.ctrl_queue.SetItem(i, 1, item.process_str)
            self.ctrl_queue.SetItem(i, 2, item.asset.installed_str)
            self.ctrl_queue.SetItem(i, 3, item.status_str)

    def update_library_tree(self, event=None):
        self.tree_library.make()
        self.update_all()

    def on_quit(self, event):
        self.config.save_config()
        self.config.save_dimensions()
        self.assets.save()
        logging.info("------------ ADI Closed")
        self.Destroy()

    def on_col_click(self, event=None):
        col = event.GetColumn()
        method = None

        if col == 0:
            method = "name"
        elif col == 1:
            method = "zip"
        elif col == 2:
            method = "size"
        elif col == 3:
            method = "import_time"
        elif col == 4:
            method = "installed"
        elif col == 5:
            method = "installed_time"

        self.assets.sort(method)
        self.update_all()

    def on_button1(self, event):
        if self.button1.GetLabel() == "Queue Install":
            self.queue_append(self.selected, True)
        elif self.button1.GetLabel() == "Queue Uninstall":
            self.queue_append(self.selected, False)
        else:
            logging.warning("No Action performed on button1 press")

    def on_button2(self, event):
        if self.button2.GetLabel() == "Install":
            self.on_asset_install(event, self.selected)
        elif self.button2.GetLabel() == "Uninstall":
            self.on_asset_uninstall(event, self.selected)
        else:
            logging.warning("No Action performed on button2 press")

    def on_button_reset_filters(self, event=None):
        self.filter_installed = False
        self.filter_not_installed = False
        self.filter_zip = False

        self.textctrl_filter.SetValue('')
        self.checkbox_installed.SetValue(False)
        self.checkbox_not_installed.SetValue(False)
        self.checkbox_zip.SetValue(False)

        self.on_refresh()

    def on_checkbox_installed(self, event):
        if self.checkbox_installed.IsChecked():
            self.filter_installed = True
            self.filter_not_installed = False
            self.checkbox_not_installed.SetValue(False)
        else:
            self.filter_installed = False
        self.update_assets()
        # self.tree_displayed.make()

    def on_checkbox_not_installed(self, event):
        if self.checkbox_not_installed.IsChecked():
            self.filter_installed = False
            self.filter_not_installed = True
            self.checkbox_installed.SetValue(False)
        else:
            self.filter_not_installed = False
        self.update_assets()
        # self.tree_displayed.make()

    def on_checkbox_zip(self, event=None):
        self.filter_zip = not self.filter_zip
        self.update_all()
        self.tree_library = self.tree_zip
        # self.tree_displayed.make()

    def on_idle(self, event):
        self.config.win_size = self.GetSize().Get()
        self.config.win_pos = self.GetPosition().Get()
        event.Skip()

    def open_directory(self, event, path=None):
        if not path: path = self.config.archive
        if not path.is_dir():
            subprocess.Popen(r'explorer /select, ' + str(path))
        else:
            subprocess.Popen(r'explorer ' + str(path))

    def on_open_archive(self, event):
        self.open_directory(event, self.config.archive)

    def on_open_library(self, event):
        self.open_directory(event, self.config.library)

    def on_filter_text(self, event):
        if self.notebook_library.GetSelection() == 1:
            self.update_assets()

    def on_filter_text_enter(self, event):
        if self.notebook_library.GetSelection() == 0:
            self.update_library_tree(event)

    def on_notebook_change(self, event=None):
        if self.notebook_library.GetSelection() == 0:
            self.checkbox_installed.Disable()
            self.checkbox_not_installed.Disable()
            self.checkbox_zip.Disable()
        elif self.notebook_library.GetSelection() == 1:
            self.checkbox_installed.Enable()
            self.checkbox_not_installed.Enable()
            self.checkbox_zip.Enable()


    def on_refresh(self, event=None):
        self.disable_frame()
        dialog = MessageDialog(parent=self, message="Refreshing folders and files...")

        refresh_thread = Thread(target=self.on_refresh_worker,
                                args=[dialog])
        refresh_thread.start()

    def on_refresh_worker(self, dialog):
        self.tree_library.make()
        self.update_all()
        dialog.on_close()
        self.enable_frame()

    def on_reimport_assets(self, event):
        self.disable_frame()
        dialog = MessageDialog(parent=self, message="Reimporting and detecting assets...")

        reimport_thread = Thread(target=self.reimport_assets_worker,
                                 args=[dialog])
        reimport_thread.start()

    def reimport_assets_worker(self, dialog):
        logging.info("Removing stored asset info and reimporting")
        self.assets = AssetList(self, clear=True)
        dialog.text_message.SetLabel("Reimporting assets...")
        self.tree_library.make()

        detect_thread = Thread(target=self.detect_directory_worker, args=[None])
        dialog.text_message.SetLabel("Detecting assets...")
        detect_thread.start()
        detect_thread.join()

        dialog.on_close()
        self.enable_frame()

    def on_clean_library(self, event):
        clean_thread = Thread(target=self.assets.clean())
        clean_thread.start()

    def on_list_sel(self, event):
        item = event.GetItem()
        self.selected = asset = self.assets.get_item(product_name=event.GetItem().GetText())
        if asset is None: return
        count = self.ctrl_asset.GetSelectedItemCount()


        if count == 1:
            self.label_filename.Enable()
            self.label_filename.SetLabel(asset.zip.name)
            self.label_name.Enable()
            self.label_name.SetLabel(asset.product_name)
            if asset.zip.exists():
                self.tree_zip.remake(asset.zip)
            else:
                self.tree_zip.remake()

            if asset.zip.exists():
                self.label_size.SetLabel('Size: ' + asset.size_display)
                self.label_zip.SetLabel('Zip: Exists')
            else:
                self.label_size.SetLabel('Size: N/A')
                self.label_zip.Disable()

            if asset.installed:
                self.button1.SetLabel("Queue Uninstall")
                self.button2.SetLabel("Uninstall")
                self.label_installed.SetLabel('Installed: True')
                self.button1.Enable()
                self.button2.Enable()
            elif asset.zip.exists() and not asset.installed:
                self.button1.SetLabel("Queue Install")
                self.button2.SetLabel("Install")
                self.label_installed.SetLabel('Installed: False')
                self.button1.Enable()
                self.button2.Enable()
            elif not asset.installed and not asset.zip.exists():
                self.button1.SetLabel("Can't Queue")
                self.button2.SetLabel("Can't Install")
                self.button1.Disable()
                self.button2.Disable()

            self.label_name.SetLabel(item.GetText())
            self.label_path.SetLabel(str(asset.path.parent))

        elif count > 1:
            selected = [self.ctrl_asset.GetFirstSelected()]
            self.selected = []
            for i in range(count - 1):
                selected.append(self.ctrl_asset.GetNextSelected(selected[i]))
            for item in selected:
                product_name = self.ctrl_asset.GetItemText(item, 0)
                for asset in self.assets.list:
                    if product_name == asset.product_name:
                        self.selected.append(asset)

            self.label_name.SetLabel(str(count) + " assets selected")
            self.label_path.SetLabel("")
            self.label_zip.SetLabel("")
            self.label_size.SetLabel("")
            self.label_installed.SetLabel("")
            self.button1.Disable()
            self.button2.Disable()

    def on_list_context(self, event):
        item = event.GetItem()
        popup_menu = wx.Menu()

        count = self.ctrl_asset.GetSelectedItemCount()

        if count == 1:
            self.selected = asset = self.assets.get_item(product_name=event.GetItem().GetText())
            if asset is None: return

            if asset.installed:
                self.helper_menu_option(event, popup_menu, 'Uninstall',
                                        self.on_asset_uninstall, event, asset)
                self.helper_menu_option(event, popup_menu, 'Queue Uninstall',
                                        self.queue_append, asset, False)
                popup_menu.AppendSeparator()
            elif not asset.installed and asset.zip.exists():
                self.helper_menu_option(event, popup_menu, 'Install',
                                        self.on_asset_install, event, asset)
                self.helper_menu_option(event, popup_menu, 'Queue Install',
                                        self.queue_append, asset, True)
                popup_menu.AppendSeparator()
            if asset.zip.exists():
                self.helper_menu_option(event, popup_menu, 'Open File Location',
                                        self.open_directory, event, asset.path)

            self.helper_menu_option(event, popup_menu, 'Detect Asset', self.on_detect_asset, asset)

        elif count > 1:
            selected = [self.ctrl_asset.GetFirstSelected()]
            self.selected = []

            for i in range(count - 1):
                selected.append(self.ctrl_asset.GetNextSelected(selected[i]))

            for item in selected:
                product_name = self.ctrl_asset.GetItemText(item, 0)
                for asset in self.assets.list:
                    if product_name == asset.product_name:
                        self.selected.append(asset)

            self.helper_menu_option(event, popup_menu, 'Queue selected to be Installed',
                                    self.queue_append_list, self.selected, True)
            self.helper_menu_option(event, popup_menu, 'Queue selected to be Uninstalled',
                                    self.queue_append_list, self.selected, False)

        self.helper_menu_option(event, popup_menu, 'Refresh', self.on_refresh)
        self.PopupMenu(popup_menu, event.GetPoint())

    def on_tree_sel(self, event):
        # Get the selected item object
        item = event.GetItem()
        count = len(self.tree_library.GetSelections())

        if count > 1:
            self.selected = self.tree_library.GetSelections()
        elif self.tree_library.GetItemData(item).path.is_dir():
            self.selected = self.tree_library.GetItemData(item)
        else:
            self.selected = self.assets.get_item(self.tree_library.GetItemData(item).file_name)

        if count == 1:
            ####
            if self.selected.path.is_dir():
                self.label_name.Enable()
                self.label_installed.Disable()
                self.label_zip.Disable()
                self.label_name.SetLabel(self.selected.path.name)
                self.label_path.Enable()
                self.label_path.SetLabel(str(self.selected.path.parent))
                self.label_size.SetLabel(str(self.get_folder_size(self.selected.path)))
                return
            else:
                self.label_name.Enable()
                self.label_filename.Enable()
                self.label_zip.Enable()
                self.label_installed.Enable()
                self.label_size.Enable()
                self.label_path.Enable()

            self.label_name.SetLabel(self.selected.product_name)
            self.label_filename.SetLabel(self.selected.file_name)
            self.label_path.SetLabel(str(self.selected.path.parent))
            if self.selected.zip.exists():
                self.tree_zip.remake(self.selected.zip)
            else:
                self.tree_zip.remake()

            if self.selected.zip.exists():
                self.label_size.SetLabel('Size: ' + self.selected.size_display)
                self.label_zip.SetLabel('Zip: Exists')
            else:
                self.label_size.SetLabel('Size: N/A')
                self.label_zip.SetLabel('Zip: N/A')

            if self.selected.installed:
                self.label_installed.SetLabel('Installed: True')
            else:
                self.label_installed.SetLabel('Installed: False')
            ####
            if self.selected.installed:
                self.button1.SetLabel('Queue Uninstall')
                self.button1.Enable()
                self.button2.SetLabel('Uninstall')
                self.button2.Enable()
            elif not self.selected.installed:
                self.button1.SetLabel('Queue Install')
                self.button1.Enable()
                self.button2.SetLabel('Install')
                self.button2.Enable()
            else:
                self.button1.Disable()
                self.button2.Disable()
        elif count > 1:
            #
            self.label_name.SetLabel(str(count) + " selected")
            self.label_filename.Disable()
            self.label_path.Disable()
            #self.label_path.SetLabel(str(self.tree_library.GetItemData(self.selected[0]).path))
            self.label_zip.Disable()
            self.label_installed.Disable()
            self.label_size.Disable()


            self.panel_right.Layout()


        self.panel_right.Layout()

    def on_tree_context(self, event):
        # Get TreeItemData
        item = event.GetItem()

        # Create menu
        popup_menu = wx.Menu()
        force_menu = wx.Menu()

        count = len(self.tree_library.GetSelections())

        if count == 1:
            self.selected = asset = self.assets.get_item(self.tree_library.GetItemText(item))
            if asset is None: self.selected = asset = self.tree_library.GetItemData(item)

            if not asset.path.is_dir():

                if asset.installed:
                    self.helper_menu_option(event, popup_menu, 'Uninstall',
                                            self.on_asset_uninstall, event, asset)
                    self.helper_menu_option(event, popup_menu, 'Queue Uninstall',
                                            self.queue_append, asset, False)
                    popup_menu.AppendSeparator()

                elif not asset.installed and asset.zip.exists():
                    self.helper_menu_option(event, popup_menu, 'Install',
                                            self.on_asset_install, event, asset)
                    self.helper_menu_option(event, popup_menu, 'Queue Install',
                                            self.queue_append, asset, True)
                    popup_menu.AppendSeparator()

                # if not asset.path.is_dir():
                #     self.helper_menu_option(event, force_menu, 'Install',
                #                             self.on_asset_install, event, asset)
                #     self.helper_menu_option(event, force_menu, 'Uninstall',
                #                             self.on_asset_uninstall, event, asset)
                #     popup_menu.AppendSubMenu(force_menu, '&Force')

                if asset.zip.exists():
                    self.helper_menu_option(event, popup_menu, 'Open File Location',
                                            self.open_directory, event, asset.path)

                self.helper_menu_option(event, popup_menu, 'Detect Asset', self.on_detect_asset, asset)
            else:
                self.helper_menu_option(event, popup_menu, 'Queue directory to be installed',
                                        self.on_queue_directory, asset.path, True)
                self.helper_menu_option(event, popup_menu, 'Queue directory to be uninstalled',
                                        self.on_queue_directory, asset.path, False)
                popup_menu.AppendSeparator()
                self.helper_menu_option(event, popup_menu, 'Open Location',
                                        self.open_directory, event, asset.path)
                self.helper_menu_option(event, popup_menu, 'Detect assets in directory',
                                        self.detect_directory, event, asset.path)

        elif count > 1:
            selected = self.tree_library.GetSelections()
            self.selected = []

            for item in selected:
                product_name = self.tree_library.GetItemText(item)
                for asset in self.assets.list:
                    if product_name == asset.product_name:
                        self.selected.append(asset)

            self.helper_menu_option(event, popup_menu, 'Queue selected to be Installed',
                                    self.queue_append_list, self.selected, True)
            self.helper_menu_option(event, popup_menu, 'Queue selected to be Uninstalled',
                                    self.queue_append_list, self.selected, False)
            popup_menu.AppendSeparator()

        self.helper_menu_option(event, popup_menu, 'Refresh', self.on_refresh)
        self.PopupMenu(popup_menu, event.GetPoint())  # show menu at cursor

    def on_queue_context(self, event):
        item = event.GetItem()
        popupMenu = wx.Menu()

        self.helper_menu_option(event, popupMenu, 'Remove from queue', self.queue.remove, item.GetText())
        point = event.GetPoint()
        self.PopupMenu(popupMenu, point)

    def on_empty_context(self, event):
        popup_menu = wx.Menu() # create menu
        self.helper_menu_option(event, popup_menu, 'Refresh', self.on_refresh) # add refresh menu option
        self.PopupMenu(popup_menu, event.GetPoint())  # show menu at cursor

    def create_menubar(self):
        logging.info("Creating Menubar")
        file_menu = wx.Menu()  # file
        file_refresh = wx.MenuItem(file_menu, -1, '&Refresh')
        file_quit = wx.MenuItem(file_menu, wx.ID_EXIT, '&Quit')

        self.Bind(wx.EVT_MENU, self.on_refresh, file_refresh)
        self.Bind(wx.EVT_MENU, self.on_quit, file_quit)

        file_menu.Append(file_refresh)
        file_menu.AppendSeparator()
        file_menu.Append(file_quit)

        lib_menu = wx.Menu()
        lib_archive = wx.MenuItem(lib_menu, -1, '&Open Zip Archive')
        lib_library = wx.MenuItem(lib_menu, -1, '&Open Library')
        lib_detect = wx.MenuItem(lib_menu, -1, '&Detect Installed Assets')
        lib_merge = wx.MenuItem(lib_menu, -1, '&Merge Backed Up Assets')
        lib_reimport = wx.MenuItem(lib_menu, -1, '&Reimport All Assets')
        lib_clean = wx.MenuItem(lib_menu, -1, '&Clean Library')

        self.Bind(wx.EVT_MENU, self.on_open_archive, lib_archive)
        self.Bind(wx.EVT_MENU, self.on_open_library, lib_library)
        self.Bind(wx.EVT_MENU, self.detect_directory, lib_detect)
        self.Bind(wx.EVT_MENU, self.on_merge_backup, lib_merge)
        self.Bind(wx.EVT_MENU, self.on_reimport_assets, lib_reimport)
        self.Bind(wx.EVT_MENU, self.on_clean_library, lib_clean)

        lib_menu.Append(lib_archive)
        lib_menu.Append(lib_library)
        lib_menu.AppendSeparator()
        lib_menu.Append(lib_detect)
        lib_menu.Append(lib_merge)
        lib_menu.Append(lib_reimport)
        lib_menu.Append(lib_clean)

        view_menu = wx.Menu()
        view_settings = wx.MenuItem(view_menu, wx.ID_ANY, '&Configuration')
        view_log = wx.MenuItem(view_menu, wx.ID_ANY, '&Log')
        view_readme = wx.MenuItem(view_menu, wx.ID_ANY, '&Readme')
        view_about = wx.MenuItem(view_menu, wx.ID_ANY, '&About')

        self.Bind(wx.EVT_MENU, self.show_settings, view_settings)
        self.Bind(wx.EVT_MENU, self.show_log, view_log)
        self.Bind(wx.EVT_MENU, self.show_readme, view_readme)
        self.Bind(wx.EVT_MENU, self.show_about, view_about)

        view_menu.Append(view_settings)
        view_menu.AppendSeparator()
        view_menu.Append(view_log)
        view_menu.Append(view_readme)
        view_menu.Append(view_about)

        menu_bar = wx.MenuBar()
        menu_bar.Append(file_menu, '&File')
        menu_bar.Append(lib_menu, '&Library')
        menu_bar.Append(view_menu, '&View')
        self.SetMenuBar(menu_bar)

    def create_toolbar(self):
        logging.info("Creating Toolbar")
        # set main frame icon
        icon = wx.Icon()
        icon.CopyFromBitmap(wx.Bitmap("icons/adi_logo.png", wx.BITMAP_TYPE_ANY))
        self.SetIcon(icon)

        self.toolbar = self.CreateToolBar(style=wx.TB_HORZ_TEXT)

        self.tool_start = self.toolbar.AddTool(wx.ID_ANY, 'Start Queue',
                                               wx.Bitmap('icons/queue_start.png'),
                                               'Start the process queue')

        self.tool_clear = self.toolbar.AddTool(wx.ID_ANY, 'Clear Queue',
                                               wx.Bitmap('icons/clear_queue.png'),
                                               'Remove all items from the queue')

        self.reset_filters = self.toolbar.AddTool(wx.ID_ANY, 'Reset Filters',
                                                  wx.Bitmap('icons/clear.png'),
                                                  'Reset Filters')

        self.tool_refresh = self.toolbar.AddTool(wx.ID_ANY, 'Refresh',
                                               wx.Bitmap('icons/refresh.png'),
                                               'Refresh files and folders')

        self.tool_settings = self.toolbar.AddTool(wx.ID_PREFERENCES, 'Configuration',
                                                  wx.Bitmap('icons/config.png'),
                                                  'Open Configuration')

        self.Bind(wx.EVT_TOOL, self.queue_process, self.tool_start)
        self.Bind(wx.EVT_TOOL, self.queue_clear, self.tool_clear)
        self.Bind(wx.EVT_TOOL, self.on_button_reset_filters, self.reset_filters)
        self.Bind(wx.EVT_TOOL, self.on_refresh, self.tool_refresh)
        self.Bind(wx.EVT_TOOL, self.show_settings, self.tool_settings)

        self.toolbar.Realize()

    def create_body(self):
        logging.info("Creating Body")
        # splitter
        self.splitter = wx.SplitterWindow(self, -1)
        self.splitter.SetSashGravity(0.5)
        self.splitter.SetSashInvisible()

        # left panel for tree
        self.panel_left = wx.Panel(self.splitter, -1)

        self.textctrl_filter = wx.TextCtrl(self.panel_left, style=wx.TE_LEFT | wx.TE_PROCESS_ENTER)
        self.textctrl_filter.Bind(wx.EVT_TEXT, self.on_filter_text)
        self.textctrl_filter.Bind(wx.EVT_TEXT_ENTER, self.on_filter_text_enter)

        self.checkbox_installed = wx.CheckBox(self.panel_left, label='Installed')
        self.checkbox_installed.Disable()

        self.checkbox_not_installed = wx.CheckBox(self.panel_left, label='Not Installed')
        self.checkbox_not_installed.Disable()

        self.checkbox_zip = wx.CheckBox(self.panel_left, label='Zip')
        self.checkbox_zip.Disable()

        self.checkbox_installed.Bind(wx.EVT_CHECKBOX, self.on_checkbox_installed)
        self.checkbox_not_installed.Bind(wx.EVT_CHECKBOX, self.on_checkbox_not_installed)
        self.checkbox_zip.Bind(wx.EVT_CHECKBOX, self.on_checkbox_zip)

        self.filter_installed = False
        self.filter_not_installed = False
        self.filter_zip = False

        box_filter_textctrl = wx.BoxSizer()
        box_filter_textctrl.Add(self.textctrl_filter, 3, wx.EXPAND, border=5)
        box_filter_textctrl.Add(5, 0, 0)
        box_filter_textctrl.Add(self.checkbox_installed, 0, wx.EXPAND)
        box_filter_textctrl.Add(self.checkbox_not_installed, 0, wx.EXPAND)
        box_filter_textctrl.Add(self.checkbox_zip, 0, wx.EXPAND)

        # notebook
        self.notebook_library = wx.Notebook(self.panel_left)

        # tree tab
        self.tree_library = FolderTree(self.notebook_library, self.config.archive, 1, wx.DefaultPosition, (-1, -1),
                                       wx.TR_HAS_BUTTONS | wx.TR_MULTIPLE | wx.TR_HIDE_ROOT,
                                       self, self.filter_installed, self.filter_not_installed, self.filter_zip)

        self.ctrl_asset = wx.ListCtrl(self.notebook_library, style=wx.LC_REPORT)
        self.ctrl_asset.InsertColumn(0, "Asset", width=221)
        self.ctrl_asset.InsertColumn(1, "Zip", width=50)
        self.ctrl_asset.InsertColumn(2, "Size", width=65)
        self.ctrl_asset.InsertColumn(3, "Import Time", width=100)
        # self.ctrl_asset.InsertColumn(4, "Installed", width=60)
        self.ctrl_asset.InsertColumn(5, "Install Time", width=100)


        self.notebook_library.AddPage(self.tree_library, "Tree")
        self.notebook_library.AddPage(self.ctrl_asset, "List")
        self.notebook_library.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_notebook_change)

        left_box = wx.BoxSizer(wx.VERTICAL)
        left_box.Add(box_filter_textctrl, 0, wx.EXPAND | wx.ALL, border=5)
        left_box.Add(0, 4, 0)
        left_box.Add(self.notebook_library, 1, wx.EXPAND | wx.ALL, border=5)  # add self.tree to leftBox

        # bind on actions.txt
        self.tree_library.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_tree_sel)
        self.tree_library.Bind(wx.EVT_TREE_ITEM_MENU, self.on_tree_context)
        self.tree_library.Bind(wx.EVT_CONTEXT_MENU, self.on_empty_context)
        #

        self.ctrl_asset.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_list_sel)
        self.ctrl_asset.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.on_list_context)
        self.ctrl_asset.Bind(wx.EVT_LIST_COL_CLICK, self.on_col_click)

        self.panel_left.SetSizer(left_box)

        # right panel
        self.panel_right = wx.Panel(self.splitter, -1)

        ##################
        font_title = wx.Font(wx.FontInfo(16))
        font_data = wx.Font(wx.FontInfo(11))

        self.label_name = wx.StaticText(self.panel_right, label='')
        self.label_name.SetFont(font_title)

        self.label_filename = wx.StaticText(self.panel_right, label='')
        self.label_filename.SetFont(font_data)

        self.label_size = wx.StaticText(self.panel_right, label='')
        self.label_size.SetFont(font_data)

        self.label_path = wx.StaticText(self.panel_right, label='')
        self.label_path.SetFont(font_data)

        self.label_installed = wx.StaticText(self.panel_right, label='')
        self.label_installed.SetFont(font_data)

        self.label_zip = wx.StaticText(self.panel_right, label='')
        self.label_zip.SetFont(font_data)

        box_details = wx.BoxSizer(wx.VERTICAL)
        box_details.Add(self.label_name, proportion=0, flag=wx.EXPAND | wx.ALL, border=2)
        box_details.Add(self.label_path, proportion=0, flag=wx.EXPAND | wx.ALL, border=2)
        box_details.Add(self.label_filename, proportion=0, flag=wx.EXPAND | wx.ALL, border=2)
        box_details.Add(self.label_size, proportion=0, flag=wx.EXPAND | wx.ALL, border=2)
        box_details.Add(self.label_installed, proportion=0, flag=wx.EXPAND | wx.ALL, border=2)
        box_details.Add(self.label_zip, proportion=0, flag=wx.EXPAND | wx.ALL, border=2)

        ##################

        self.button1 = wx.Button(self.panel_right, label='Add to Queue', size=(20, 30))
        self.button1.Bind(wx.EVT_BUTTON, self.on_button1)

        self.button2 = wx.Button(self.panel_right, label='Install', size=(20, 30))
        self.button2.Bind(wx.EVT_BUTTON, self.on_button2)

        box_buttons = wx.BoxSizer()
        box_buttons.Add(self.button2, proportion=1, flag=wx.LEFT)
        box_buttons.Add(self.button1, proportion=1, flag=wx.LEFT)

        ##################
        self.right_notebook = wx.Notebook(self.panel_right)

        # zip page
        self.tree_zip = ZipTree(self.right_notebook, 1, wx.DefaultPosition, (-1, -1),
                                wx.TR_HAS_BUTTONS | wx.TR_MULTIPLE | wx.TR_HIDE_ROOT, False)
        self.right_notebook.AddPage(self.tree_zip, "Zip")

        # queue page
        self.ctrl_queue = wx.ListCtrl(self.right_notebook, style=wx.LC_REPORT)
        self.ctrl_queue.InsertColumn(0, "Asset", width=225)
        self.ctrl_queue.InsertColumn(1, "Process", width=60)
        self.ctrl_queue.InsertColumn(2, "State", width=85)
        self.ctrl_queue.InsertColumn(3, "Status", width=75)

        self.ctrl_queue.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.on_queue_context)

        self.right_notebook.AddPage(self.ctrl_queue, "Queue")
        # self.zipTree.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnLeftClick)

        ##################

        self.box_right = wx.BoxSizer(wx.VERTICAL)
        self.box_right.Add(box_details, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)
        self.box_right.Add(box_buttons, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)
        self.box_right.Add(self.right_notebook, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.BOTTOM | wx.RIGHT, border=5)

        ##################

        self.panel_right.SetSizer(self.box_right)

        # Put the left and right panes into the split window
        self.splitter.SplitVertically(self.panel_left, self.panel_right)

    def create_logger(self):
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False

        handler_console = None
        handlers = logging.getLogger().handlers
        for h in handlers:
            if isinstance(h, logging.StreamHandler):
                handler_console = h
                break

        if handler_console is None:
            handler_console = logging.StreamHandler()

        if handler_console is not None:
            # first we need to remove to avoid duplication
            logging.getLogger().removeHandler(handler_console)
            formatter = logging.Formatter('%(asctime)s / %(levelname)s / %(message)s')
            handler_console.setFormatter(formatter)
            # then add it back
            self.logger.addHandler(handler_console)

        fh = logging.FileHandler(self.config.get_config_path() / Path('log.txt'))
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        if not self.config.get_config_path().exists():
            self.config.get_config_path().mkdir(parents=True)

    def helper_menu_option(self, event, parentmenu, label, method, *args):
        """event, parentmenu, label, method, *args"""
        menuItem = parentmenu.Append(-1, label)
        wrapper = lambda event: method(*args)
        self.Bind(wx.EVT_MENU, wrapper, menuItem)

    def sound_action_complete(self, event=None):
        system = platform.system()
        # todo: failed to play sound on 7
        if system == 'Windows':
            winsound.PlaySound("DefaultBeep", winsound.SND_ALIAS)
        elif system == 'Darwin':
            pass
        else:
            pass

    def sound_queue_complete(self, event=None):
        system = platform.system()
        if system == 'Windows':
            winsound.PlaySound("DefaultBeep", winsound.SND_ALIAS)
        elif system == 'Darwin':
            pass
        else:
            pass

    def sound_error(self, event=None):
        system = platform.system()
        if system == 'Windows':
            winsound.PlaySound("SystemCritical", winsound.SND_ALIAS)
        elif system == 'Darwin':
            pass
        else:
            pass

    @staticmethod
    def excepthook(*exc_info):
        text = "".join(traceback.format_exception(*exc_info))
        logging.exception("\nUnhandled exception: %s", text)

    @staticmethod
    def get_folder_size(start_path='.'):
        size = 0
        rnd = 2 * 10
        for dirpath, dirnames, filenames in os.walk(start_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                # skip if it is symbolic link
                if not os.path.islink(fp):
                    size += os.path.getsize(fp)

        if size > 2 ** 30:
            size /= 2 ** 30
            ext = 'GB'
        else:
            size /= 2 ** 20
            ext = 'MB'

        return str(int(size * rnd) / rnd) + ' ' + ext