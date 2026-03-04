"""
PPT 动画效果注入模块

通过 OOXML 直接操作实现 PPT 动画效果：
1. 页面切换动画（淡入、滑动、推进等）
2. 元素进入动画（标题飞入、内容逐项显示）

实现原理：
- python-pptx 生成基础 PPTX 文件
- 解压 PPTX（ZIP 格式），修改幻灯片 XML
- 注入 CT_Transition（页面切换）和 CT_Animate（元素动画）定义
- 重新打包为 PPTX
"""

import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
import xml.etree.ElementTree as ET
from xml.dom import minidom
import logging
import os
import re

logger = logging.getLogger(__name__)

# OOXML 命名空间
NS = {
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'ooxml': 'http://schemas.openxmlformats.org/officeDocument/2006/sharedTypes',
}

# 注册命名空间前缀（用于 ET 输出）
ET.register_namespace('a', 'http://schemas.openxmlformats.org/drawingml/2006/main')
ET.register_namespace('p', 'http://schemas.openxmlformats.org/presentationml/2006/main')
ET.register_namespace('r', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships')


class PPTXAnimator:
    """PPTX 动画注入器"""

    # 页面切换效果映射
    TRANSITION_EFFECTS = {
        'fade': 'fade',  # 淡入
        'push': 'push',  # 推进
        'wipe': 'wipe',  # 擦除
        'split': 'split',  # 分割
        'cut': 'cut',  # 切出
        'reveal': 'reveal',  # 显现
        'random': 'randomBar',  # 随机线条
        'bars': 'barnumber',  # 百叶窗
    }

    # 元素进入动画映射
    ENTRY_EFFECTS = {
        'flyIn': 'flyIn',  # 飞入
        'float': 'float',  # 浮入
        'appear': 'appear',  # 出现
        'zoom': 'zoom',  # 缩放
        'bounce': 'bounce',  # 弹跳
        'fadeIn': 'fadeIn',  # 淡入
    }

    def __init__(
        self,
        transition_type: str = 'fade',
        transition_duration: float = 0.5,
        entry_effect: str = 'flyIn',
        entry_duration: float = 0.3
    ):
        """
        初始化动画配置

        Args:
            transition_type: 页面切换类型（fade/push/wipe/split 等）
            transition_duration: 切换持续时间（秒）
            entry_effect: 元素进入动画类型（flyIn/float/appear 等）
            entry_duration: 元素动画持续时间（秒）
        """
        self.transition_type = transition_type
        self.transition_duration = transition_duration
        self.entry_effect = entry_effect
        self.entry_duration = entry_duration

    def add_animations(self, pptx_path: Path, output_path: Optional[Path] = None) -> Path:
        """
        为 PPTX 文件添加动画

        Args:
            pptx_path: 输入 PPTX 文件路径
            output_path: 输出路径（None 则覆盖原文件）

        Returns:
            输出文件路径
        """
        if not pptx_path.exists():
            raise FileNotFoundError(f"PPTX 文件不存在：{pptx_path}")

        output_path = output_path or pptx_path

        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            try:
                # 1. 解压 PPTX
                self._extract_pptx(pptx_path, temp_path)

                # 2. 修改幻灯片 XML 添加动画
                self._inject_animations(temp_path)

                # 3. 重新打包
                self._package_pptx(temp_path, output_path)

                logger.info(f"动画已注入：{output_path}")
                return output_path

            except Exception as e:
                logger.error(f"动画注入失败：{e}")
                raise RuntimeError(f"动画注入失败：{e}") from e

    def _extract_pptx(self, pptx_path: Path, dest_dir: Path):
        """解压 PPTX 文件（ZIP 格式）"""
        with zipfile.ZipFile(pptx_path, 'r') as zip_ref:
            zip_ref.extractall(dest_dir)

    def _package_pptx(self, src_dir: Path, output_path: Path):
        """重新打包为 PPTX 文件"""
        # 确保父目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 创建 ZIP 文件（PPTX 本质是 ZIP）
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
            for file_path in src_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(src_dir)
                    zip_ref.write(file_path, arcname)

    def _inject_animations(self, pptx_dir: Path):
        """
        注入动画到所有幻灯片

        Args:
            pptx_dir: 解压后的 PPTX 目录
        """
        # 找到所有幻灯片文件
        slides_dir = pptx_dir / 'ppt' / 'slides'
        if not slides_dir.exists():
            raise ValueError("无效的 PPTX 结构：找不到 slides 目录")

        # 处理每个幻灯片
        for slide_file in sorted(slides_dir.glob('slide*.xml')):
            logger.debug(f"处理幻灯片：{slide_file.name}")
            self._process_slide(slide_file)

        # 处理 presentation.xml（设置默认切换效果）
        presentation_file = pptx_dir / 'ppt' / 'presentation.xml'
        if presentation_file.exists():
            self._process_presentation(presentation_file)

    def _process_slide(self, slide_file: Path):
        """
        处理单个幻灯片 XML，添加切换和元素动画

        Args:
            slide_file: 幻灯片 XML 文件路径
        """
        try:
            tree = ET.parse(slide_file)
            root = tree.getroot()

            # 1. 添加页面切换效果
            self._add_transition(root)

            # 2. 添加元素动画
            self._add_element_animations(root)

            # 保存修改后的 XML
            self._save_xml(tree, slide_file)

        except ET.ParseError as e:
            logger.warning(f"幻灯片 XML 解析失败 {slide_file.name}: {e}")
        except Exception as e:
            logger.warning(f"处理幻灯片失败 {slide_file.name}: {e}")

    def _add_transition(self, slide_root: ET.Element):
        """
        添加页面切换效果

        Args:
            slide_root: 幻灯片根元素
        """
        # 查找 <p:cSld> 元素
        c_sld = slide_root.find('p:cSld', NS)
        if c_sld is None:
            return

        # 检查是否已有切换效果
        existing_transition = c_sld.find('p:transition', NS)
        if existing_transition is not None:
            # 移除现有切换效果
            c_sld.remove(existing_transition)

        # 创建切换效果元素
        effect_name = self.TRANSITION_EFFECTS.get(
            self.transition_type,
            'fade'
        )

        # <p:transition> 元素
        transition = ET.SubElement(c_sld, '{%s}transition' % NS['p'])

        # 切换效果子元素（如 <p:fade>）
        effect_elem = ET.SubElement(
            transition,
            '{%s}%s' % (NS['p'], effect_name)
        )

        # 持续时间属性（毫秒）
        dur_ms = int(self.transition_duration * 1000)
        transition.set('spd', str(dur_ms))

    def _add_element_animations(self, slide_root: ET.Element):
        """
        添加元素进入动画

        Args:
            slide_root: 幻灯片根元素
        """
        # 查找 <p:cSld> 元素
        c_sld = slide_root.find('p:cSld', NS)
        if c_sld is None:
            return

        # 查找所有形状（文本框、图形等）
        sp_tree = c_sld.find('.//p:spTree', NS)
        if sp_tree is None:
            return

        # 检查是否已有动画时间轴
        existing_timing = c_sld.find('p:timing', NS)
        if existing_timing is not None:
            # 移除现有动画
            c_sld.remove(existing_timing)

        # 创建动画时间轴
        timing = ET.SubElement(c_sld, '{%s}timing' % NS['p'])
        time_node_list = ET.SubElement(timing, '{%s}timeNodeList' % NS['p'])

        # 为每个形状添加动画
        shape_index = 0
        for shape in sp_tree.findall('.//p:sp', NS):
            # 获取形状的 ID
            shape_id = shape.get('id', str(shape_index))

            # 添加动画时间轴节点
            self._add_shape_animation(time_node_list, shape, shape_index)
            shape_index += 1

        # 为图片也添加动画
        pic_index = 0
        for pic in sp_tree.findall('.//p:pic', NS):
            pic_id = pic.get('id', f'pic{pic_index}')
            self._add_pic_animation(time_node_list, pic, pic_index)
            pic_index += 1

    def _add_shape_animation(
        self,
        time_node_list: ET.Element,
        shape: ET.Element,
        shape_index: int
    ):
        """
        为单个形状添加动画时间轴节点

        Args:
            time_node_list: 时间轴节点列表元素
            shape: 形状元素
            shape_index: 形状索引（用于动画顺序）
        """
        # 获取形状 ID
        shape_id = shape.get('id', str(shape_index))

        # 创建并行时间节点（paraTimeNode）
        par_time_node = ET.SubElement(
            time_node_list,
            '{%s}parTimeNode' % NS['p'],
            {
                'id': str(shape_index + 1),
                'presetID': self._get_effect_preset_id(),
                'presetClass': 'entr',  # 进入动画
                'presetSubtype': '0',
                'fill': 'hold',
                'nodeType': 'mainSeq'
            }
        )

        # 持续时间
        dur = ET.SubElement(par_time_node, '{%s}dur' % NS['p'], {
            'val': str(int(self.entry_duration * 1000))
        })

        # 简单时间线
        s_t_m = ET.SubElement(par_time_node, '{%s}stM' % NS['p'], {
            'val': str(shape_index * 500)  # 每个元素间隔 500ms
        })

        # 子时间节点列表
        child_tn_lst = ET.SubElement(par_time_node, '{%s}childTnLst' % NS['p'])

        # 并行子节点（效果本身）
        child_par = ET.SubElement(child_tn_lst, '{%s}parTimeNode', {
            'id': str(shape_index + 100),
            'fill': 'hold'
        })

        ET.SubElement(child_par, '{%s}dur', {'val': str(int(self.entry_duration * 1000))})
        ET.SubElement(child_par, '{%s}stM', {'val': '0'})

        # 效果子节点列表
        child_child_tn_lst = ET.SubElement(child_par, '{%s}childTnLst' % NS['p'])

        # 设置效果类型
        set_tn = ET.SubElement(child_child_tn_lst, '{%s}setTimeNode', {
            'id': str(shape_index + 200)
        })
        ET.SubElement(set_tn, '{%s}dur', {'val': '1'})

        # 动画值列表
        anim_val_lst = ET.SubElement(set_tn, '{%s}animValLst' % NS['p'])

        # 动画值 - 属性类型
        anim_val = ET.SubElement(anim_val_lst, '{%s}animVal', {
            'attrName': 'style',
            'attrName2': 'p'
        })

        # 动画值数据
        val_data = ET.SubElement(anim_val, '{%s}valData', {
            'valType': 'str'
        })

        # 设置动画值（简化为出现效果）
        ET.SubElement(val_data, '{%s}strVal', {'val': 'visible'})

    def _add_pic_animation(
        self,
        time_node_list: ET.Element,
        pic: ET.Element,
        pic_index: int
    ):
        """
        为图片添加动画

        Args:
            time_node_list: 时间轴节点列表元素
            pic: 图片元素
            pic_index: 图片索引
        """
        # 图片动画类似形状动画
        self._add_shape_animation(time_node_list, pic, pic_index + 1000)

    def _get_effect_preset_id(self) -> str:
        """获取动画效果预设 ID"""
        # 常见进入动画的 presetID
        preset_ids = {
            'flyIn': '2',
            'float': '3',
            'appear': '1',
            'zoom': '5',
            'bounce': '8',
            'fadeIn': '4',
        }
        return preset_ids.get(self.entry_effect, '2')

    def _process_presentation(self, presentation_file: Path):
        """
        处理 presentation.xml，设置默认切换

        Args:
            presentation_file: presentation.xml 文件路径
        """
        try:
            tree = ET.parse(presentation_file)
            root = tree.getroot()

            # 可以在这里设置全局默认切换效果
            # 但通常每个幻灯片有自己的切换设置

            self._save_xml(tree, presentation_file)

        except Exception as e:
            logger.warning(f"处理 presentation.xml 失败：{e}")

    def _save_xml(self, tree: ET.ElementTree, file_path: Path):
        """
        保存 XML 文件（带格式）

        Args:
            tree: ElementTree 对象
            file_path: 输出文件路径
        """
        # 获取 XML 字符串
        xml_str = ET.tostring(
            tree.getroot(),
            encoding='unicode',
            xml_declaration=True
        )

        # 美化 XML（可选）
        try:
            parsed = minidom.parseString(xml_str)
            pretty_xml = parsed.toprettyxml(indent='  ', encoding=None)
            # 移除多余的空行
            pretty_xml = '\n'.join(
                line for line in pretty_xml.split('\n')
                if line.strip()
            )
        except Exception:
            pretty_xml = xml_str

        # 写入文件
        file_path.write_text(pretty_xml, encoding='utf-8')


class AnimationPreset:
    """动画预设配置"""

    @staticmethod
    def elementary_school() -> Dict[str, Any]:
        """小学风格动画（活泼、明显）"""
        return {
            'transition': 'push',
            'transition_duration': 0.6,
            'entry_effect': 'bounce',
            'entry_duration': 0.4,
        }

    @staticmethod
    def middle_school() -> Dict[str, Any]:
        """初中风格动画（简洁、专业）"""
        return {
            'transition': 'fade',
            'transition_duration': 0.4,
            'entry_effect': 'fadeIn',
            'entry_duration': 0.3,
        }

    @staticmethod
    def high_school() -> Dict[str, Any]:
        """高中风格动画（克制、专业、无多余装饰）"""
        return {
            'transition': 'cut',
            'transition_duration': 0.2,
            'entry_effect': 'appear',
            'entry_duration': 0.15,
        }

    @staticmethod
    def none() -> Dict[str, Any]:
        """无动画"""
        return {
            'transition': 'cut',
            'transition_duration': 0,
            'entry_effect': 'appear',
            'entry_duration': 0,
        }


def add_animation_to_ppt(
    pptx_path: str,
    output_path: Optional[str] = None,
    grade: str = '6',
    subject: str = 'general'
) -> str:
    """
    便捷函数：为 PPT 添加动画

    Args:
        pptx_path: 输入 PPTX 路径
        output_path: 输出路径
        grade: 年级（用于选择动画风格）
        subject: 学科

    Returns:
        输出文件路径
    """
    from .ppt_generator import PPTStyle

    # 根据年级获取动画建议
    style = PPTStyle.get_style(grade)
    animation_suggestion = style.get('animation_suggestion', '')

    # 选择动画预设
    grade_group = style.get('group', 'elementary_high')

    if grade_group == 'elementary_low':
        preset = AnimationPreset.elementary_school()
    elif grade_group == 'middle':
        preset = AnimationPreset.middle_school()
    elif grade_group == 'high_school':
        preset = AnimationPreset.high_school()
    else:
        preset = AnimationPreset.elementary_school()

    # 创建动画器
    animator = PPTXAnimator(
        transition_type=preset['transition'],
        transition_duration=preset['transition_duration'],
        entry_effect=preset['entry_effect'],
        entry_duration=preset['entry_duration']
    )

    # 添加动画
    result = animator.add_animations(
        Path(pptx_path),
        Path(output_path) if output_path else None
    )

    return str(result)
