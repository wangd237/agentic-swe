# pydantic_inheritance_repo

这是从 `pydantic/pydantic#9582` 提炼出的最小 `semi_real` benchmark。

当前缺陷：

- 父类和子类都可以定义 `model_validator`
- 但旧逻辑里子类一旦声明自己的 validator
- 父类 validator 就会被整条覆盖掉

期望行为：

- 子类校验时继续执行父类 validator
- 再执行子类自己的 validator
- 父类单独校验路径保持不变
