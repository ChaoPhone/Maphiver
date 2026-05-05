"""
Maphiver 生产环境入口
打包为 exe 后运行此文件，同时提供 API 和前端静态文件服务
"""

import sys
import os
import webbrowser
import threading
import time
from pathlib import Path

# 确定基础目录
# PyInstaller --onefile 会将数据解压到 sys._MEIPASS
# exe 实际运行位置是 sys.executable
if getattr(sys, 'frozen', False):
    # 打包后的 exe
    EXE_DIR = Path(sys.executable).parent      # exe 所在目录（数据存储）
    MEIPASS = Path(sys._MEIPASS)               # PyInstaller 解压的临时目录
    BASE_DIR = MEIPASS                         # 代码和数据文件在 MEIPASS
    DATA_BASE_DIR = EXE_DIR                    # 用户数据存储在 exe 旁
else:
    # 开发模式
    BASE_DIR = Path(__file__).parent
    DATA_BASE_DIR = BASE_DIR

# 将 backend 目录加入 path
BACKEND_DIR = BASE_DIR / "backend"
if BACKEND_DIR.exists():
    sys.path.insert(0, str(BACKEND_DIR))

# 设置环境变量（用户数据目录）
os.environ["BASE_DIR"] = str(DATA_BASE_DIR)

# 加载 .env（优先从 exe 旁加载）
env_file = DATA_BASE_DIR / ".env"
if not env_file.exists() and (DATA_BASE_DIR / ".env.example").exists():
    print(f"[WARN] .env 不存在，请从 .env.example 复制并配置 DEEPSEEK_API_KEY")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from api import documents, sessions, qa, health, footprints, cards, document_links, export, images
from repositories.database import init_db

init_db()

app = FastAPI(
    title="Maphiver",
    description="流式知识河",
    version="0.2.7",
)

# CORS 允许本地访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(qa.router, prefix="/api/qa", tags=["qa"])
app.include_router(footprints.router, prefix="/api/footprints", tags=["footprints"])
app.include_router(cards.router, prefix="/api/cards", tags=["cards"])
app.include_router(document_links.router, prefix="/api", tags=["document-links"])
app.include_router(export.router, prefix="/api", tags=["export"])
app.include_router(images.router, prefix="/api/images", tags=["images"])

# 挂载前端静态文件
# 打包后: MEIPASS/frontend/dist
# 开发模式: BASE_DIR/frontend/dist
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="static")
else:
    print(f"[WARN] 前端静态文件未找到: {FRONTEND_DIST}")
    print("[WARN] 请先运行 npm run build 或重新打包 exe")


def open_browser():
    """延迟打开浏览器"""
    time.sleep(2)
    webbrowser.open("http://localhost:8742")


def main():
    port = 8742
    print(f"""
==================================
  Maphiver v0.2.7
==================================
  服务地址: http://localhost:{port}
==================================
""")
    # 启动浏览器
    threading.Thread(target=open_browser, daemon=True).start()

    # 启动服务
    uvicorn.run(app, host="127.0.0.1", port=port)


if __name__ == "__main__":
    main()