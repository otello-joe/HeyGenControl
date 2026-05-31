# main.py
import os
import sys

# =================================================================
# 【Windows 黑屏关键修复】
# 必须在所有 PyQt 导入之前，甚至在所有逻辑之前设置
# =================================================================
from PyQt6.QtCore import Qt, QCoreApplication
if sys.platform == "win32":
    # 强制使用桌面显卡 OpenGL 渲染，解决 Windows 环境下的黑屏问题
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_UseDesktopOpenGL)
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

# 【针对 Windows 优化启动参数】
# 加入了 --disable-gpu-compositing，这比完全禁用 GPU 性能更好且能解决黑屏
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    "--disable-web-security "
    "--disable-site-isolation-trials "
    "--no-sandbox "
    "--disable-blink-features=AutomationControlled "
    "--disable-webrtc "
    "--ignore-gpu-blocklist "
    "--disable-gpu-compositing " # Windows 兼容性修复
    "--enable-gpu-rasterization "
    "--num-raster-threads=2"     # 减少线程数，提升窄边栏操作的响应速度
)
# =================================================================

import time
import json
import random
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QStackedWidget, QTextEdit, QSplitter,
                             QListWidgetItem, QLabel, QMessageBox)
from PyQt6.QtCore import QUrl, QTimer, QSettings, QSize
from PyQt6.QtGui import QFont, QIcon

# 导入自定义组件
from styles import STYLE_SHEET
from browser import BrowserInstance
from ui_components import LeftSidebar, TopBar

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HeyGen 群控自动化 v1.0 (Stable-Pro)")
        self.setStyleSheet(STYLE_SHEET)
        self.setWindowIcon(QIcon(resource_path("heygen-logo.ico")))

        # 跨平台路径识别
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
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.left_sidebar = LeftSidebar(self.switch_account, self.add_account, self.batch_remove_accounts, self.open_global_canva)
        self.main_splitter.addWidget(self.left_sidebar)

        center_container = QWidget(); c_v_lay = QVBoxLayout(center_container); c_v_lay.setContentsMargins(0,0,0,0); c_v_lay.setSpacing(0)
        self.top_bar = TopBar(self.load_web_page, self.refresh_page, self.update_all_zoom, self.go_heygen_login, self.sync_canva_to_current)

        self.center_splitter = QSplitter(Qt.Orientation.Vertical)
        self.browser_stack = QStackedWidget()
        self.log_area = QTextEdit(); self.log_area.setReadOnly(True); self.log_area.setObjectName("LogArea")

        self.center_splitter.addWidget(self.browser_stack); self.center_splitter.addWidget(self.log_area)
        c_v_lay.addWidget(self.top_bar); c_v_lay.addWidget(self.center_splitter)

        self.main_splitter.addWidget(center_container)
        self.setCentralWidget(self.main_splitter)

        self.main_splitter.setSizes([130, 1100])
        self.center_splitter.setSizes([800, 100])

        self.refresh_account_list_ui()
        self.restore_window_settings()

        self.log("🚀 HeyGen 群控 v1.0 启动成功 (OpenGL 渲染模式)。")
        if self.all_accounts:
            self.switch_account(self.all_accounts[0])

        self.cleanup_timer = QTimer(); self.cleanup_timer.timeout.connect(self.unload_inactive_browsers); self.cleanup_timer.start(60000)

    # ================= 核心逻辑：日志、切换、同步 (保持之前版本) =================
    def log(self, text):
        try:
            ts = time.strftime("%H:%M:%S")
            curr_w = self.browser_stack.currentWidget()
            prefix = "System"
            if curr_w:
                iid = getattr(curr_w, 'instance_id', 'Unknown')
                prefix = "Canva" if iid == "canva_global" else f"Acc-{iid}"
            log_html = f"<span style='color:#555555'>[{ts}]</span> <span style='color:#2ecc71'><b>[{prefix}]</b> {text}</span>"
            self.log_area.append(log_html)
            self.log_area.verticalScrollBar().setValue(self.log_area.verticalScrollBar().maximum())
        except: pass

    def refresh_account_list_ui(self):
        lw = self.left_sidebar.account_list; cid = lw.currentItem().data(Qt.ItemDataRole.UserRole) if lw.currentItem() else None; lw.clear()
        for acc in reversed(self.all_accounts):
            it = QListWidgetItem(); it.setData(Qt.ItemDataRole.UserRole, acc); it.setSizeHint(QSize(0, 36)); lw.addItem(it)
            w = QWidget(); lay = QHBoxLayout(w); lay.setContentsMargins(5, 0, 5, 0)
            dot = QLabel("●"); dot.setStyleSheet(f"color: {'#3498db' if acc in self.instances else '#95a5a6'}; font-size: 14px; border:none;")
            txt = QLabel(f"环境 {acc}"); txt.setStyleSheet("color: #ecf0f1; font-weight: bold; border:none;")
            lay.addWidget(dot); lay.addWidget(txt); lay.addStretch(); lw.setItemWidget(it, w)
            if acc == cid: lw.setCurrentItem(it)
        lw.doItemsLayout()

    def switch_account(self, aid):
        if aid not in self.instances:
            self.log(f"加载环境 {aid}...")
            inst = BrowserInstance(aid, self.storage_root, self.on_url_changed)
            inst.log_status.connect(self.log)
            self.instances[aid] = inst; self.browser_stack.addWidget(inst)
            inst.setUrl(QUrl("https://app.heygen.com/login"))
            self.refresh_account_list_ui()
        target = self.instances[aid]; target.last_accessed = time.time(); self.browser_stack.setCurrentWidget(target); self.top_bar.url_input.setText(target.url().toString())

    def open_global_canva(self):
        cid = "canva_global"
        if cid not in self.instances:
            inst = BrowserInstance(cid, self.storage_root, self.on_url_changed)
            inst.log_status.connect(self.log); self.instances[cid] = inst; self.browser_stack.addWidget(inst)
            inst.page().profile().cookieStore().cookieAdded.connect(self.on_canva_cookie_captured); inst.setUrl(QUrl("https://www.canva.com"))
        target = self.instances[cid]; target.last_accessed = time.time(); self.browser_stack.setCurrentWidget(target); self.left_sidebar.account_list.clearSelection()

    def sync_canva_to_current(self):
        curr = self.browser_stack.currentWidget()
        if not curr or not self.canva_cookies_vault: self.log("❌ 无法同步：母本未登录"); return
        if time.time() - self.last_sync_time < 5: self.log("⏳ 冷却中..."); return
        self.last_sync_time = time.time(); dst = curr.page().profile().cookieStore()
        for c in self.canva_cookies_vault: dst.setCookie(c)
        QTimer.singleShot(1000, lambda: curr.setUrl(QUrl("https://www.canva.com")))

    def unload_inactive_browsers(self):
        now = time.time(); curr = self.browser_stack.currentWidget()
        for i, inst in list(self.instances.items()):
            if inst != curr and now - inst.last_accessed > 600:
                if i == "canva_global" and now - inst.last_accessed < 1200: continue
                try: self.instances.pop(i); self.browser_stack.removeWidget(inst); inst.setPage(None); inst.deleteLater(); self.refresh_account_list_ui()
                except: pass

    def on_canva_cookie_captured(self, c):
        if "canva.com" in c.domain():
            for x in list(self.canva_cookies_vault):
                if x.name() == c.name() and x.domain() == c.domain(): self.canva_cookies_vault.remove(x); break
            self.canva_cookies_vault.append(c)

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
            for item in sel:
                aid = item.data(Qt.ItemDataRole.UserRole); self.all_accounts.remove(aid) if aid in self.all_accounts else None
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
        geo = self.settings.value("geometry"); s1 = self.settings.value("main_splitter_state"); s2 = self.settings.value("center_splitter_state")
        if geo: self.restoreGeometry(geo)
        if s1: self.main_splitter.restoreState(s1)
        if s2: self.center_splitter.restoreState(s2)
    def save_window_settings(self):
        self.settings.setValue("geometry", self.saveGeometry()); self.settings.setValue("main_splitter_state", self.main_splitter.saveState()); self.settings.setValue("center_splitter_state", self.center_splitter.saveState())
    def closeEvent(self, event):
        self.save_window_settings(); event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv); app.setFont(QFont("Microsoft YaHei", 10)); window = MainWindow(); window.show(); sys.exit(app.exec())
