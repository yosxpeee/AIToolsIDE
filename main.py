import wx

# アプリケーションを作る
app = wx.App()
# Frameの作成
frame = wx.Frame(
    parent=None,
    id=-1,
    title='AI Tools IDE v0.1',
    size=(400, 400)
)
frame.Show()
app.SetTopWindow(frame)
app.MainLoop()