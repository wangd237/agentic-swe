这个最小仓库从 `pypa/packaging#1240` 提炼而来。

它模拟 `DirectUrl._from_dict()` 在检查 file URL 时大小写敏感、且错误拒绝 `file:/...` 形式的缺陷。
