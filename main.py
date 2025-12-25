import wx

# アプリケーションを作る
app = wx.App()
# Frameの作成
frame = wx.Frame(
    parent=None,
    id=-1,
    title='wxpython',
    size=(640, 480)
)
frame.Show()
app.SetTopWindow(frame)
app.MainLoop()