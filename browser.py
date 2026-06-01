# browser.py
import os
import time
import random
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

        # 1. 为当前环境生成唯一指纹数据
        random.seed(str(instance_id))
        self.fp_mem = random.choice([4, 8, 16])
        self.fp_cpu = random.choice([4, 8, 12])
        self.fp_res = random.choice([(1920, 1080), (1440, 900), (1536, 864)])

        storage_path = os.path.join(storage_root, f"acc_{instance_id}")
        os.makedirs(storage_path, exist_ok=True)

        self.profile = QWebEngineProfile(f"storage_{instance_id}", self)
        self.profile.setPersistentStoragePath(storage_path)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)
        self.profile.setHttpCacheMaximumSize(40 * 1024 * 1024)

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
        """【深度指纹伪装】：修正了花括号冲突报错"""
        # 使用普通字符串，并通过 .replace 注入变量
        js_template = """(function() {
            // 1. 抹除自动化痕迹
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

            // 2. 硬件环境随机化
            Object.defineProperty(navigator, 'deviceMemory', { get: () => FP_MEM });
            Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => FP_CPU });

            // 3. 屏幕分辨率伪装
            Object.defineProperty(window.screen, 'width', { get: () => FP_RES_W });
            Object.defineProperty(window.screen, 'height', { get: () => FP_RES_H });

            // 4. 补全 Chrome 特有对象
            window.chrome = { app: { isInstalled: false }, runtime: {}, loadTimes: () => ({}), csi: () => ({}) };

            // 5. 阻止 Canva 探测 WebGL 真实指纹
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) return 'Google Inc. (Intel)';
                if (parameter === 37446) return 'ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0)';
                return getParameter.apply(this, arguments);
            };
        })();"""

        js = js_template.replace("FP_MEM", str(self.fp_mem))\
                         .replace("FP_CPU", str(self.fp_cpu))\
                         .replace("FP_RES_W", str(self.fp_res[0]))\
                         .replace("FP_RES_H", str(self.fp_res[1]))

        script = QWebEngineScript()
        script.setSourceCode(js)
        script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        script.setRunsOnSubFrames(True)
        self.profile.scripts().insert(script)
