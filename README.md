# 家庭一览 · Family Overview

一个本地优先的家庭经济信息管理工具。把家庭成员、资产负债、定期收支与重大约定放在一起，方便家人共同商讨、由一人统一维护。

从一次家底盘点开始，之后按收入规则、固定费用和重大变化持续更新。所有业务字段均可留空，允许先保存草稿，再逐步补充。

![家庭一览首页，空白数据状态](docs/screenshots/desktop.jpg)

## 功能

| 模块 | 记录内容 |
| --- | --- |
| 家庭成员 | 成员称呼、角色及基础经济情况 |
| 资产盘点 | 逐项资产、归属、估值及盘点日期 |
| 负债与借款 | 剩余欠款、承担人及还款安排 |
| 借出款 | 债权归属、余额与预计收回时间 |
| 担保责任 | 责任范围与关联约定 |
| 定期收支 | 工资、养老金、水电、电话费、月供等规则 |
| 重大与约定 | 待商讨事项、承担安排、已付、待付和预留金额 |
| 养老与保障 | 养老、医保与商业保险摘要 |

支持按成员查看、搜索与状态筛选、附件上传下载、修改历史、移除恢复和ZIP备份。桌面采用侧边导航与详情面板，窄屏采用折叠导航。

金额保留空白与真实零的区别，支持区间金额；不同币种分开汇总。共同安排不默认平均分摊，定期规则形成月度预计收支，实际支付累计由用户确认。

## 快速开始

需要 **Python 3.12或更新版本**，无需安装第三方运行依赖。

```sh
git clone https://github.com/Mai-Mu/family-overview.git
cd family-overview
python server.py --open
```

Windows也可双击根目录的`启动家庭一览.cmd`。

默认访问地址为 <http://127.0.0.1:8765>。使用时保持服务运行；关闭终端或按`Ctrl+C`停止。需要其他端口时使用`python server.py --port 8766 --open`。

### 初次填写

1. 在首页建立成员，默认角色模板可修改，也可自行新增。
2. 盘点当前资产与负债，填写金额对应的截至日期。
3. 整理长期收入、固定费用及还款规则。
4. 补充重大或约定事项，记录时间、金额、承担人和付款进度。
5. 按需补充保障、借出款、担保和附件。

点击保存后写入SQLite。当前浏览器会临时缓存最近一份未保存内容，刷新后恢复；附件需要重新选择，明确放弃更改会清除临时草稿。

## 技术栈与目录

前端使用原生HTML、CSS和JavaScript ES Modules；后端使用Python标准库`http.server`与`sqlite3`，金额统计采用`Decimal`。

```text
family-overview/
├── server.py                   # 本机HTTP服务、数据接口与SQLite
├── web/                        # 前端页面、样式和交互
├── design/                     # 字段生成器、JSON定义和HTML字段目录
├── docs/                       # 需求、实现设计、验证记录及页面预览
├── tests/                      # 临时数据库与HTTP测试
├── scripts/                    # 公开文件检查工具
├── .gitignore                  # 数据、附件、备份和本机文件排除规则
└── 启动家庭一览.cmd             # Windows启动入口
```

`data/`在启动时自动创建，仅用于本机运行，不进入版本控制。

## 数据与备份

- 数据库：`data/family.sqlite3`。
- 附件：`data/uploads/`。
- 备份：页面右上角“备份数据”下载ZIP，包含数据库一致性快照、附件、记录JSON和字段定义。

恢复时先停服，将当前`data`目录另行留存，再把ZIP中的`family.sqlite3`和`uploads`放进新的`data`目录，重新启动。第一版采用手动文件恢复。

应用仅监听`127.0.0.1`，没有登录、应用级加密、云端同步或AI服务接入。数据库、附件、备份与浏览器草稿都可能包含私人资料，保存在个人设备中，勿提交到公开仓库。具体说明见[数据与安全](SECURITY.md)。

## 开发与验证

```sh
python -m unittest discover -s tests -v
python design/build_field_catalog.py
python scripts/check_public_files.py
```

已安装Node.js时，可额外执行`node --check web/app.js`。Node.js仅用于开发检查。

字段目录由生成器维护，修改`design/build_field_catalog.py`后重新生成JSON与HTML。测试使用临时目录和合成数据。

## 文档

- [功能需求与统计口径](docs/requirements.md)
- [页面与存储设计](docs/architecture.md)
- [验证记录](docs/testing.md)
- [详细字段目录](design/家庭经济信息收集字段设计.html)
- [贡献说明](CONTRIBUTING.md)
