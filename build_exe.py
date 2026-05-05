"""
Maphiver exe 打包脚本
用法: python build_exe.py
"""

import subprocess
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
FRONTEND = ROOT / "frontend"
BACKEND = ROOT / "backend"
DIST_DIR = ROOT / "dist"


def build_frontend():
    """构建前端静态文件"""
    print("[1/3] 构建前端...")
    if (FRONTEND / "dist").exists():
        shutil.rmtree(str(FRONTEND / "dist"))
    # 使用 vite build 直接构建，跳过 vue-tsc 类型检查（Node v24 不兼容）
    r = subprocess.run(
        ["npm", "run", "build", "--", "--skip-ts"],
        cwd=str(FRONTEND),
        shell=True,
        capture_output=True,
        text=True
    )
    if r.returncode != 0:
        # 如果带参数失败，尝试直接 vite build
        r = subprocess.run(
            [str(FRONTEND / "node_modules" / ".bin" / "vite.cmd"), "build"],
            cwd=str(FRONTEND),
            shell=True,
            capture_output=True,
            text=True
        )
    if r.returncode != 0:
        print(f"[ERROR] 前端构建失败:\n{r.stderr}")
        return False
    print("[OK] 前端构建完成")
    return True


def build_exe():
    """PyInstaller 打包"""
    print("[2/3] PyInstaller 打包...")

    # 清理旧构建
    if (ROOT / "build").exists():
        shutil.rmtree(str(ROOT / "build"))
    if DIST_DIR.exists():
        shutil.rmtree(str(DIST_DIR))

    # PyInstaller 命令
    cmd = [
        "pyinstaller",
        "--onefile",                    # 单文件 exe
        "--windowed",                   # 无控制台窗口
        "--name", "Maphiver",           # exe 名称
        "--icon", str(ROOT / "image" / "icon.ico") if (ROOT / "image" / "icon.ico").exists() else None,
        # 包含数据文件
        "--add-data", f"{FRONTEND / 'dist'};frontend/dist",
        "--add-data", f"{BACKEND / 'prompts'};backend/prompts",
        # 隐藏导入（FastAPI/uvicorn 常见遗漏）
        "--hidden-import", "uvicorn.logging",
        "--hidden-import", "uvicorn.loops",
        "--hidden-import", "uvicorn.loops.auto",
        "--hidden-import", "uvicorn.protocols",
        "--hidden-import", "uvicorn.protocols.http",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "uvicorn.protocols.websockets",
        "--hidden-import", "uvicorn.protocols.websockets.auto",
        "--hidden-import", "uvicorn.lifespan",
        "--hidden-import", "uvicorn.lifespan.on",
        "--hidden-import", "httpcore",
        "--hidden-import", "httpcore._backends",
        "--hidden-import", "httpcore._backends.auto",
        "--hidden-import", "anyio",
        "--hidden-import", "anyio._backends",
        "--hidden-import", "anyio._backends._asyncio",
        "--hidden-import", "starlette",
        "--hidden-import", "starlette.responses",
        "--hidden-import", "starlette.routing",
        "--hidden-import", "starlette.middleware",
        "--hidden-import", "starlette.middleware.cors",
        "--hidden-import", "starlette.staticfiles",
        "--hidden-import", "sqlite3",
        "--hidden-import", "fitz",              # PyMuPDF
        "--hidden-import", "docx",             # python-docx
        "--hidden-import", "openai",
        "--hidden-import", "httpx",
        "--hidden-import", "jose",
        "--hidden-import", "passlib",
        "--hidden-import", "bcrypt",
        "--hidden-import", "python_multipart",
        "--hidden-import", "aiofiles",
        # 排除不需要的模块
        "--exclude-module", "tkinter",
        "--exclude-module", "matplotlib",
        "--exclude-module", "PIL",
        "--exclude-module", "pytest",
        # 工作目录
        "--workpath", str(ROOT / "build"),
        "--distpath", str(DIST_DIR),
        "--specpath", str(ROOT),
        # 入口文件
        str(ROOT / "serve.py"),
    ]

    # 过滤掉 None 值（icon 可能不存在）
    cmd = [c for c in cmd if c is not None]

    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)

    if r.returncode != 0:
        print(f"[ERROR] PyInstaller 打包失败:\n{r.stderr}")
        return False

    print("[OK] 打包完成")
    return True


def copy_data_files():
    """复制数据目录模板到 dist"""
    print("[3/3] 创建数据目录模板...")
    exe_dir = DIST_DIR
    data_dir = exe_dir / "data"
    data_dir.mkdir(exist_ok=True)
    (data_dir / "uploads").mkdir(exist_ok=True)
    (data_dir / "images").mkdir(exist_ok=True)

    # 复制 .env.example
    env_example = BACKEND / ".env.example"
    if env_example.exists():
        shutil.copy(str(env_example), str(exe_dir / ".env.example"))
        print("[OK] 已复制 .env.example")
        print("[INFO] 运行 exe 前请创建 .env 文件并设置 DEEPSEEK_API_KEY")

    return True


def main():
    print("""
==================================
  Maphiver exe 打包工具
==================================
""")

    # 检查 pyinstaller
    r = subprocess.run(["pyinstaller", "--version"], capture_output=True, text=True, shell=True)
    if r.returncode != 0:
        print("[ERROR] PyInstaller 未安装，请运行: pip install pyinstaller")
        return

    if not build_frontend():
        return
    if not build_exe():
        return
    if not copy_data_files():
        return

    print(f"""
==================================
  打包完成！
==================================
  输出位置: {DIST_DIR / 'Maphiver.exe'}

  使用说明:
  1. 将 Maphiver.exe 放到目标目录
  2. 创建 .env 文件并设置 DEEPSEEK_API_KEY
  3. 双击运行 Maphiver.exe
==================================
""")


if __name__ == "__main__":
    main()