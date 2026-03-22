"""
动画应用器 — 将 AI 返回的 AnimationHint 应用到 PPTX Slide

当前状态：桩实现（Stub）
python-pptx 不原生支持动画操作，需要直接操作 OOXML XML。
此模块预留了完整接口，后续可通过以下方式扩展：
  1. 直接操作 lxml 元素树（<p:timing>, <p:anim>）
  2. 集成 Aspose.Slides for Python（付费库，功能完整）
  3. 使用模板滑页中已有的动画作为 "动画模板" 复用

设计原则：
  - 可插拔：pptx_writer.py 通过 AnimationApplicator 调用
  - 失败安全：不支持的效果仅记录日志，不影响其他处理
  - 渐进增强：随着实现完善，无需修改调用方代码
"""

import logging
from typing import Optional

from lxml import etree
from pptx.oxml.ns import qn

from .models import AnimationHint

logger = logging.getLogger(__name__)

EFFECT_PRESET_MAP = {
    "appear": 1,
    "fade": 10,
    "fly_in": 2,
    "zoom": 53,
    "wipe": 22,
}

TRIGGER_MAP = {
    "on_click": "onClick",
    "with_previous": "withPrev",
    "after_previous": "afterPrev",
}


class AnimationApplicator:
    """
    将 AnimationHint 应用到 PPTX Slide。

    当前为桩实现，仅记录日志。
    取消注释 _apply_entrance_animation 中的 XML 操作代码即可启用基础动画。
    """

    def __init__(self, enabled: bool = False):
        """
        Args:
            enabled: 是否启用实际的动画应用。
                     False = 仅记录日志（安全模式）
                     True  = 尝试操作 OOXML XML
        """
        self.enabled = enabled

    def apply(self, slide, shapes: list, hints: list[AnimationHint]) -> int:
        """
        将动画提示应用到幻灯片。

        Args:
            slide:  python-pptx Slide 对象
            shapes: slide.shapes 的列表
            hints:  AI 返回的动画提示列表

        Returns:
            实际应用的动画数量
        """
        if not hints:
            return 0

        applied = 0
        for hint in hints:
            if hint.shape_index >= len(shapes):
                logger.warning(
                    f"AnimationHint shape_index {hint.shape_index} "
                    f"超出范围 (共 {len(shapes)} 个 shape)"
                )
                continue

            if not self.enabled:
                logger.info(
                    f"动画提示 [未启用]: shape_{hint.shape_index} "
                    f"effect={hint.effect} trigger={hint.trigger}"
                )
                continue

            shape = shapes[hint.shape_index]
            success = self._apply_entrance_animation(slide, shape, hint)
            if success:
                applied += 1

        return applied

    def _get_shape_id(self, shape) -> str:
        """从 shape 元素获取数值 ID"""
        shape_el = shape._element
        cNvPr = shape_el.find(".//" + qn("p:cNvPr"))
        if cNvPr is not None:
            return cNvPr.attrib.get("id", "1")
        nvSpPr = shape_el.find(qn("p:nvSpPr"))
        if nvSpPr is not None:
            inner = nvSpPr.find(qn("p:cNvPr"))
            if inner is not None:
                return inner.attrib.get("id", "1")
        return "1"

    def _remove_existing_animations_for_shape(self, slide_el, sp_id: str):
        """移除 slide 中已有的针对该 shape 的动画，避免重复"""
        ns = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main"}
        for spTgt in slide_el.findall(".//p:spTgt", ns):
            if spTgt.attrib.get("spid") == sp_id:
                par_node = spTgt
                while par_node is not None:
                    parent = par_node.getparent()
                    if parent is not None and parent.tag == qn("p:childTnLst"):
                        parent.remove(par_node)
                        break
                    par_node = parent

    def _apply_entrance_animation(
        self, slide, shape, hint: AnimationHint
    ) -> bool:
        """
        通过 OOXML XML 操作添加入场动画。
        包含目标元素引用 (<p:tgtEl>) 和去重机制。
        """
        preset_id = EFFECT_PRESET_MAP.get(hint.effect)
        if preset_id is None:
            logger.warning(f"不支持的动画效果: {hint.effect}")
            return False

        trigger = TRIGGER_MAP.get(hint.trigger, "onClick")
        duration = hint.duration_ms or 500

        try:
            sp_id = self._get_shape_id(shape)
            spTree = slide.shapes._spTree
            slide_el = spTree.getparent()

            self._remove_existing_animations_for_shape(slide_el, sp_id)

            timing = slide_el.find(qn("p:timing"))
            if timing is None:
                timing = etree.SubElement(slide_el, qn("p:timing"))

            tn_lst = timing.find(qn("p:tnLst"))
            if tn_lst is None:
                tn_lst = etree.SubElement(timing, qn("p:tnLst"))

            par_tn = tn_lst.find(qn("p:par"))
            if par_tn is None:
                par_tn = etree.SubElement(tn_lst, qn("p:par"))
                c_tn_root = etree.SubElement(par_tn, qn("p:cTn"), attrib={
                    "id": "1", "dur": "indefinite",
                    "restart": "never", "nodeType": "tmRoot",
                })
                child_tn_lst = etree.SubElement(c_tn_root, qn("p:childTnLst"))
            else:
                c_tn_root = par_tn.find(qn("p:cTn"))
                child_tn_lst = c_tn_root.find(qn("p:childTnLst"))
                if child_tn_lst is None:
                    child_tn_lst = etree.SubElement(c_tn_root, qn("p:childTnLst"))

            seq = child_tn_lst.find(qn("p:seq"))
            if seq is None:
                seq = etree.SubElement(child_tn_lst, qn("p:seq"), attrib={
                    "concurrent": "1", "nextAc": "seek",
                })
                seq_cTn = etree.SubElement(seq, qn("p:cTn"), attrib={
                    "id": "2", "dur": "indefinite", "nodeType": "mainSeq",
                })
                seq_child = etree.SubElement(seq_cTn, qn("p:childTnLst"))
            else:
                seq_cTn = seq.find(qn("p:cTn"))
                seq_child = seq_cTn.find(qn("p:childTnLst"))
                if seq_child is None:
                    seq_child = etree.SubElement(seq_cTn, qn("p:childTnLst"))

            existing_ids = set()
            for el in slide_el.iter():
                ctn_id = el.attrib.get("id")
                if ctn_id and ctn_id.isdigit():
                    existing_ids.add(int(ctn_id))
            next_id = max(existing_ids, default=2) + 1

            click_par = etree.SubElement(seq_child, qn("p:par"))
            click_cTn = etree.SubElement(click_par, qn("p:cTn"), attrib={
                "id": str(next_id), "fill": "hold",
            })
            stCondLst = etree.SubElement(click_cTn, qn("p:stCondLst"))
            etree.SubElement(stCondLst, qn("p:cond"), attrib={"delay": "0"})
            inner_child = etree.SubElement(click_cTn, qn("p:childTnLst"))

            anim_par = etree.SubElement(inner_child, qn("p:par"))
            anim_cTn = etree.SubElement(anim_par, qn("p:cTn"), attrib={
                "id": str(next_id + 1),
                "presetID": str(preset_id),
                "presetClass": "entr",
                "presetSubtype": "0",
                "fill": "hold",
                "dur": str(duration),
                "nodeType": "clickEffect" if trigger == "onClick" else "afterEffect",
            })

            anim_stCond = etree.SubElement(anim_cTn, qn("p:stCondLst"))
            etree.SubElement(anim_stCond, qn("p:cond"), attrib={"delay": "0"})
            anim_child = etree.SubElement(anim_cTn, qn("p:childTnLst"))

            anim_effect = etree.SubElement(anim_child, qn("p:set"))
            set_cBhvr = etree.SubElement(anim_effect, qn("p:cBhvr"))
            set_cTn = etree.SubElement(set_cBhvr, qn("p:cTn"), attrib={
                "id": str(next_id + 2), "dur": "1", "fill": "hold",
            })
            etree.SubElement(set_cTn, qn("p:stCondLst")).append(
                etree.Element(qn("p:cond"), attrib={"delay": "0"})
            )
            tgtEl = etree.SubElement(set_cBhvr, qn("p:tgtEl"))
            etree.SubElement(tgtEl, qn("p:spTgt"), attrib={"spid": sp_id})
            attrNameLst = etree.SubElement(set_cBhvr, qn("p:attrNameLst"))
            etree.SubElement(attrNameLst, qn("p:attrName")).text = "style.visibility"
            to_el = etree.SubElement(anim_effect, qn("p:to"))
            val_el = etree.SubElement(to_el, qn("p:strVal"), attrib={"val": "visible"})

            logger.info(
                f"动画已应用: shape_{hint.shape_index} (spid={sp_id}) "
                f"effect={hint.effect}(preset={preset_id}) "
                f"trigger={trigger} duration={duration}ms"
            )
            return True

        except Exception as e:
            logger.error(f"动画应用失败: {e}", exc_info=True)
            return False
