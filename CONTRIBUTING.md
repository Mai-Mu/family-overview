# 贡献说明

欢迎通过Issue说明使用场景或问题，也可提交改进。

## 本地开发

使用Python 3.12或更新版本，在项目根目录执行`python server.py --open`。无需安装第三方运行依赖。源码目录与职责见README。

修改字段时先编辑`design/build_field_catalog.py`，再运行生成器，保持JSON与HTML一致。业务字段继续允许留空；统计必须区分空白、真实零和金额范围，不混合不同币种，不自动平均分配共同资产。

提交前运行：

```sh
python -m unittest discover -s tests -v
python design/build_field_catalog.py
git add <需要提交的源文件>
python scripts/check_public_files.py
```

前端改动可加做`node --check web/app.js`，并验证相关界面操作。测试与截图只使用合成数据。

## 提交资料

Issue、截图、日志与代码中均不要包含实际家庭财务资料、账户信息、完整证件号码、私人联系方式、本机用户目录或访问凭据。数据库、上传附件、ZIP备份和测试产物不应进入Git。

提交说明应写清变化、原因和验证结果；较大功能先描述使用场景与数据口径。
