"""半真实的 requests 依赖约束配置。"""

from __future__ import annotations


INSTALL_REQUIRES = [
    "charset_normalizer>=2,<4",
    "idna>=2.5,<4",
    "urllib3>=1.21.1,<1.27",
    "certifi>=2017.4.17",
]


def get_install_requires() -> list[str]:
    # 测试通过读取这个函数返回值来校验依赖约束。
    return INSTALL_REQUIRES.copy()
