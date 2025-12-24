"""wxPython GUI for AIToolsIDE: left menu + WebView + settings dialog."""
import wx
import wx.html2
from . import config


class SettingsPanel(wx.Panel):
    def __init__(self, parent, cfg, on_save=None, on_cancel=None):
        super().__init__(parent)
        self.on_save = on_save
        self.on_cancel = on_cancel
        self.cfg = cfg.copy()

        s = wx.BoxSizer(wx.VERTICAL)

        # area to list editable tool rows
        self.list_panel = wx.Panel(self)
        self.list_sizer = wx.BoxSizer(wx.VERTICAL)
        self.list_panel.SetSizer(self.list_sizer)

        s.Add(self.list_panel, 1, wx.ALL | wx.EXPAND, 8)

        # add / save / cancel controls at bottom
        ctl_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_add = wx.Button(self, label="追加")
        ctl_sizer.Add(btn_add, 0, wx.RIGHT, 6)
        ctl_sizer.AddStretchSpacer()
        btn_save = wx.Button(self, label="保存")
        btn_cancel = wx.Button(self, label="キャンセル")
        ctl_sizer.Add(btn_save, 0, wx.RIGHT, 6)
        ctl_sizer.Add(btn_cancel, 0)

        s.Add(ctl_sizer, 0, wx.EXPAND | wx.ALL, 8)

        self.SetSizer(s)

        btn_add.Bind(wx.EVT_BUTTON, self._on_add_row)
        btn_save.Bind(wx.EVT_BUTTON, self.on_save_clicked)
        btn_cancel.Bind(wx.EVT_BUTTON, self.on_cancel_clicked)

        self.rows = []  # list of (name_ctrl, url_ctrl, remove_btn, container)
        self.build_rows(self.cfg)

    def build_rows(self, cfg: dict):
        # clear existing
        for _, _, _, cont in list(self.rows):
            cont.Destroy()
        self.rows.clear()

        for name, url in cfg.items():
            self._create_row(name, url)

    def _create_row(self, name: str = "", url: str = ""):
        cont = wx.Panel(self.list_panel)
        hs = wx.BoxSizer(wx.HORIZONTAL)
        name_ctrl = wx.TextCtrl(cont, value=name)
        url_ctrl = wx.TextCtrl(cont, value=url)
        btn_rm = wx.Button(cont, label="削除")
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
        self.rows.append((name_ctrl, url_ctrl, btn_rm, cont))

    def _on_add_row(self, event):
        self._create_row("", "")
        self.Layout()

    def on_save_clicked(self, event):
        newcfg = {}
        for name_ctrl, url_ctrl, _, _ in self.rows:
            name = name_ctrl.GetValue().strip()
            url = url_ctrl.GetValue().strip()
            if not name:
                continue
            key = name.lower().replace(" ", "_")
            newcfg[key] = url
        if not newcfg:
            wx.MessageBox("ツールが一つも設定されていません。", "エラー", wx.OK | wx.ICON_ERROR)
            return
        config.save(newcfg)
        if callable(self.on_save):
            self.on_save(newcfg)

    def on_cancel_clicked(self, event):
        if callable(self.on_cancel):
            self.on_cancel()
        else:
            self.Hide()


class MainFrame(wx.Frame):
    def __init__(self, cfg):
        super().__init__(None, title="AIToolsIDE", size=(1200, 800))
        self.cfg = cfg
        self.current_tool = None

        self.splitter = wx.SplitterWindow(self)
        left = wx.Panel(self.splitter)
        right = wx.Panel(self.splitter)

        # Right side will contain settings panel (top) and webview (fill)
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        self.settings_panel = SettingsPanel(right, cfg, on_save=self._on_settings_saved, on_cancel=self._on_settings_cancelled)
        self.settings_panel.Hide()
        # let settings occupy the full right area when shown
        right_sizer.Add(self.settings_panel, 1, wx.EXPAND)

        # dynamic tool panels will be created from cfg
        self.tool_panels = {}
        self.tool_webviews = {}
        self.tool_loaded = {}

        # store right references so helper methods can modify layout
        self.right = right
        self.right_sizer = right_sizer
        # placeholder: create panels for each configured tool
        self._build_tool_panels(self.cfg)
        right.SetSizer(right_sizer)

        self.splitter.SplitVertically(left, right, sashPosition=220)

        left_sizer = wx.BoxSizer(wx.VERTICAL)
        # area to contain tool buttons (rebuildable)
        self.tools_sizer = wx.BoxSizer(wx.VERTICAL)
        left_sizer.Add(self.tools_sizer, 0, wx.EXPAND | wx.ALL, 6)
        left_sizer.AddStretchSpacer()
        btn_settings = wx.Button(left, label="設定")
        left_sizer.Add(btn_settings, 0, wx.EXPAND | wx.ALL, 6)
        left.SetSizer(left_sizer)

        btn_settings.Bind(wx.EVT_BUTTON, self.on_settings)
        # build left menu buttons from cfg
        self._build_left_menu(left)
        # show first tool by default
        first = next(iter(self.cfg.keys()), None)
        if first:
            self.show_tool(first)

        left.SetMinSize((220, -1))

    def load_url(self, url: str):
        if not url:
            return
        if not url.startswith("http"):
            url = "http://" + url
        try:
            # default to stable diffusion webview
            # load into the first available webview (legacy helper)
            for w in self.tool_webviews.values():
                try:
                    w.LoadURL(url)
                    break
                except Exception:
                    continue
        except Exception:
            wx.MessageBox(f"URLを開けません: {url}", "エラー", wx.OK | wx.ICON_ERROR)

    # --- dynamic tool panel helpers ---
    def _clear_tool_panels(self):
        for p in list(self.tool_panels.values()):
            try:
                p.Destroy()
            except Exception:
                pass
        self.tool_panels.clear()
        self.tool_webviews.clear()
        self.tool_loaded.clear()

    def _build_tool_panels(self, cfg: dict):
        # clear any existing
        self._clear_tool_panels()
        # create a panel+webview per configured tool and add to right_sizer
        for key, url in cfg.items():
            panel = wx.Panel(self.right)
            s = wx.BoxSizer(wx.VERTICAL)
            web = wx.html2.WebView.New(panel)
            s.Add(web, 1, wx.EXPAND)
            panel.SetSizer(s)
            panel.Hide()
            self.right_sizer.Add(panel, 1, wx.EXPAND)
            self.tool_panels[key] = panel
            self.tool_webviews[key] = web
            self.tool_loaded[key] = False

    def _build_left_menu(self, left_panel):
        # clear existing children in tools_sizer
        for child in list(self.tools_sizer.GetChildren()):
            widget = child.GetWindow()
            if widget:
                widget.Destroy()
        # create buttons for each tool
        for key in self.cfg.keys():
            label = key.replace('_', ' ').title()
            btn = wx.Button(left_panel, label=label)
            btn.SetMinSize((200, 36))
            self.tools_sizer.Add(btn, 0, wx.EXPAND | wx.ALL, 6)
            btn.Bind(wx.EVT_BUTTON, lambda e, k=key: self.show_tool(k))
        # refresh
        left_panel.Layout()

    def show_tool(self, tool_name: str):
        # If settings panel is open, treat any tool switch as a cancel:
        # close settings and restore the previously selected tool.
        try:
            if self.settings_panel.IsShown():
                self._on_settings_cancelled()
                return
        except Exception:
            pass

        # remember current tool so we can restore after closing settings
        self.current_tool = tool_name
        # hide all tool panels
        for name, panel in self.tool_panels.items():
            try:
                panel.Hide()
                panel.Enable(False)
            except Exception:
                pass

        # ensure requested tool exists
        panel = self.tool_panels.get(tool_name)
        if panel is None:
            wx.MessageBox(f"ツールが見つかりません: {tool_name}", "エラー", wx.OK | wx.ICON_ERROR)
            return

        # load URL if not yet loaded
        url = self.cfg.get(tool_name)
        loaded = self.tool_loaded.get(tool_name, False)
        if url and not loaded:
            try:
                if not url.startswith("http"):
                    url = "http://" + url
                w = self.tool_webviews.get(tool_name)
                if w is not None:
                    w.LoadURL(url)
                self.tool_loaded[tool_name] = True
            except Exception:
                wx.MessageBox(f"URLを開けません: {url}", "エラー", wx.OK | wx.ICON_ERROR)

        # show selected panel
        try:
            panel.Show()
            panel.Enable(True)
        except Exception:
            pass

        # refresh layout
        try:
            parent = panel.GetParent()
            if parent is not None:
                parent.Layout()
        except Exception:
            pass
        try:
            self.splitter.Layout()
        except Exception:
            pass
        self.Layout()

    def on_settings(self, event):
        # toggle visibility of in-frame settings panel
        if self.settings_panel.IsShown():
            # hide settings and restore previously selected tool
            self.settings_panel.Hide()
            if self.current_tool:
                self.show_tool(self.current_tool)
        else:
            # update settings panel with current cfg and show it
            self.settings_panel.build_rows(self.cfg)
            # hide all webviews while settings is visible
            for panel in self.tool_panels.values():
                try:
                    panel.Hide()
                    panel.Enable(False)
                except Exception:
                    pass
            self.settings_panel.Show()
        # refresh layout on parent containers
        try:
            parent = self.settings_panel.GetParent()
            if parent is not None:
                parent.Layout()
        except Exception:
            pass
        try:
            self.splitter.Layout()
        except Exception:
            pass
        self.Layout()

    def _on_settings_saved(self, newcfg):
        # called by SettingsPanel when user saves
        self.cfg = newcfg
        # rebuild tool UI from new config
        self._build_tool_panels(self.cfg)
        self._build_left_menu(self.splitter.GetWindow1())
        # hide settings and show first tool
        try:
            self.settings_panel.Hide()
            parent = self.settings_panel.GetParent()
            if parent is not None:
                parent.Layout()
        except Exception:
            pass
        try:
            self.splitter.Layout()
        except Exception:
            pass
        # prefer stable_diffusion if present, else first
        preferred = "stable_diffusion" if "stable_diffusion" in self.cfg else next(iter(self.cfg.keys()), None)
        if preferred:
            self.show_tool(preferred)
        self.Layout()

    def _on_settings_cancelled(self):
        # hide settings and restore previously selected tool
        try:
            self.settings_panel.Hide()
            parent = self.settings_panel.GetParent()
            if parent is not None:
                parent.Layout()
        except Exception:
            pass
        try:
            self.splitter.Layout()
        except Exception:
            pass
        if self.current_tool:
            self.show_tool(self.current_tool)
        else:
            first = next(iter(self.cfg.keys()), None)
            if first:
                self.show_tool(first)


def main():
    cfg = config.load()
    app = wx.App(False)
    frame = MainFrame(cfg)
    frame.Show()
    app.MainLoop()
