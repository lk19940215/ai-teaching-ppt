"""
数学工具函数模块
提供基础的数学运算功能
"""

from typing import Union


def sum(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    """
    计算两个数的和

    Args:
        a: 第一个数
        b: 第二个数

    Returns:
        两数之和
    """
    return a + b


def sub(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    """
    计算两个数的差

    Args:
        a: 被减数
        b: 减数

    Returns:
        两数之差
    """
    return a - b


def mul(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    """
    计算两个数的积

    Args:
        a: 第一个数
        b: 第二个数

    Returns:
        两数之积
    """
    return a * b


def div(a: Union[int, float], b: Union[int, float]) -> float:
    """
    计算两个数的商

    Args:
        a: 被除数
        b: 除数

    Returns:
        两数之商

    Raises:
        ZeroDivisionError: 当除数为零时抛出
    """
    if b == 0:
        raise ZeroDivisionError("除数不能为零")
    return a / b


def sqrt(a: Union[int, float]) -> float:
    """
    计算平方根

    Args:
        a: 非负数

    Returns:
        平方根

    Raises:
        ValueError: 当输入为负数时抛出
    """
    if a < 0:
        raise ValueError("不能对负数求平方根")
    return a ** 0.5