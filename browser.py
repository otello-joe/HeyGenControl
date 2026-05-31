# browser.py
import os
import time
from PyQt6.QtWidgets import QDialog, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage, QWebEngineSettings, QWebEngineScript
from PyQt6.QtCore import QUrl, pyqtSignal

class CustomWebPage(QWebEnginePage):
    def __init__(self, profile, parent_browser=None):
        super().__init__(profile, parent_browser)
        self.parent_browser = parent_browser

    def createWindow(self, windowType):
        try:
            self.dialog = QDialog(self.parent_browser); self.dialog.setWindowTitle("安全验证"); self.dialog.resize(650, 750)
            lay = QVBoxLayout(self.dialog); lay.setContentsMargins(0, 0, 0, 0)
            view = QWebEngineView(self.dialog); page = CustomWebPage(self.profile(), self.parent_browser)
            view.setPage(page); lay.addWidget(view); page.windowCloseRequested.connect(self.dialog.accept)
            self.dialog.show(); return page
        except: return None

    def javaScriptConsoleMessage(self, level, message, line, sourceID):
        if "LOG:" in message:
            try: self.parent_browser.log_status.emit(message.replace("LOG:", "").strip())
            except: pass
        return

class BrowserInstance(QWebEngineView):
    log_status = pyqtSignal(str)

    def __init__(self, instance_id, storage_root, url_callback):
        super().__init__()
        self.instance_id = instance_id
        self.last_accessed = time.time()

        # 确保存储路径
        storage_path = os.path.join(storage_root, f"acc_{instance_id}")
        os.makedirs(storage_path, exist_ok=True)

        self.profile = QWebEngineProfile(f"storage_{instance_id}", self)
        self.profile.setPersistentStoragePath(storage_path)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)
        self.profile.setHttpCacheMaximumSize(50 * 1024 * 1024)

        settings = self.profile.settings()
        def safe_set(attr, val):
            try: settings.setAttribute(getattr(QWebEngineSettings.WebAttribute, attr), val)
            except: pass

        safe_set("WebSecurityEnabled", False); safe_set("ThirdPartyCookiesPolicy", True)
        safe_set("LocalStorageEnabled", True); safe_set("WebGLEnabled", True)
        safe_set("Accelerated2dCanvasEnabled", True); safe_set("JavascriptCanAccessClipboard", True)

        self.setup_stealth()
        self.setPage(CustomWebPage(self.profile, self))
        self.setZoomFactor(0.75)
        self.urlChanged.connect(lambda qurl: url_callback(self.instance_id, qurl.toString()))

    def setup_stealth(self):
        js = """(function() {
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });
            Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
            window.chrome = { app: { isInstalled: false }, runtime: {}, loadTimes: () => ({}), csi: () => ({}) };
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) return 'Google Inc. (Intel)';
                if (parameter === 37446) return 'ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0)';
                return getParameter.apply(this, arguments);
            };
        })();"""
        script = QWebEngineScript()
        script.setSourceCode(js); script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        script.setRunsOnSubFrames(True); self.profile.scripts().insert(script)
