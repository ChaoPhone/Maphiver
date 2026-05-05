import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 确定基础目录（支持 PyInstaller 打包）
if os.environ.get("BASE_DIR"):
    BASE_DIR = Path(os.environ["BASE_DIR"])
elif getattr(sys, 'frozen', False):
    # PyInstaller 打包后的 exe 所在目录
    BASE_DIR = Path(sys.executable).parent
else:
    # 正常开发模式
    BASE_DIR = Path(__file__).parent.parent

load_dotenv(str(BASE_DIR / ".env") if (BASE_DIR / ".env").exists() else None)

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DATABASE_PATH = DATA_DIR / "maphiver.db"

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")

UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))