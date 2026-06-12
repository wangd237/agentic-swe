# jinja async repr repo

这个最小仓库从 `pallets/jinja#2151` 提炼而来。

它模拟 `AsyncLoopContext.__repr__` 错误访问 async 长度逻辑，导致字符串表示里暴露协程对象的缺陷。
