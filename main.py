# main.py
import os
import sys

# 【核心提权】：禁用 WebRTC、禁用自动化特征、开启硬件加速
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    "--disable-web-security "
    "--disable-site-isolation-trials "
    "--no-sandbox "
    "--disable-blink-features=AutomationControlled "
    "--disable-webrtc "
    "--ignore-gpu-blocklist "
    "--enable-gpu-rasterization "
    "--num-raster-threads=4"
)

import time
import json
import random
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QStackedWidget, QTextEdit, QSplitter,
                             QListWidgetItem, QLabel, QMessageBox)
from PyQt6.QtCore import Qt, QUrl, QTimer, QSettings, QSize
from PyQt6.QtGui import QFont

from styles import STYLE_SHEET
from browser import BrowserInstance
from ui_components import LeftSidebar, TopBar

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HeyGen 群控 v5.3 (Layout-Pro)")
        self.setStyleSheet(STYLE_SHEET)

        # 路径识别
        if sys.platform == "win32":
            self.base_path = os.path.join(os.environ.get("APPDATA"), "HeyGenControl")
        else:
            self.base_path = os.path.join(os.path.expanduser("~"), ".config", "HeyGenControl")
        os.makedirs(self.base_path, exist_ok=True)
        self.config_file = os.path.join(self.base_path, "accounts.txt")
        self.storage_root = os.path.join(self.base_path, "browser_data")
        os.makedirs(self.storage_root, exist_ok=True)

        self.settings = QSettings("MyCompany", "HeyGenControl")
        self.canva_cookies_vault = []
        self.last_sync_time = 0
        self.all_accounts = self.load_accounts_config()
        self.instances = {}

        # --- UI 构建 ---
        # 1. 左右主分割器
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)

        self.left_sidebar = LeftSidebar(self.switch_account, self.add_account, self.batch_remove_accounts, self.open_global_canva)
        self.main_splitter.addWidget(self.left_sidebar)

        # 2. 中间区域（包含顶部栏、网页、日志区）
        center_container = QWidget()
        center_v_layout = QVBoxLayout(center_container)
        center_v_layout.setContentsMargins(0, 0, 0, 0)
        center_v_layout.setSpacing(0)

        # 顶部工具栏
        self.top_bar = TopBar(self.load_web_page, self.refresh_page, self.update_all_zoom, self.go_heygen_login, self.sync_canva_to_current)
        center_v_layout.addWidget(self.top_bar)

        # 3. 中间上下分割器（上方网页，下方日志）
        self.center_splitter = QSplitter(Qt.Orientation.Vertical)

        self.browser_stack = QStackedWidget()
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setObjectName("LogArea")

        self.center_splitter.addWidget(self.browser_stack)
        self.center_splitter.addWidget(self.log_area)

        center_v_layout.addWidget(self.center_splitter)
        self.main_splitter.addWidget(center_container)

        self.setCentralWidget(self.main_splitter)

        # 设置默认比例：左边窄(130)，中间宽；下方日志窄(100)，上方网页高
        self.main_splitter.setSizes([130, 1100])
        self.center_splitter.setSizes([800, 100])

        self.refresh_account_list_ui()
        self.restore_window_settings()

        if self.all_accounts: self.switch_account(self.all_accounts[0])
        self.cleanup_timer = QTimer(); self.cleanup_timer.timeout.connect(self.unload_inactive_browsers); self.cleanup_timer.start(60000)

    def log(self, text):
        ts = time.strftime("%H:%M:%S")
        self.log_area.append(f"<span style='color:#7f8c8d'>[{ts}]</span> {text}")
        self.log_area.verticalScrollBar().setValue(self.log_area.verticalScrollBar().maximum())

    def refresh_account_list_ui(self):
        lw = self.left_sidebar.account_list; curr_id = lw.currentItem().data(Qt.ItemDataRole.UserRole) if lw.currentItem() else None; lw.clear()
        for acc in reversed(self.all_accounts):
            it = QListWidgetItem(); it.setData(Qt.ItemDataRole.UserRole, acc); it.setSizeHint(QSize(0, 36)); lw.addItem(it)
            w = QWidget(); lay = QHBoxLayout(w); lay.setContentsMargins(5, 0, 5, 0)
            dot = QLabel("●"); dot.setStyleSheet(f"color: {'#3498db' if acc in self.instances else '#95a5a6'}; font-size: 14px; border:none;")
            txt = QLabel(f"环境 {acc}"); txt.setStyleSheet("color: #ecf0f1; font-weight: bold; border:none;")
            lay.addWidget(dot); lay.addWidget(txt); lay.addStretch(); lw.setItemWidget(it, w)
            if acc == curr_id: lw.setCurrentItem(it)
        lw.doItemsLayout()

    # ================= 业务与维护逻辑 =================
    def switch_account(self, aid):
        if aid not in self.instances:
            self.log(f"激活环境 {aid}...")
            inst = BrowserInstance(aid, self.storage_root, self.on_url_changed)
            inst.log_status.connect(self.log); self.instances[aid] = inst; self.browser_stack.addWidget(inst)
            inst.setUrl(QUrl("https://app.heygen.com/login"))
            self.refresh_account_list_ui()
        target = self.instances[aid]; target.last_accessed = time.time(); self.browser_stack.setCurrentWidget(target); self.top_bar.url_input.setText(target.url().toString())

    def open_global_canva(self):
        cid = "canva_global"
        if cid not in self.instances:
            self.log("加载 Canva 母本..."); inst = BrowserInstance(cid, self.storage_root, self.on_url_changed)
            inst.log_status.connect(self.log); self.instances[cid] = inst; self.browser_stack.addWidget(inst)
            inst.page().profile().cookieStore().cookieAdded.connect(self.on_canva_cookie_captured); inst.setUrl(QUrl("https://www.canva.com"))
        target = self.instances[cid]; target.last_accessed = time.time(); self.browser_stack.setCurrentWidget(target); self.left_sidebar.account_list.clearSelection()

    def unload_inactive_browsers(self):
        now = time.time(); curr = self.browser_stack.currentWidget()
        for i, inst in list(self.instances.items()):
            if inst != curr and now - inst.last_accessed > 600:
                if i == "canva_global" and now - inst.last_accessed < 1200: continue
                try: self.instances.pop(i); self.browser_stack.removeWidget(inst); inst.setPage(None); inst.deleteLater(); self.refresh_account_list_ui()
                except: pass

    def sync_canva_to_current(self):
        curr = self.browser_stack.currentWidget()
        if not curr or not self.canva_cookies_vault: self.log("❌ 无法同步：母本未登录"); return
        if time.time() - self.last_sync_time < 5: self.log("⏳ 冷却中..."); return
        self.last_sync_time = time.time(); dst = curr.page().profile().cookieStore()
        for c in self.canva_cookies_vault: dst.setCookie(c)
        QTimer.singleShot(1000, lambda: curr.setUrl(QUrl("https://www.canva.com")))

    def on_canva_cookie_captured(self, c):
        if "canva.com" in c.domain():
            for x in list(self.canva_cookies_vault):
                if x.name() == c.name() and x.domain() == c.domain(): self.canva_cookies_vault.remove(x); break
            self.canva_cookies_vault.append(c)

    # --- 系统支撑函数 ---
    def load_accounts_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f: return [int(l.strip()) for l in f if l.strip().isdigit()]
        return [1]
    def save_accounts_config(self):
        with open(self.config_file, "w") as f:
            for acc in self.all_accounts: f.write(f"{acc}\n")
    def add_account(self):
        nid = max(self.all_accounts)+1 if self.all_accounts else 1; self.all_accounts.append(nid); self.save_accounts_config(); self.refresh_account_list_ui()
    def batch_remove_accounts(self):
        sel = self.left_sidebar.account_list.selectedItems()
        if sel and QMessageBox.question(self, "确认", f"移除 {len(sel)} 个账号？") == QMessageBox.StandardButton.Yes:
            for it in sel:
                aid = it.data(Qt.ItemDataRole.UserRole); self.all_accounts.remove(aid) if aid in self.all_accounts else None
                if aid in self.instances: inst = self.instances.pop(aid); self.browser_stack.removeWidget(inst); inst.setPage(None); inst.deleteLater()
            self.save_accounts_config(); self.refresh_account_list_ui()
    def go_heygen_login(self): self.browser_stack.currentWidget().setUrl(QUrl("https://app.heygen.com/login"))
    def load_web_page(self, u): self.browser_stack.currentWidget().setUrl(QUrl(u if u.startswith("http") else "https://"+u))
    def refresh_page(self): self.browser_stack.currentWidget().reload()
    def update_all_zoom(self, v): [i.setZoomFactor(v) for i in self.instances.values()]
    def on_url_changed(self, id, url):
        try:
            if self.browser_stack.currentWidget() == self.instances.get(id): self.top_bar.url_input.setText(url)
        except: pass
    def restore_window_settings(self):
        geo = self.settings.value("geometry"); split_h = self.settings.value("main_splitter_state"); split_v = self.settings.value("center_splitter_state")
        if geo: self.restoreGeometry(geo)
        if split_h: self.main_splitter.restoreState(split_h)
        if split_v: self.center_splitter.restoreState(split_v)
    def closeEvent(self, event):
        self.settings.setValue("geometry", self.saveGeometry()); self.settings.setValue("main_splitter_state", self.main_splitter.saveState()); self.settings.setValue("center_splitter_state", self.center_splitter.saveState()); event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv); app.setFont(QFont("Microsoft YaHei", 10)); window = MainWindow(); window.show(); sys.exit(app.exec())
