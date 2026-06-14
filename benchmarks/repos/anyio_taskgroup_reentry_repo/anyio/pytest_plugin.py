"""最小占位 pytest plugin。

本地 semi-real 仓库里的 `anyio` 包会遮住环境中已安装的 anyio。
pytest 在自动加载入口点时会尝试导入 `anyio.pytest_plugin`，
这里提供一个空插件模块，让测试能够继续进入我们真正关注的回归语义。
"""
