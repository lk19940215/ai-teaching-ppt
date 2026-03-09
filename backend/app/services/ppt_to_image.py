# -*- coding: utf-8 -*-
"""
PPT 转图片服务
使用 LibreOffice headless 模式将 PPTX 每页转换为 PNG 图片

设计文档：.claude-coder/plans/ppt-merge-technical-design.md#5-版本化管理设计
"""

import os
import uuid
import logging
import subprocess
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class Resolution(Enum):
    """图片分辨率"""
    HIGH = "high"      # 1920x1080
    MEDIUM = "medium"  # 1280x720
    LOW = "low"        # 640x360


@dataclass
class ConversionResult:
    """转换结果"""
    success: bool
    images: List[Dict[str, Any]]  # [{page, url, width, height}]
    error: Optional[str] = None


class LibreOfficeDetector:
    """LibreOffice 安装检测器"""

    # Windows 常见安装路径
    WINDOWS_PATHS = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]

    # Linux 常见安装路径
    LINUX_PATHS = [
        "/usr/bin/libreoffice",
        "/usr/bin/soffice",
        "/snap/bin/libreoffice",
    ]

    # macOS 常见安装路径
    MACOS_PATHS = [
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    ]

    @classmethod
    def find_soffice(cls) -> Optional[str]:
        """
        查找 LibreOffice soffice 可执行文件
        Returns:
            可执行文件路径，未找到返回 None
        """
        # 1. 检查环境变量
        soffice = shutil.which("soffice") or shutil.which("libreoffice")
        if soffice:
            return soffice

        # 2. 根据平台检查常见路径
        import platform
        system = platform.system()

        if system == "Windows":
            paths = cls.WINDOWS_PATHS
        elif system == "Linux":
            paths = cls.LINUX_PATHS
        elif system == "Darwin":
            paths = cls.MACOS_PATHS
        else:
            paths = []

        for path in paths:
            if os.path.isfile(path):
                logger.info(f"找到 LibreOffice: {path}")
                return path

        # 3. Windows 注册表检测
        if system == "Windows":
            try:
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\LibreOffice\LibreOffice"
                )
                install_path = winreg.QueryValueEx(key, "InstallPath")[0]
                soffice_path = os.path.join(install_path, "program", "soffice.exe")
                if os.path.isfile(soffice_path):
                    logger.info(f"从注册表找到 LibreOffice: {soffice_path}")
                    return soffice_path
            except Exception as e:
                logger.debug(f"注册表检测失败：{e}")

        logger.warning("未找到 LibreOffice 安装")
        return None

    @classmethod
    def is_installed(cls) -> bool:
        """检查 LibreOffice 是否已安装"""
        return cls.find_soffice() is not None

    @classmethod
    def get_install_guide(cls) -> str:
        """获取安装指引"""
        import platform
        system = platform.system()

        if system == "Windows":
            return (
                "请安装 LibreOffice:\n"
                "1. 访问 https://www.libreoffice.org/download/download/\n"
                "2. 下载 Windows 版本安装包\n"
                "3. 运行安装程序，默认安装即可\n"
                "4. 重启后端服务"
            )
        elif system == "Linux":
            return (
                "请安装 LibreOffice:\n"
                "Ubuntu/Debian: sudo apt install libreoffice\n"
                "CentOS/RHEL: sudo yum install libreoffice\n"
                "Arch: sudo pacman -S libreoffice"
            )
        elif system == "Darwin":
            return (
                "请安装 LibreOffice:\n"
                "brew install --cask libreoffice\n"
                "或访问 https://www.libreoffice.org/download/download/"
            )
        else:
            return "请访问 https://www.libreoffice.org/download/download/ 安装 LibreOffice"


class PptToImageConverter:
    """PPT 转图片转换器"""

    # 超时设置（秒）
    DEFAULT_TIMEOUT = 30  # 每页默认超时
    MAX_TIMEOUT = 300     # 最大总超时

    # 分辨率 DPI 映射
    RESOLUTION_DPI = {
        Resolution.HIGH: 150,
        Resolution.MEDIUM: 100,
        Resolution.LOW: 50,
    }

    def __init__(
        self,
        output_dir: Path,
        resolution: Resolution = Resolution.HIGH,
        timeout_per_page: int = 30
    ):
        """
        初始化转换器

        Args:
            output_dir: 输出目录
            resolution: 图片分辨率
            timeout_per_page: 每页超时时间（秒）
        """
        self.output_dir = Path(output_dir)
        self.resolution = resolution
        self.timeout_per_page = timeout_per_page

        # 检测 LibreOffice
        self.soffice_path = LibreOfficeDetector.find_soffice()

    def convert(
        self,
        pptx_path: Path,
        pages: Optional[List[int]] = None
    ) -> ConversionResult:
        """
        将 PPTX 转换为 PNG 图片
        使用 python-pptx 逐页提取并转换为图片

        Args:
            pptx_path: PPTX 文件路径
            pages: 指定页码（可选，默认全部）

        Returns:
            ConversionResult 转换结果
        """
        if not self.soffice_path:
            return ConversionResult(
                success=False,
                images=[],
                error=f"LibreOffice 未安装。\n{LibreOfficeDetector.get_install_guide()}"
            )

        if not pptx_path.exists():
            return ConversionResult(
                success=False,
                images=[],
                error=f"文件不存在：{pptx_path}"
            )

        try:
            # 先用 python-pptx 获取总页数
            from pptx import Presentation
            prs = Presentation(pptx_path)
            total_slides = len(prs.slides)

            # 确定要转换的页码
            if pages is not None:
                slide_indices = [i for i in pages if i < total_slides]
            else:
                slide_indices = list(range(total_slides))

            logger.info(f"开始转换：{pptx_path.name} ({len(slide_indices)} 页) -> {self.output_dir}")

            # 创建输出目录
            session_id = str(uuid.uuid4())[:8]
            session_dir = self.output_dir / session_id
            session_dir.mkdir(parents=True, exist_ok=True)

            # 逐页转换
            images = []
            base_name = pptx_path.stem

            for slide_idx in slide_indices:
                try:
                    # 创建临时单页 PPTX
                    temp_pptx = session_dir / f"temp_slide_{slide_idx}.pptx"
                    self._create_single_slide_pptx(prs, slide_idx, temp_pptx)

                    # 转换单页
                    cmd = [
                        self.soffice_path,
                        "--headless",
                        "--convert-to", "png",
                        "--outdir", str(session_dir),
                        str(temp_pptx)
                    ]

                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=self.timeout_per_page,
                        cwd=str(session_dir)
                    )

                    # 清理临时 PPTX
                    try:
                        temp_pptx.unlink()
                    except Exception:
                        pass

                    if result.returncode != 0:
                        logger.warning(f"第 {slide_idx} 页转换失败：{result.stderr}")
                        continue

                    # 找到生成的 PNG 文件（LibreOffice 会添加随机后缀）
                    png_pattern = f"temp_slide_{slide_idx}*.png"
                    png_files = list(session_dir.glob(png_pattern))
                    if not png_files:
                        logger.warning(f"第 {slide_idx} 页未找到生成的 PNG 文件")
                        continue

                    png_file = png_files[0]
                    # 重命名为最终文件名
                    final_name = f"{base_name}_page_{slide_idx}.png"
                    final_path = session_dir / final_name
                    png_file.rename(final_path)

                    images.append({
                        "page": slide_idx,
                        "url": f"/static/versions/{session_id}/{final_name}",
                        "path": str(final_path),
                        "width": 1920,
                        "height": 1080
                    })

                except subprocess.TimeoutExpired:
                    logger.warning(f"第 {slide_idx} 页转换超时")
                    continue
                except Exception as e:
                    logger.warning(f"第 {slide_idx} 页转换异常：{e}")
                    continue

            logger.info(f"转换成功：生成 {len(images)}/{len(slide_indices)} 张图片")
            return ConversionResult(
                success=True,
                images=images
            )

        except Exception as e:
            logger.exception(f"转换异常：{e}")
            return ConversionResult(
                success=False,
                images=[],
                error=f"转换异常：{str(e)}"
            )

    def _create_single_slide_pptx(
        self,
        source_prs: "Presentation",
        slide_idx: int,
        output_path: Path
    ) -> None:
        """
        从源 PPTX 提取单页创建新的 PPTX 文件
        使用简化的方法 - 只复制 slide 的 XML

        Args:
            source_prs: 源 PPTX 对象
            slide_idx: 要提取的页码（0-indexed）
            output_path: 输出路径
        """
        from pptx import Presentation
        from pptx.oxml import parse_xml

        # 创建新的 PPTX
        new_prs = Presentation()

        # 获取源幻灯片
        source_slide = source_prs.slides[slide_idx]

        # 删除默认的空白幻灯片（如果有）
        if len(new_prs.slides) > 0:
            new_prs.slides._sldIdLst.remove(new_prs.slides._sldIdLst[0])

        # 复制源幻灯片的 XML
        source_xml = source_slide._element.xml
        new_slide_element = parse_xml(source_xml.encode('utf-8'))

        # 添加到新 PPTX
        new_prs.slides._sldIdLst.append(new_slide_element)

        # 保存
        new_prs.save(str(output_path))

    def _collect_images(
        self,
        session_dir: Path,
        pages: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """收集生成的图片（备用方法：当直接转换多页 PPT 时）"""
        images = []

        # LibreOffice 输出格式：filename.png, filename_2.png, filename_3.png, ...
        png_files = sorted(session_dir.glob("*.png"))

        for idx, png_file in enumerate(png_files):
            page_num = idx  # 0-indexed

            # 如果指定了页码，只返回指定的页
            if pages is not None and page_num not in pages:
                continue

            images.append({
                "page": page_num,
                "url": f"/static/versions/{session_dir.name}/{png_file.name}",
                "path": str(png_file),
                "width": 1920,  # LibreOffice 默认输出宽度
                "height": 1080
            })

        return images

    def convert_single_page(
        self,
        pptx_path: Path,
        page_index: int
    ) -> ConversionResult:
        """
        转换单页

        Args:
            pptx_path: PPTX 文件路径
            page_index: 页码（0-indexed）

        Returns:
            ConversionResult 转换结果
        """
        return self.convert(pptx_path, pages=[page_index])


# 便捷函数
def convert_pptx_to_images(
    pptx_path: Path,
    output_dir: Path,
    resolution: str = "high",
    pages: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    将 PPTX 转换为图片（便捷函数）

    Args:
        pptx_path: PPTX 文件路径
        output_dir: 输出目录
        resolution: 分辨率 (high/medium/low)
        pages: 指定页码（可选）

    Returns:
        转换结果字典
    """
    res = Resolution(resolution.lower())
    converter = PptToImageConverter(output_dir, res)
    result = converter.convert(pptx_path, pages)
    return {
        "success": result.success,
        "images": result.images,
        "error": result.error
    }


def check_libreoffice() -> Dict[str, Any]:
    """
    检查 LibreOffice 安装状态

    Returns:
        {installed: bool, path: str|null, guide: str}
    """
    path = LibreOfficeDetector.find_soffice()
    return {
        "installed": path is not None,
        "path": path,
        "guide": LibreOfficeDetector.get_install_guide() if not path else None
    }
