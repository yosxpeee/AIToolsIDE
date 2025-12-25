import wx

SYS_COLOR_LIST = [
    "SCROLLBAR",
    "DESKTOP",
    "ACTIVECAPTION",
    "INACTIVECAPTION",
    "MENU",
    "WINDOW",
    "WINDOWFRAME",
    "MENUTEXT",
    "WINDOWTEXT",
    "CAPTIONTEXT",
    "ACTIVEBORDER",
    "INACTIVEBORDER",
    "APPWORKSPACE",
    "HIGHLIGHT",
    "HIGHLIGHTTEXT",
    "BTNFACE",
    "BTNSHADOW",
    "GRAYTEXT",
    "BTNTEXT",
    "INACTIVECAPTIONTEXT",
    "BTNHIGHLIGHT",
    "3DDKSHADOW",
    "3DLIGHT",
    "INFOTEXT",
    "INFOBK",
    "LISTBOX",
    "HOTLIGHT",
    "GRADIENTACTIVECAPTION",
    "GRADIENTINACTIVECAPTION",
    "MENUHILIGHT",
    "MENUBAR",
    "LISTBOXTEXT",
    "LISTBOXHIGHLIGHTTEXT",
    "BACKGROUND",
    "3DFACE",
    "3DSHADOW",
    "BTNHILIGHT",
    "3DHIGHLIGHT",
    "3DHILIGHT",
    "FRAMEBK"
]


class MyApp(wx.Frame):
    def __init__(self, *args, **kw):
        super(MyApp, self).__init__(*args, **kw)

        self.InitUI()

    def InitUI(self):

        panel = wx.Panel(self)
        box = wx.BoxSizer(wx.HORIZONTAL)

        color_list = wx.ListCtrl(panel, wx.ID_ANY, style=wx.LC_REPORT)

        color_list.InsertColumn(0, "Index", width=50)
        color_list.InsertColumn(1, "Name", width=250)
        color_list.InsertColumn(2, "Color (R,G,B,alpha)", width=200)

        for i, item in enumerate(SYS_COLOR_LIST):
            color_list.InsertItem(i, str(i))
            color_list.SetItem(i, 1, item)
            try:
                color = wx.SystemSettings.GetColour(i)
                color_list.SetItem(i, 2, str(color))
                color_list.SetItemBackgroundColour(i, wx.Colour(color))
                if sum(color[:3]) < 500 and color[3] > 50:
                    color_list.SetItemTextColour(i, wx.Colour("white"))
                elif color[3] > 50:
                    color_list.SetItemTextColour(i, wx.Colour("black"))

            except AssertionError:
                color_list.SetItem(i, 2, "None")

        box.Add(color_list, 1, wx.EXPAND)
        panel.SetSizer(box)

        self.SetSize((500, 500))
        self.SetTitle('List of wx.SystemColour')


def main():
    app = wx.App()
    gui = MyApp(None)
    gui.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()