# remove-aisa 实施记录

日期：2026-10-17。当前分支：remove-aisa。

## 已实现

- 移除旧 AIsa 客户端，独立接入 DeepSeek、两种可选 X 供应商、DataForSEO、Reddit OAuth 和 YouTube Data API；保留原独立来源。
- CLI、MCP、每日采集、关键词、需求、痛点、趋势复盘和新网站模块改用独立适配层。
- 本地 JSON v2 配置、显式非覆盖迁移；默认禁止网络，原配置不改动。
- 固定来源 HTTP、禁重定向、AIsa 域名拦截、持久化请求上限、缓存、运行锁和费用未知标记。
- Markdown/JSON 报告保留供应商失败与费用记录；缺搜索量不伪装成零、未知竞争度不伪装为拥挤。
- 新增离线验收工具及配置启动指南。
- 支持 --providers-config：复用原业务配置，供应商密钥与限额单独保存，CLI/MCP 均支持；本地文件不入库。

## 已执行证据

在包含源码的 Windows 本地环境执行：

- 完整离线回归：142 passed，0 failures。
- 零 AIsa 专项：4 passed，0 failures；包含域名拦截与静态依赖检查。
- 静态 inventory：PASS，旧模块不存在、未发现旧模块导入。
- git diff --check：通过。

可复现命令见 [配置启动指南](../REMOVE_AISA_GUIDE.md)。本次原始日志、JUnit XML、摘要、验收报告在 `state/acceptance/latest/`，属于本地运行数据，不提交密钥或 state。

## 尚未完成

所有13项真实供应商验收仍为 NOT_RUN。当前代码和模拟接口测试不能证明线上功能等效。

- 真实 API 字段、分页、空结果、账号覆盖及服务资格确认。
- 模型保留集人工标注与原基线对照。
- 7天14轮稳定性、新鲜度、召回率验证及真实14天复盘。
- 实际账单对账、预算确认；请求次数上限不能替代金额上限。
- 真实 smoke / compare 自动化与证据集构建，目前验收命令只支持离线 inventory/contracts/no-aisa/report。
- Linux 实机与 GitHub Actions 运行验证。

因此当前交付为开发实现与离线验证，不是“全功能替代验收完成”。未切换正式定时任务，未调用真实付费接口，尚未执行真实付费验收。
