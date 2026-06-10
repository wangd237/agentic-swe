# packaging_specifier_repo

这是从 `pypa/packaging#810` 提炼出的最小 `semi_real` benchmark。

当前缺陷：

- `>4.1.0a2.dev1234` 这类 `Specifier` 在比较带 `local` 段的版本时
- 错误地只比较了 `base_version`
- 导致 `4.1.0a2.dev1235+local` 也被错误判成不满足条件

期望行为：

- 相同 public 版本加 `local` 段时，仍应判为不满足 `>`
- 但当 `dev` 段已经更大时，即便带 `local` 段，也应正确判为满足 `>`
