"""SettingsPanel class moved out from app.py for better modularity."""
import wx
from . import config

class SettingsPanel(wx.Panel):
    def __init__(self, parent, cfg, on_save=None, on_cancel=None):
        super().__init__(parent)
        self.on_save = on_save
        self.on_cancel = on_cancel
        self.cfg = cfg.copy()
        s = wx.BoxSizer(wx.VERTICAL)
        # header label
        try:
            header = wx.StaticText(self, label="設定")
            f = header.GetFont()
            try:
                f.SetPointSize(f.GetPointSize() + 2)
            except Exception:
                pass
            try:
                f.SetWeight(wx.FONTWEIGHT_BOLD)
            except Exception:
                pass
            header.SetFont(f)
            s.Add(header, 0, wx.ALL | wx.ALIGN_LEFT, 8)
        except Exception:
            pass
        self.mode_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.mode_radio_title = wx.StaticText(self, label="テーマ: ")
        self.mode_radio_light = wx.RadioButton(self, wx.ID_ANY, 'ライト', style=wx.RB_GROUP)
        self.mode_radio_dark = wx.RadioButton(self, wx.ID_ANY, 'ダーク')
        if self.cfg["webview_theme"] == "dark":
            self.mode_radio_dark.SetValue(True)
        else:
            self.mode_radio_light.SetValue(True)
        self.mode_sizer.Add(self.mode_radio_title)
        self.mode_sizer.Add(self.mode_radio_light, flag=wx.GROW)
        self.mode_sizer.Add(self.mode_radio_dark, flag=wx.GROW)
        s.Add(self.mode_sizer, 0, wx.LEFT, 8)
        # area to list editable tool rows
        self.list_panel = wx.Panel(self)
        self.list_sizer = wx.BoxSizer(wx.VERTICAL)
        self.list_panel.SetSizer(self.list_sizer)
        s.Add(self.list_panel, 1, wx.ALL | wx.EXPAND, 8)
        # add controls: only "追加" stays inside the settings content
        ctl_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_add = wx.Button(self, label="追加")
        ctl_sizer.Add(btn_add, 0, wx.RIGHT, 6)
        ctl_sizer.AddStretchSpacer()
        s.Add(ctl_sizer, 0, wx.EXPAND | wx.ALL, 8)
        self.SetSizer(s)
        btn_add.Bind(wx.EVT_BUTTON, self._on_add_row)
        self.rows = []  # list of (key_ctrl, name_ctrl, url_ctrl, remove_btn, container)
        self.build_rows(self.cfg["menu_items"])

    def build_rows(self, cfg: dict):
        # clear existing
        for _, _, _, _, cont in list(self.rows):
            cont.Destroy()
        self.rows.clear()
        for key, entry in cfg.items():
            # expect entry to be dict {name, url}
            keyword = key
            name = entry.get("name", key)
            url = entry.get("url", "")
            self._create_row(keyword, name, url)

    def _create_row(self, keyword: str = "", name: str = "", url: str = ""):
        cont = wx.Panel(self.list_panel)
        hs = wx.BoxSizer(wx.HORIZONTAL)
        key_ctrl = wx.TextCtrl(cont, value=keyword)
        name_ctrl = wx.TextCtrl(cont, value=name)
        url_ctrl = wx.TextCtrl(cont, value=url)
        btn_rm = wx.Button(cont, label="削除")
        hs.Add(wx.StaticText(cont, label="キー:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        hs.Add(key_ctrl, 0, wx.EXPAND | wx.RIGHT, 6)
        hs.Add(wx.StaticText(cont, label="名前:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        hs.Add(name_ctrl, 0, wx.EXPAND | wx.RIGHT, 6)
        hs.Add(wx.StaticText(cont, label="URL:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        hs.Add(url_ctrl, 1, wx.EXPAND | wx.RIGHT, 6)
        hs.Add(btn_rm, 0)
        cont.SetSizer(hs)
        self.list_sizer.Add(cont, 0, wx.EXPAND | wx.BOTTOM, 6)
        def on_remove(evt):
            cont.Destroy()
            # remove from rows list
            self.rows[:] = [r for r in self.rows if r[3] is not cont]
            self.Layout()
        btn_rm.Bind(wx.EVT_BUTTON, on_remove)
        self.rows.append((key_ctrl, name_ctrl, url_ctrl, btn_rm, cont))

    def _on_add_row(self, event):
        self._create_row("", "")
        self.Layout()

    def on_save_clicked(self, event):
        newcfg = {}
        if self.mode_radio_light.GetValue() == True:
            newcfg["webview_theme"] = "light"
        else:
            newcfg["webview_theme"] = "dark"
        newcfg["menu_items"] = {}
        for key_ctrl, name_ctrl, url_ctrl, _, _, in self.rows:
            key = key_ctrl.GetValue().strip()
            name = name_ctrl.GetValue().strip()
            url = url_ctrl.GetValue().strip()
            if not key:
                continue
            if not name:
                continue
            if not url:
                continue
            newcfg["menu_items"][key] = {"name": name, "url": url}
        if not newcfg:
            wx.MessageBox("ツールが一つも設定されていません。", "エラー", wx.OK | wx.ICON_ERROR)
            return
        try:
            config.save(newcfg)
        except Exception:
            wx.MessageBox("設定の保存に失敗しました。", "エラー", wx.OK | wx.ICON_ERROR)
            return
        if callable(self.on_save):
            self.on_save(newcfg)

    # note: save/cancel buttons are managed by MainFrame's bottom bar
    def trigger_cancel(self):
        if callable(self.on_cancel):
            self.on_cancel()
        else:
            self.Hide()
