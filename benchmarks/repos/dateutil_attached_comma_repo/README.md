# dateutil_attached_comma_repo

这是从 `dateutil/dateutil#1191` 提炼出的最小 `semi_real` benchmark。

当前缺陷：

- `may15 , 2021` 可以正确解析出 `2021-05-15`
- `may15,2021` 却因为逗号紧贴年份，没有被正确识别出 year
- 最终错误回落到默认年份

期望行为：

- `may15,2021` 应与加空格的版本保持一致
- 都应被解析成 `2021-05-15`
