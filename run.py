"""
Maphiver - 一键启动开发环境
用法: python run.py
"""

import os
import sys
import time
import signal
import shutil
import webbrowser
import threading
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"
VENV_DIR = BACKEND_DIR / ".venv"

BACKEND_PORT = 8742
FRONTEND_PORT = 4173

processes = []


def get_venv_python() -> Path:
    """获取虚拟环境中的 Python 可执行路径"""
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def ensure_venv() -> bool:
    """如果虚拟环境不存在则创建"""
    if VENV_DIR.exists():
        return True
    log("正在创建虚拟环境...")
    r = subprocess.run(
        [sys.executable, "-m", "venv", str(VENV_DIR)],
        capture_output=True, text=True
    )
    if r.returncode != 0:
        err(f"创建虚拟环境失败:\n{r.stderr}")
        return False
    ok("虚拟环境创建成功")
    return True


def log(msg):
    print(f"  [INFO] {msg}")


def ok(msg):
    print(f"  [OK] {msg}")


def err(msg):
    print(f"  [ERROR] {msg}")


def check_python():
    """检查 Python 环境，确保虚拟环境可用"""
    if not ensure_venv():
        return False
    venv_python = get_venv_python()
    try:
        subprocess.run([str(venv_python), "--version"], check=True, capture_output=True)
    except:
        err("虚拟环境 Python 不可用")
        return False
    try:
        subprocess.run([str(venv_python), "-m", "pip", "--version"], check=True, capture_output=True)
        return True
    except:
        err("虚拟环境中 pip 不可用")
        return False


def check_node():
    try:
        subprocess.run(["node", "--version"], check=True, capture_output=True)
        subprocess.run(["npm", "--version"], check=True, capture_output=True, shell=True)
        return True
    except:
        err("Node.js/npm not found")
        return False


def install_python_deps():
    """在虚拟环境中安装 Python 依赖"""
    log("正在安装 Python 依赖...")
    venv_python = get_venv_python()
    r = subprocess.run(
        [str(venv_python), "-m", "pip", "install", "-r", str(BACKEND_DIR / "requirements.txt"), "-q"],
        capture_output=True, text=True
    )
    if r.returncode != 0:
        err(f"pip 安装失败:\n{r.stderr}")
        return False
    ok("Python 依赖安装完成")
    return True


def install_npm_deps():
    if (FRONTEND_DIR / "node_modules").exists():
        ok("Node modules already installed")
        return True
    log("Installing npm dependencies...")
    r = subprocess.run(["npm", "install"], cwd=str(FRONTEND_DIR), capture_output=True, text=True, shell=True)
    if r.returncode != 0:
        err(f"npm install failed:\n{r.stderr}")
        return False
    ok("npm dependencies installed")
    return True


def start_backend():
    log(f"启动 Backend: http://localhost:{BACKEND_PORT}")
    venv_python = get_venv_python()
    proc = subprocess.Popen(
        [str(venv_python), "-m", "uvicorn", "main:app", "--reload", "--port", str(BACKEND_PORT)],
        cwd=str(BACKEND_DIR), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        encoding="utf-8", errors="replace", bufsize=1
    )
    processes.append(proc)
    return proc


def start_frontend():
    log(f"Starting Frontend on http://localhost:{FRONTEND_PORT}")
    proc = subprocess.Popen(
        ["npm", "run", "dev"], cwd=str(FRONTEND_DIR),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        encoding="utf-8", errors="replace", bufsize=1, shell=True
    )
    processes.append(proc)
    return proc


def wait_for_backend(proc, timeout=30):
    import urllib.request, urllib.error
    log("Waiting for Backend to be ready...")
    start = time.time()
    while time.time() - start < timeout:
        if proc.poll() is not None:
            return False
        try:
            resp = urllib.request.urlopen(f"http://localhost:{BACKEND_PORT}/api/health", timeout=2)
            if resp.status == 200:
                ok("Backend is ready!")
                return True
        except:
            pass
        time.sleep(1)
    err(f"Backend not responding within {timeout}s")
    return False


def read_output(proc, prefix):
    for line in iter(proc.stdout.readline, ""):
        line = line.rstrip()
        if line:
            print(f"[{prefix}] {line}")
    if proc.stdout and not proc.stdout.closed:
        proc.stdout.close()


def cleanup(signum=None, frame=None):
    print("\n[INFO] Shutting down...")
    for proc in processes:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except:
                proc.kill()
    print("[INFO] All services stopped.")
    sys.exit(0)


def main():
    print("""
==================================
  Maphiver v0.2.7
==================================
""")

    if not check_python():
        sys.exit(1)
    if not check_node():
        sys.exit(1)

    env_file = BACKEND_DIR / ".env"
    if not env_file.exists():
        log("Creating backend/.env from .env.example...")
        shutil.copy(str(BACKEND_DIR / ".env.example"), str(env_file))
        err("Please edit backend/.env and set DEEPSEEK_API_KEY, then restart.")
        sys.exit(1)

    if not install_python_deps():
        sys.exit(1)
    if not install_npm_deps():
        sys.exit(1)

    backend_proc = start_backend()
    frontend_proc = start_frontend()

    wait_for_backend(backend_proc)

    time.sleep(3)
    webbrowser.open(f"http://localhost:{FRONTEND_PORT}")

    print(f"""
==================================
  Backend : http://localhost:{BACKEND_PORT}
  Frontend: http://localhost:{FRONTEND_PORT}
==================================
  Press Ctrl+C to stop all services.
""")

    t1 = threading.Thread(target=read_output, args=(backend_proc, "BACKEND"), daemon=True)
    t2 = threading.Thread(target=read_output, args=(frontend_proc, "FRONTEND"), daemon=True)
    t1.start()
    t2.start()

    backend_proc.wait()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    main()
