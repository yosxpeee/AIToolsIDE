"""wxPython GUI for AIToolsIDE: left menu + WebView + settings dialog."""
import wx
import wx.html2
from . import config


class SettingsPanel(wx.Panel):
    def __init__(self, parent, cfg, on_save=None, on_cancel=None):
        super().__init__(parent)
        self.on_save = on_save
        self.on_cancel = on_cancel
        s = wx.BoxSizer(wx.VERTICAL)

        grid = wx.FlexGridSizer(rows=2, cols=2, vgap=8, hgap=8)
        grid.AddGrowableCol(1, 1)

        grid.Add(wx.StaticText(self, label="Stable Diffusion URL:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.sd_ctrl = wx.TextCtrl(self, value=cfg.get("stable_diffusion", ""))
        grid.Add(self.sd_ctrl, 1, wx.EXPAND)

        grid.Add(wx.StaticText(self, label="IOPaint URL:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.io_ctrl = wx.TextCtrl(self, value=cfg.get("iopaint", ""))
        grid.Add(self.io_ctrl, 1, wx.EXPAND)

        s.Add(grid, 0, wx.ALL | wx.EXPAND, 8)
        # push buttons to the bottom of the panel
        s.AddStretchSpacer()

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_save = wx.Button(self, label="保存")
        btn_cancel = wx.Button(self, label="キャンセル")
        btn_sizer.AddStretchSpacer()
        btn_sizer.Add(btn_save, 0, wx.RIGHT, 6)
        btn_sizer.Add(btn_cancel, 0)

        s.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 8)

        self.SetSizer(s)

        btn_save.Bind(wx.EVT_BUTTON, self.on_save_clicked)
        btn_cancel.Bind(wx.EVT_BUTTON, self.on_cancel_clicked)

    def on_save_clicked(self, event):
        sd = self.sd_ctrl.GetValue().strip() or config.DEFAULT["stable_diffusion"]
        io = self.io_ctrl.GetValue().strip() or config.DEFAULT["iopaint"]
        newcfg = {"stable_diffusion": sd, "iopaint": io}
        config.save(newcfg)
        if callable(self.on_save):
            self.on_save(newcfg)

    def on_cancel_clicked(self, event):
        # call cancel callback if provided (MainFrame will restore view),
        # otherwise hide as a fallback
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

        # Create separate panels for each tool's WebView so we can toggle via Enable/Disable
        self.sd_panel = wx.Panel(right)
        sd_s = wx.BoxSizer(wx.VERTICAL)
        self.web_sd = wx.html2.WebView.New(self.sd_panel)
        sd_s.Add(self.web_sd, 1, wx.EXPAND)
        self.sd_panel.SetSizer(sd_s)

        self.io_panel = wx.Panel(right)
        io_s = wx.BoxSizer(wx.VERTICAL)
        self.web_io = wx.html2.WebView.New(self.io_panel)
        io_s.Add(self.web_io, 1, wx.EXPAND)
        self.io_panel.SetSizer(io_s)

        right_sizer.Add(self.sd_panel, 1, wx.EXPAND)
        right_sizer.Add(self.io_panel, 1, wx.EXPAND)
        right.SetSizer(right_sizer)

        # track whether we've loaded each webview once
        self.sd_loaded = False
        self.io_loaded = False

        self.splitter.SplitVertically(left, right, sashPosition=220)

        left_sizer = wx.BoxSizer(wx.VERTICAL)
        btn_sd = wx.Button(left, label="Stable Diffusion WebUI")
        btn_io = wx.Button(left, label="IOPaint")
        # ensure left column has a reasonable width so buttons are visible
        left.SetMinSize((220, -1))
        btn_sd.SetMinSize((200, 36))
        btn_io.SetMinSize((200, 36))
        left_sizer.Add(btn_sd, 0, wx.EXPAND | wx.ALL, 6)
        left_sizer.Add(btn_io, 0, wx.EXPAND | wx.ALL, 6)
        left_sizer.AddStretchSpacer()
        btn_settings = wx.Button(left, label="設定")
        left_sizer.Add(btn_settings, 0, wx.EXPAND | wx.ALL, 6)
        left.SetSizer(left_sizer)

        btn_sd.Bind(wx.EVT_BUTTON, lambda e: self.show_tool("stable_diffusion"))
        btn_io.Bind(wx.EVT_BUTTON, lambda e: self.show_tool("iopaint"))
        btn_settings.Bind(wx.EVT_BUTTON, self.on_settings)
        # show SD by default after layout is set
        self.show_tool("stable_diffusion")

    def load_url(self, url: str):
        if not url:
            return
        if not url.startswith("http"):
            url = "http://" + url
        try:
            # default to stable diffusion webview
            try:
                self.web_sd.LoadURL(url)
                self.sd_loaded = True
            except Exception:
                # fallback: try io
                self.web_io.LoadURL(url)
                self.io_loaded = True
        except Exception:
            wx.MessageBox(f"URLを開けません: {url}", "エラー", wx.OK | wx.ICON_ERROR)

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
        # Show appropriate panel and enable/disable without reloading if already opened
        if tool_name == "stable_diffusion":
            url = self.cfg.get("stable_diffusion")
            if url and not self.sd_loaded:
                try:
                    if not url.startswith("http"):
                        url = "http://" + url
                    self.web_sd.LoadURL(url)
                    self.sd_loaded = True
                except Exception:
                    wx.MessageBox(f"URLを開けません: {url}", "エラー", wx.OK | wx.ICON_ERROR)
            # enable SD panel, disable IO panel
            self.sd_panel.Show()
            self.sd_panel.Enable(True)
            self.io_panel.Hide()
            self.io_panel.Enable(False)
        elif tool_name == "iopaint":
            url = self.cfg.get("iopaint")
            if url and not self.io_loaded:
                try:
                    if not url.startswith("http"):
                        url = "http://" + url
                    self.web_io.LoadURL(url)
                    self.io_loaded = True
                except Exception:
                    wx.MessageBox(f"URLを開けません: {url}", "エラー", wx.OK | wx.ICON_ERROR)
            # enable IO panel, disable SD panel
            self.io_panel.Show()
            self.io_panel.Enable(True)
            self.sd_panel.Hide()
            self.sd_panel.Enable(False)
        # refresh layout
        try:
            parent = self.sd_panel.GetParent()
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
            # update controls with current cfg values then show
            self.settings_panel.sd_ctrl.SetValue(self.cfg.get("stable_diffusion", ""))
            self.settings_panel.io_ctrl.SetValue(self.cfg.get("iopaint", ""))
            # hide webviews while settings is visible
            try:
                self.sd_panel.Hide()
                self.sd_panel.Enable(False)
            except Exception:
                pass
            try:
                self.io_panel.Hide()
                self.io_panel.Enable(False)
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
        # show stable diffusion panel after save (loads if not loaded yet)
        self.show_tool("stable_diffusion")
        # hide settings after save and refresh layout
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


def main():
    cfg = config.load()
    app = wx.App(False)
    frame = MainFrame(cfg)
    frame.Show()
    app.MainLoop()
