import wx

########################################
# AI Tools IDE
#
# Programming assisted by GPT-5 mini
########################################
from src import config
from src import main_frame

def main():
    cfg = config.load()
    app = wx.App(False)
    frame = main_frame.MainFrame(cfg)
    frame.Show()
    app.MainLoop()

if __name__ == '__main__':
    main()
