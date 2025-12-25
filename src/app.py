"""wxPython GUI for AIToolsIDE: left menu + WebView + settings dialog."""
import wx
import wx.html2
from . import config
from .settings_panel import SettingsPanel

APP_VERSION = "v0.1"

class MainFrame(wx.Frame):
    def __init__(self, cfg):
        super().__init__(None, title=f"AI Tools IDE {APP_VERSION}", size=(1440, 900))
        self.cfg = cfg
        self.current_tool = None

        self.splitter = wx.SplitterWindow(self)
        left = wx.Panel(self.splitter)
        right = wx.Panel(self.splitter)

        # Right side will contain settings panel (top) and webview (fill)
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        # wrap settings in a bordered container so it has a visible border
        settings_container = wx.Panel(right, style=wx.BORDER_SIMPLE)
        settings_sizer = wx.BoxSizer(wx.VERTICAL)
        self.settings_panel = SettingsPanel(settings_container, cfg, on_save=self._on_settings_saved, on_cancel=self._on_settings_cancelled)
        self.settings_panel.Hide()
        settings_sizer.Add(self.settings_panel, 1, wx.EXPAND)
        settings_container.SetSizer(settings_sizer)
        self.settings_container = settings_container
        # let settings occupy the full right area when shown
        right_sizer.Add(settings_container, 1, wx.EXPAND | wx.ALL, 6)

        # dynamic tool panels will be created from cfg
        self.tool_panels = {}
        self.tool_webviews = {}
        self.tool_url_ctrls = {}
        self.tool_loaded = {}

        # store right references so helper methods can modify layout
        self.right = right
        self.right_sizer = right_sizer
        # bottom buttons for settings (Save / Cancel) — outside the settings panel
        self.settings_button_panel = wx.Panel(right)
        btn_bar = wx.BoxSizer(wx.HORIZONTAL)
        btn_bar.AddStretchSpacer()
        self.btn_save = wx.Button(self.settings_button_panel, label="保存")
        self.btn_cancel = wx.Button(self.settings_button_panel, label="キャンセル")
        btn_bar.Add(self.btn_save, 0, wx.RIGHT, 6)
        btn_bar.Add(self.btn_cancel, 0)
        self.settings_button_panel.SetSizer(btn_bar)
        # add to right_sizer (fixed at bottom)
        right_sizer.Add(self.settings_button_panel, 0, wx.EXPAND | wx.ALL, 8)
        # placeholder: create panels for each configured tool
        self._build_tool_panels(self.cfg)
        right.SetSizer(right_sizer)
        # initially hide settings UI and its button panel so webviews occupy space
        try:
            self.right_sizer.Hide(self.settings_container)
            self.right_sizer.Hide(self.settings_button_panel)
        except Exception:
            pass

        self.splitter.SplitVertically(left, right, sashPosition=220)

        # build left side: tools list in a content panel, with a vertical separator at its right
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        # area to contain tool buttons (rebuildable)
        self.tools_sizer = wx.BoxSizer(wx.VERTICAL)
        left_sizer.Add(self.tools_sizer, 0, wx.EXPAND | wx.ALL, 6)
        left_sizer.AddStretchSpacer()

        # put left_sizer into a content panel so we can add a vertical StaticLine beside it
        left_content = wx.Panel(left)
        # create settings button as child of left_content so sizer parents match
        btn_settings = wx.Button(left_content, label="設定")
        left_sizer.Add(btn_settings, 0, wx.EXPAND | wx.ALL, 6)
        left_content.SetSizer(left_sizer)
        # keep reference so other methods can rebuild the left menu
        self.left_content = left_content
        outer_left = wx.BoxSizer(wx.HORIZONTAL)
        outer_left.Add(left_content, 1, wx.EXPAND)
        sep = wx.StaticLine(left, style=wx.LI_VERTICAL)
        outer_left.Add(sep, 0, wx.EXPAND)
        left.SetSizer(outer_left)

        btn_settings.Bind(wx.EVT_BUTTON, self.on_settings)
        # build left menu buttons from cfg
        self._build_left_menu(left_content)
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
        for key, entry in cfg.items():
            # expect entry to be dict {name,url}
            url = entry.get("url", "")
            panel = wx.Panel(self.right)
            s = wx.BoxSizer(wx.VERTICAL)

            # top bar: refresh button + url field
            top_bar = wx.Panel(panel)
            top_s = wx.BoxSizer(wx.HORIZONTAL)
            btn_refresh = wx.Button(top_bar, label="⟳", size=(24,24))
            # URL display is readonly; users can copy but not edit here
            url_ctrl = wx.TextCtrl(top_bar, value=url, style=wx.TE_READONLY)
            top_s.Add(btn_refresh, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
            top_s.Add(url_ctrl, 1, wx.EXPAND)
            top_bar.SetSizer(top_s)

            web = wx.html2.WebView.New(panel)
            s.Add(top_bar, 0, wx.EXPAND | wx.ALL, 6)
            s.Add(web, 1, wx.EXPAND)
            panel.SetSizer(s)
            panel.Hide()
            self.right_sizer.Add(panel, 1, wx.EXPAND)
            self.tool_panels[key] = panel
            self.tool_webviews[key] = web
            self.tool_url_ctrls[key] = url_ctrl
            self.tool_loaded[key] = False

            # bind refresh button to reload the shown URL (TextCtrl is readonly)
            btn_refresh.Bind(wx.EVT_BUTTON, lambda e, k=key: self._load_url_into_tool(k, self.tool_url_ctrls[k].GetValue()))

    def _show_settings_ui(self):
        # show settings container and hide tool panels so settings takes full area
        try:
            for panel in self.tool_panels.values():
                try:
                    panel.Hide()
                except Exception:
                    pass
            self.settings_container.Show()
            # ensure settings panel itself is visible and laid out
            try:
                self.settings_panel.Show()
                self.settings_panel.Layout()
            except Exception:
                pass
            self.settings_button_panel.Show()
            self.right.Layout()
            self.splitter.Layout()
        except Exception:
            pass

    def _show_tool_ui(self):
        # show only the currently selected tool panel and hide settings container/button panel
        try:
            try:
                self.settings_panel.Hide()
            except Exception:
                pass
            try:
                self.settings_container.Hide()
            except Exception:
                pass
            try:
                self.settings_button_panel.Hide()
            except Exception:
                pass

            # hide all panels first
            for key, panel in self.tool_panels.items():
                try:
                    panel.Hide()
                except Exception:
                    pass

            # choose panel to show
            target = self.current_tool or next(iter(self.cfg.keys()), None)
            if target and target in self.tool_panels:
                try:
                    self.tool_panels[target].Show()
                except Exception:
                    pass

            self.right.Layout()
            self.splitter.Layout()
        except Exception:
            pass

    def _load_url_into_tool(self, key: str, url: str):
        if not url:
            return
        if not url.startswith("http"):
            url = "http://" + url
        try:
            w = self.tool_webviews.get(key)
            if w is not None:
                w.LoadURL(url)
                self.tool_loaded[key] = True
        except Exception:
            wx.MessageBox(f"URLを開けません: {url}", "エラー", wx.OK | wx.ICON_ERROR)

    def _build_left_menu(self, left_panel):
        # clear existing children in tools_sizer
        for child in list(self.tools_sizer.GetChildren()):
            widget = child.GetWindow()
            if widget:
                widget.Destroy()
        # create buttons for each tool
        for key, entry in self.cfg.items():
            # display name from entry['name']
            label = entry.get("name", key)
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
                # close settings first, but continue to switch to the requested tool
                self._on_settings_cancelled()
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
        entry = self.cfg.get(tool_name)
        # expect dict
        url = entry.get("url")
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
            # hide settings and restore tool UI
            self.settings_panel.Hide()
            self._show_tool_ui()
            if self.current_tool:
                self.show_tool(self.current_tool)
        else:
            # update settings panel with current cfg and show it
            self.settings_panel.build_rows(self.cfg)
            # hide all webviews while settings is visible
            self._show_settings_ui()
            # bind bottom buttons to settings actions
            self.btn_save.Bind(wx.EVT_BUTTON, lambda e: self.settings_panel.on_save_clicked(e))
            self.btn_cancel.Bind(wx.EVT_BUTTON, lambda e: self.settings_panel.trigger_cancel())
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
        # rebuild left menu using the saved left content panel
        try:
            self._build_left_menu(self.left_content)
        except Exception:
            # fallback to splitter left window if left_content missing
            self._build_left_menu(self.splitter.GetWindow1())
        # hide settings and restore tool UI
        try:
            self.settings_panel.Hide()
        except Exception:
            pass
        try:
            self._show_tool_ui()
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
        except Exception:
            pass
        try:
            self._show_tool_ui()
        except Exception:
            pass
        # do NOT automatically call show_tool here; caller (e.g. show_tool)
        # will proceed to switch to the requested tool. If no caller
        # chooses a tool, restore previous/current selection below.
        if not self.current_tool:
            first = next(iter(self.cfg.keys()), None)
            if first:
                self.current_tool = first


def main():
    cfg = config.load()
    app = wx.App(False)
    frame = MainFrame(cfg)
    frame.Show()
    app.MainLoop()
