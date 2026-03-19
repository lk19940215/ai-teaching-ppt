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
import fitz  # PyMuPDF

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

            logger.info(f"开始转换：{pptx_path.name} ({total_slides} 页) -> {self.output_dir}")

            # 直接使用 output_dir 作为输出目录
            session_dir = self.output_dir
            session_dir.mkdir(parents=True, exist_ok=True)

            # 获取 session_id（从 output_dir 名称推断）
            session_id = self.output_dir.name

            base_name = pptx_path.stem
            images = []

            # 方案：PPTX → PDF → PNG（支持多页）
            # 步骤1：用 LibreOffice 转 PDF
            total_timeout = min(total_slides * self.timeout_per_page, self.MAX_TIMEOUT)

            # 创建临时目录存放 PDF
            temp_pdf_dir = session_dir / "temp_pdf"
            temp_pdf_dir.mkdir(exist_ok=True)

            pdf_cmd = [
                self.soffice_path,
                "--headless",
                "--convert-to", "pdf",
                "--outdir", str(temp_pdf_dir.absolute()),
                str(pptx_path.absolute())
            ]

            logger.info(f"执行 LibreOffice PDF 转换：{' '.join(pdf_cmd)}")

            pdf_result = subprocess.run(
                pdf_cmd,
                capture_output=True,
                text=True,
                timeout=total_timeout,
                cwd=str(session_dir.absolute())
            )

            logger.info(f"LibreOffice PDF 返回码：{pdf_result.returncode}")

            if pdf_result.returncode != 0:
                logger.error(f"LibreOffice PDF 转换失败：{pdf_result.stderr}")
                # 清理临时目录
                shutil.rmtree(temp_pdf_dir, ignore_errors=True)
                return ConversionResult(
                    success=False,
                    images=[],
                    error=f"LibreOffice PDF 转换失败：{pdf_result.stderr}"
                )

            # 查找生成的 PDF
            pdf_files = list(temp_pdf_dir.glob("*.pdf"))
            if not pdf_files:
                logger.error("未找到生成的 PDF 文件")
                shutil.rmtree(temp_pdf_dir, ignore_errors=True)
                return ConversionResult(
                    success=False,
                    images=[],
                    error="未找到生成的 PDF 文件"
                )

            pdf_path = pdf_files[0]

            # 步骤2：用 PyMuPDF 将 PDF 转换为 PNG
            logger.info(f"使用 PyMuPDF 转换 PDF → PNG：{pdf_path}")

            try:
                doc = fitz.open(str(pdf_path))
                total_pages = len(doc)

                for page_idx in range(total_pages):
                    # 如果指定了页码，只处理指定的页
                    if pages is not None and page_idx not in pages:
                        continue

                    page = doc[page_idx]
                    # 根据分辨率设置渲染 DPI
                    dpi = self.RESOLUTION_DPI.get(self.resolution, 150)
                    mat = fitz.Matrix(dpi / 72, dpi / 72)
                    pix = page.get_pixmap(matrix=mat)

                    # 保存 PNG
                    final_name = f"{base_name}_page_{page_idx}.png"
                    final_path = session_dir / final_name
                    pix.save(str(final_path))

                    images.append({
                        "page": page_idx,
                        "url": f"http://localhost:8000/public/versions/{session_id}/{final_name}",
                        "path": str(final_path),
                        "width": pix.width,
                        "height": pix.height
                    })

                    logger.debug(f"转换第 {page_idx + 1}/{total_pages} 页完成")

                doc.close()
                logger.info(f"PyMuPDF 转换完成：生成 {len(images)} 张图片")

            except Exception as e:
                logger.error(f"PyMuPDF 转换失败：{e}")
                shutil.rmtree(temp_pdf_dir, ignore_errors=True)
                return ConversionResult(
                    success=False,
                    images=[],
                    error=f"PDF 转 PNG 失败：{str(e)}"
                )

            # 清理临时目录
            shutil.rmtree(temp_pdf_dir, ignore_errors=True)

            logger.info(f"转换成功：生成 {len(images)} 张图片")
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
                "url": f"http://localhost:8000/public/versions/{session_dir.name}/{png_file.name}",
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


def convert_single_slide_to_image(
    pptx_path: Path,
    output_dir: Path,
    page_index: int = 0,
    resolution: str = "high"
) -> Dict[str, Any]:
    """
    单页 PPT 转图片便捷函数

    封装 PptToImageConverter 调用，返回标准格式。
    支持 LibreOffice 未安装时的降级处理。

    Args:
        pptx_path: PPTX 文件路径
        output_dir: 输出目录
        page_index: 页码（0-indexed），默认 0
        resolution: 分辨率 (high/medium/low)，默认 high

    Returns:
        {
            success: bool,
            url: str | None,      # 图片 URL（如 http://localhost:8000/public/images/xxx.png）
            path: str | None,     # 图片本地路径
            width: int | None,    # 图片宽度
            height: int | None,   # 图片高度
            error: str | None,    # 错误信息
            degraded: bool        # 是否降级（LibreOffice 未安装）
        }
    """
    # 检查 LibreOffice 是否安装
    if not LibreOfficeDetector.is_installed():
        logger.warning("LibreOffice 未安装，单页转换降级")
        return {
            "success": False,
            "url": None,
            "path": None,
            "width": None,
            "height": None,
            "error": f"LibreOffice 未安装，无法生成预览图。\n{LibreOfficeDetector.get_install_guide()}",
            "degraded": True
        }

    # 检查文件是否存在
    if not pptx_path.exists():
        logger.error(f"PPTX 文件不存在：{pptx_path}")
        return {
            "success": False,
            "url": None,
            "path": None,
            "width": None,
            "height": None,
            "error": f"PPTX 文件不存在：{pptx_path}",
            "degraded": False
        }

    try:
        # 解析分辨率参数
        res = Resolution(resolution.lower())

        # 创建转换器并执行转换
        converter = PptToImageConverter(output_dir, res)
        result = converter.convert_single_page(pptx_path, page_index)

        if not result.success:
            return {
                "success": False,
                "url": None,
                "path": None,
                "width": None,
                "height": None,
                "error": result.error,
                "degraded": False
            }

        # 提取单页结果
        if not result.images:
            return {
                "success": False,
                "url": None,
                "path": None,
                "width": None,
                "height": None,
                "error": "转换成功但未生成图片",
                "degraded": False
            }

        image_info = result.images[0]

        # 构建标准返回格式
        # 图片 URL 格式：http://localhost:8000/public/images/{session_id}/{filename}
        # 如果 output_dir 路径中包含 session_id，使用它构建 URL
        session_id = output_dir.name
        image_filename = Path(image_info["path"]).name

        # 检查 URL 是否已经是完整格式
        if image_info.get("url"):
            image_url = image_info["url"]
        else:
            # 使用 images 路径格式
            image_url = f"http://localhost:8000/public/images/{session_id}/{image_filename}"

        return {
            "success": True,
            "url": image_url,
            "path": image_info.get("path"),
            "width": image_info.get("width"),
            "height": image_info.get("height"),
            "error": None,
            "degraded": False
        }

    except ValueError as e:
        # 分辨率参数错误
        logger.error(f"无效的分辨率参数：{resolution}，错误：{e}")
        return {
            "success": False,
            "url": None,
            "path": None,
            "width": None,
            "height": None,
            "error": f"无效的分辨率参数：{resolution}，支持值：high/medium/low",
            "degraded": False
        }
    except Exception as e:
        logger.exception(f"单页转换异常：{e}")
        return {
            "success": False,
            "url": None,
            "path": None,
            "width": None,
            "height": None,
            "error": f"转换异常：{str(e)}",
            "degraded": False
        }
