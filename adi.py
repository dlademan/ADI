from MainFrame import MainFrame
import wx, wx.adv


class ADI(wx.App):
    """ADI application class"""

    def OnInit(self):
        frame = MainFrame(None, -1, "Alternative Daz Importer")

        return True


if __name__ == '__main__':
    app = ADI(False)
    app.MainLoop()