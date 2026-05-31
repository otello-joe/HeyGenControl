# main.py
import os
import sys

# 【顶级提权与显卡加速】
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

# 导入自定义组件
from styles import STYLE_SHEET
from browser import BrowserInstance
from ui_components import LeftSidebar, TopBar
from PyQt6.QtGui import QFont, QIcon # 增加 QIcon

def resource_path(relative_path):
    """ 获取资源的绝对路径，兼容开发环境和 PyInstaller 打包后的路径 """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HeyGen 群控自动化 v1.0")
        self.setStyleSheet(STYLE_SHEET)

        # 【核心修改】：设置窗口图标
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

        # 传入带有日志记录的回调
        self.top_bar = TopBar(
            self.load_web_page,
            self.refresh_page,
            self.update_all_zoom,
            self.go_heygen_login,
            self.sync_canva_to_current
        )
        c_v_lay.addWidget(self.top_bar)

        self.center_splitter = QSplitter(Qt.Orientation.Vertical)
        self.browser_stack = QStackedWidget()
        self.log_area = QTextEdit(); self.log_area.setReadOnly(True); self.log_area.setObjectName("LogArea")

        self.center_splitter.addWidget(self.browser_stack); self.center_splitter.addWidget(self.log_area)
        c_v_lay.addWidget(self.center_splitter)
        self.main_splitter.addWidget(center_container)

        self.setCentralWidget(self.main_splitter)
        self.main_splitter.setSizes([130, 1100])
        self.center_splitter.setSizes([800, 100])

        self.refresh_account_list_ui()
        self.restore_window_settings()

        self.log("🚀 HeyGen 群控 v1.0 启动成功。")
        if self.all_accounts:
            self.switch_account(self.all_accounts[0])

        self.cleanup_timer = QTimer(); self.cleanup_timer.timeout.connect(self.unload_inactive_browsers); self.cleanup_timer.start(60000)

    # ================= 核心日志函数 =================
    def log(self, text):
        """记录系统日志：统一亮绿色排版"""
        try:
            ts = time.strftime("%H:%M:%S")
            curr_w = self.browser_stack.currentWidget()
            prefix = "System"
            if curr_w:
                iid = getattr(curr_w, 'instance_id', 'Unknown')
                prefix = "Canva" if iid == "canva_global" else f"Acc-{iid}"

            # 使用 HTML 确保颜色精准展示为亮绿色 (#2ecc71)
            log_html = f"<span style='color:#2ecc71'>[{ts}] <b>[{prefix}]</b> {text}</span>"
            self.log_area.append(log_html)
            self.log_area.verticalScrollBar().setValue(self.log_area.verticalScrollBar().maximum())
        except:
            pass

    # ================= 业务动作（全部增加日志输出） =================

    def go_heygen_login(self):
        """点击『HeyGen 首页』按钮"""
        self.log("🏠 正在尝试跳转至 HeyGen 登录页...")
        w = self.browser_stack.currentWidget()
        if w: w.setUrl(QUrl("https://app.heygen.com/login"))

    def sync_canva_to_current(self):
        """点击『同步至 Canva』按钮"""
        curr = self.browser_stack.currentWidget()
        if not curr or not self.canva_cookies_vault:
            self.log("❌ <span style='color:#e74c3c'>同步失败：『公共 Canva』尚未登录，无凭证可供同步。</span>")
            return

        now = time.time()
        if now - self.last_sync_time < 5:
            self.log(f"⏳ <span style='color:#f39c12'>操作频繁：请等待 {int(5-(now-self.last_sync_time))} 秒后再同步。</span>")
            return

        self.last_sync_time = now
        self.log(f"🔄 正在同步 {len(self.canva_cookies_vault)} 条凭证，并跳转至 Canva...")
        dst = curr.page().profile().cookieStore()
        for c in self.canva_cookies_vault: dst.setCookie(c)
        QTimer.singleShot(1000, lambda: curr.setUrl(QUrl("https://www.canva.com")))

    def switch_account(self, aid):
        """点击左侧列表切换账号"""
        if aid not in self.instances:
            self.log(f"⚙️ 正在初始化新环境：{aid} ...")
            inst = BrowserInstance(aid, self.storage_root, self.on_url_changed)
            inst.log_status.connect(self.log)
            self.instances[aid] = inst; self.browser_stack.addWidget(inst)
            inst.setUrl(QUrl("https://app.heygen.com/login"))
            self.refresh_account_list_ui()

        target = self.instances[aid]
        target.last_accessed = time.time()
        self.browser_stack.setCurrentWidget(target)
        self.top_bar.url_input.setText(target.url().toString())
        self.log(f"✅ 已切换至环境 {aid}")

    def load_web_page(self, u):
        """地址栏跳转"""
        w = self.browser_stack.currentWidget()
        if w:
            url_str = u if u.startswith("http") else "https://" + u
            self.log(f"🌐 正在跳转至: {url_str}")
            w.setUrl(QUrl(url_str))

    def refresh_page(self):
        """点击刷新"""
        w = self.browser_stack.currentWidget()
        if w:
            self.log("🔄 正在刷新当前页面...")
            w.reload()

    def add_account(self):
        """添加账号按钮"""
        nid = max(self.all_accounts)+1 if self.all_accounts else 1
        self.all_accounts.append(nid)
        self.save_accounts_config()
        self.refresh_account_list_ui()
        self.log(f"➕ 成功添加新环境 ID: {nid}")

    def batch_remove_accounts(self):
        """移除显示按钮"""
        sel = self.left_sidebar.account_list.selectedItems()
        if not sel: return
        count = len(sel)
        if QMessageBox.question(self, "确认", f"确定从视图移除选中的 {count} 个账号？") == QMessageBox.StandardButton.Yes:
            for it in sel:
                aid = it.data(Qt.ItemDataRole.UserRole)
                if aid in self.all_accounts: self.all_accounts.remove(aid)
                if aid in self.instances:
                    inst = self.instances.pop(aid); self.browser_stack.removeWidget(inst); inst.setPage(None); inst.deleteLater()
            self.save_accounts_config()
            self.refresh_account_list_ui()
            self.log(f"🗑️ 已批量移除 {count} 个显示项。")

    def unload_inactive_browsers(self):
        """内存回收巡检"""
        now = time.time(); curr_view = self.browser_stack.currentWidget()
        for aid, inst in list(self.instances.items()):
            if inst == curr_view: continue
            if aid == "canva_global" and now - inst.last_accessed < 1200: continue
            if now - inst.last_accessed > 600:
                self.log(f"♻️ 内存回收：账号 {aid} 已闲置10分钟，执行自动卸载。")
                try: self.instances.pop(aid); self.browser_stack.removeWidget(inst); inst.setPage(None); inst.deleteLater(); self.refresh_account_list_ui()
                except: pass

    # --- 基础支撑逻辑保持不变 ---
    def open_global_canva(self):
        cid = "canva_global"
        if cid not in self.instances:
            self.log("🎨 正在初始化公共 Canva 母本...")
            inst = BrowserInstance(cid, self.storage_root, self.on_url_changed)
            inst.log_status.connect(self.log); self.instances[cid] = inst; self.browser_stack.addWidget(inst)
            inst.page().profile().cookieStore().cookieAdded.connect(self.on_canva_cookie_captured)
            inst.setUrl(QUrl("https://www.canva.com"))
        target = self.instances[cid]; target.last_accessed = time.time(); self.browser_stack.setCurrentWidget(target); self.left_sidebar.account_list.clearSelection()
        self.log("✅ 已切换至母本环境。")

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
