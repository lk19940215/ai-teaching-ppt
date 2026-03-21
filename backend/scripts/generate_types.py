#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从 Pydantic 模型生成 TypeScript 类型定义

feat-245: 前后端类型定义自动同步

使用方法：
    cd backend
    python scripts/generate_types.py

输出：
    frontend/src/types/generated.ts
"""

import sys
from pathlib import Path
from typing import get_origin, get_args, Union, List, Dict, Optional, Any
from enum import Enum

# 添加项目根目录到路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from pydantic import BaseModel
from pydantic.fields import FieldInfo

# 导入需要导出的模型
from app.models.ppt_structure import (
    Position,
    Style,
    Paragraph,
    ElementData,
    TeachingContent,
    SlideData,
    DocumentData,
    SlideVersion,
    SlideState,
    DocumentState,
    SessionData,
    ElementType,
    SlideType,
    TeachingRole,
    SlideStatus,
)


# TypeScript 类型映射
PYTHON_TO_TS = {
    'str': 'string',
    'int': 'number',
    'float': 'number',
    'bool': 'boolean',
    'Any': 'any',
    'Dict': 'Record<string, any>',
    'List': 'Array',
}


def python_type_to_ts(annotation, field_name: str = '') -> str:
    """将 Python 类型注解转换为 TypeScript 类型"""
    origin = get_origin(annotation)

    # 处理 Optional
    if origin is Union:
        args = get_args(annotation)
        # Optional[X] 实际上是 Union[X, None]
        if len(args) == 2 and type(None) in args:
            inner_type = [a for a in args if a is not type(None)][0]
            return python_type_to_ts(inner_type, field_name) + ' | null'
        else:
            return ' | '.join(python_type_to_ts(a, field_name) for a in args)

    # 处理 List
    if origin is list:
        args = get_args(annotation)
        if args:
            inner_type = python_type_to_ts(args[0], field_name)
            return f'Array<{inner_type}>'
        return 'Array<any>'

    # 处理 Dict
    if origin is dict:
        args = get_args(annotation)
        if len(args) == 2:
            key_type = python_type_to_ts(args[0], field_name)
            value_type = python_type_to_ts(args[1], field_name)
            return f'Record<{key_type}, {value_type}>'
        return 'Record<string, any>'

    # 处理 Enum
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        # 枚举类型：生成联合类型
        values = [f"'{v.value}'" for v in annotation]
        return ' | '.join(values)

    # 处理 BaseModel 子类
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return annotation.__name__

    # 基本类型
    type_name = getattr(annotation, '__name__', str(annotation))
    if type_name in PYTHON_TO_TS:
        return PYTHON_TO_TS[type_name]

    # 处理嵌套的类型引用
    if hasattr(annotation, '_name'):
        return annotation._name or 'any'

    return 'any'


def get_field_type(field: FieldInfo, field_name: str) -> str:
    """获取字段的 TypeScript 类型"""
    annotation = field.annotation
    if annotation is None:
        return 'any'
    return python_type_to_ts(annotation, field_name)


def generate_ts_interface(model: type[BaseModel], indent: int = 0) -> str:
    """生成 TypeScript 接口定义"""
    lines = []
    indent_str = '  ' * indent
    model_name = model.__name__

    # 获取字段信息
    fields = model.model_fields

    # 接口开始
    lines.append(f'{indent_str}export interface {model_name} {{')

    for field_name, field_info in fields.items():
        ts_type = get_field_type(field_info, field_name)
        is_required = field_info.is_required()

        # 检查是否有默认值
        if not is_required:
            field_name_ts = f'{field_name}?'
        else:
            field_name_ts = field_name

        # 添加注释
        description = field_info.description
        if description:
            lines.append(f'{indent_str}  /** {description} */')

        lines.append(f'{indent_str}  {field_name_ts}: {ts_type}')

    # 接口结束
    lines.append(f'{indent_str}}}')

    return '\n'.join(lines)


def generate_ts_enum(enum_class: type[Enum]) -> str:
    """生成 TypeScript 枚举类型（联合类型）"""
    values = [f"'{v.value}'" for v in enum_class]
    enum_name = enum_class.__name__

    lines = [
        f'/** {enum_class.__doc__ or enum_name} */',
        f"export type {enum_name} = {' | '.join(values)};",
    ]
    return '\n'.join(lines)


def generate_types_file(output_path: Path) -> None:
    """生成 TypeScript 类型定义文件"""

    # 要导出的模型列表（按依赖顺序）
    models = [
        # 枚举类型
        ElementType,
        SlideType,
        TeachingRole,
        SlideStatus,
        # 基础模型
        Position,
        Style,
        Paragraph,
        ElementData,
        TeachingContent,
        SlideData,
        DocumentData,
        # 版本管理模型
        SlideVersion,
        SlideState,
        DocumentState,
        SessionData,
    ]

    lines = [
        '/**',
        ' * 自动生成的 TypeScript 类型定义',
        ' * feat-245: 从 Python Pydantic 模型生成',
        ' * ',
        ' * 警告：此文件由脚本自动生成，请勿手动修改！',
        ' * 生成命令：cd backend && python scripts/generate_types.py',
        ' */',
        '',
    ]

    # 生成枚举类型
    enums = [ElementType, SlideType, TeachingRole, SlideStatus]
    lines.append('// ==================== 枚举类型 ====================')
    lines.append('')
    for enum_class in enums:
        lines.append(generate_ts_enum(enum_class))
        lines.append('')

    # 生成接口
    lines.append('// ==================== 数据模型 ====================')
    lines.append('')

    base_models = [Position, Style, Paragraph, ElementData, TeachingContent,
                   SlideData, DocumentData, SlideVersion, SlideState,
                   DocumentState, SessionData]

    for model in base_models:
        lines.append(generate_ts_interface(model))
        lines.append('')

    # 写入文件
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text('\n'.join(lines), encoding='utf-8')
    print(f'TypeScript types generated: {output_path}')


if __name__ == '__main__':
    # 输出路径
    project_root = backend_dir.parent
    output_path = project_root / 'frontend' / 'src' / 'types' / 'generated.ts'

    generate_types_file(output_path)