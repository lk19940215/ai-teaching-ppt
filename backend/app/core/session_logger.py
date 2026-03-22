"""
会话级别文件日志

每个会话生成独立日志文件，记录完整的处理流程：
  上传 → 解析 → AI 处理 → 预览图生成 → 组合 → 下载

日志存放在 logs/ 目录下，每个会话一个文件（{session_id}.log）。
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from ..config import settings

logger = logging.getLogger(__name__)

_LOG_DIR = Path(settings.BASE_DIR) / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)


class SessionLogger:
    """单个会话的日志记录器"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self._start_times: dict[str, float] = {}
        self._log_path = _LOG_DIR / f"{session_id}.log"

    def _write(self, lines: list[str]) -> None:
        with open(self._log_path, "a", encoding="utf-8") as f:
            for line in lines:
                f.write(line + "\n")

    def _ts(self) -> str:
        return datetime.now().strftime("%H:%M:%S.%f")[:-3]

    def begin(self, stage: str, **meta: Any) -> None:
        """记录阶段开始"""
        self._start_times[stage] = time.time()
        lines = [
            "",
            f"[{self._ts()}] [{self.session_id}] ▶ {stage}",
        ]
        if meta:
            for k, v in meta.items():
                lines.append(f"  {k}: {v}")
        self._write(lines)

    def end(self, stage: str, *, success: bool = True, **meta: Any) -> None:
        """记录阶段结束"""
        elapsed = time.time() - self._start_times.pop(stage, time.time())
        status = "✓" if success else "✗"
        lines = [
            f"[{self._ts()}] [{self.session_id}] {status} {stage} ({elapsed:.1f}s)",
        ]
        if meta:
            for k, v in meta.items():
                val = json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v)
                if len(val) > 200:
                    val = val[:200] + "..."
                lines.append(f"  {k}: {val}")
        self._write(lines)

    def section(self, title: str) -> None:
        """写入分隔线"""
        self._write([
            "",
            "=" * 60,
            f"[{self._ts()}] [{self.session_id}] {title}",
            "=" * 60,
        ])

    def info(self, message: str, **meta: Any) -> None:
        """记录信息"""
        lines = [f"[{self._ts()}] [{self.session_id}] ℹ {message}"]
        for k, v in meta.items():
            lines.append(f"  {k}: {v}")
        self._write(lines)

    def error(self, message: str, **meta: Any) -> None:
        """记录错误"""
        lines = [f"[{self._ts()}] [{self.session_id}] ✗ ERROR: {message}"]
        for k, v in meta.items():
            lines.append(f"  {k}: {v}")
        self._write(lines)

    def dump(self, label: str, content: str) -> None:
        """记录完整内容块（不截断），用于记录 system prompt / LLM 输入 / LLM 输出"""
        border = "-" * 40
        self._write([
            f"[{self._ts()}] [{self.session_id}] 📄 {label}",
            border,
            content,
            border,
        ])


_loggers: dict[str, SessionLogger] = {}


def get_session_logger(session_id: str) -> SessionLogger:
    """获取或创建会话日志器（单例）"""
    if session_id not in _loggers:
        _loggers[session_id] = SessionLogger(session_id)
    return _loggers[session_id]


