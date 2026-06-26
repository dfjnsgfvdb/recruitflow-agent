import os
import sys

import uvicorn


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


if __name__ == "__main__":
    # Windows + Anaconda + Python 3.8 下，uvicorn reload 子进程在 Ctrl+C 退出时
    # 容易打印 KeyboardInterrupt / CancelledError 堆栈。默认关闭 reload，保证退出干净。
    # 如需热重载，可在 PowerShell 中设置：$env:UVICORN_RELOAD="true"
    reload_enabled = _env_bool("UVICORN_RELOAD", default=sys.platform != "win32")
    try:
        uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=reload_enabled)
    except KeyboardInterrupt:
        print("Server stopped.")
