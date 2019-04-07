from MainFrame import MainFrame
import wx


class ADI(wx.App):
    """ADI application class"""

    def OnInit(self):
        frame = MainFrame(None, -1, "Alternative Daz Importer")
        frame.Show(True)
        self.SetTopWindow(frame)
        return True


if __name__ == '__main__':
    app = ADI(0)
    app.MainLoop()