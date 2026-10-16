# 文件配置与Bash启动器验证记录

用户范围：依赖与配置修改手册；不得使用环境变量配置项目；Linux和Windows均用Bash脚本；实际用Windows脚本启动。用户选择完整模式，凭证由用户在本地填写，不在聊天中收集。

分支：feat/file-config-launchers，从已交付文档分支的858ef43继续；没有修改或推送原文档草稿PR。本轮业务配置入口按用户新要求更改，原0.4.0资料保留历史基线，操作以USER_MANUAL为准。

## 交付与实现

- [用户手册](../USER_MANUAL.md)：依赖、两平台安装、JSON字段、可选服务、命令、报告、退出码、迁移限制。
- scripts/start-linux.sh、scripts/start-windows.sh、scripts/start-common.sh：Bash脚本，定位仓库、setup/虚拟环境、传递参数，固定Python `-E -X utf8`，无export/凭证环境注入/PowerShell。
- requirements-launcher.txt：标准邮件与MCP启动依赖；.gitattributes强制.sh使用LF。
- radar.settings：从配置加载凭证与地址的ContextVar；不读取环境或用户CLI缓存；普通线程池通过inherit_context继承，asyncio.to_thread沿用上下文。
- config.load：UTF-8/BOM读取，credentials/services字段和类型校验，服务地址HTTPS约束；重新加载清除旧凭证。
- AIsa/GoAnyAPI/GitHub/TrustMRR/邮件/GSC均改为文件配置；MCP路径改为--config/--state。
- server.json移除过时的凭证environmentVariables广告；客户端以本地配置/命令行路径使用本分支。
- launcher：完整模式先检查本地AIsa Key，缺失直接停止；配置GSC时检查token文件；daily可见数据块错误返回3，不能当完整采集成功。
- config.json及reports/本地文件被忽略；没有把密钥加入示例、日志或Git。

## 已执行验证

1. 修改前现有用例迁移至文件设置后：95 passed in 6.58s；仅替换已变更配置契约的输入方式，未删除原算法断言。
2. 新增凭证隔离、reload、服务地址最终消费、线程上下文、预检阻止无Key采集、降级结果、Windows真实脚本等测试后：**109 passed in 8.27s**。
3. Windows真实Bash集成用例：从其他工作目录，传入含空格的配置路径，调用start-windows.sh check，exit0；只用测试假Key，无网络，输出不含Key。
4. `bash -n`检查三份Bash脚本通过。
5. 已真实执行`bash scripts/start-windows.sh setup`，安装/确认markdown3.11.1与mcp2.3.0及其依赖，exit0；保留已有config.json，不覆盖用户配置。
6. 最终补验配置缺失也统一返回预检exit2，完整测试：**110 passed in 5.86s**；真实`start-windows.sh --help`通过。
7. 15个手册/入口/验证记录本地链接通过；runtime AST无environ/getenv/putenv读取；启动脚本LF、实际命令无export/eval/PowerShell；git diff --check通过。config.json与reports/startup.log均由git check-ignore确认未纳入追踪。
8. 用户要求提交并合入main前再次执行完整测试：110 passed in 6.17s；三份Bash语法检查与git diff --check通过。实际API认证失败作为运行验收限制保留，不以单元测试通过替代。

## 本机完整模式启动结果

实际命令：在Git for Windows Bash中执行`bash scripts/start-windows.sh`，默认daily；标准输出/错误保存于本地reports/startup.log。

**结果：exit2，预检停止。** 提示：`fill credentials.aisa_api_key in the local config file before full-mode startup`。本地AIsa Key为空，尚未开始正式采集，不能声称项目已完成完整模式运行。未偷偷降为免费模式、未使用假Key跳过预检、未读取环境里的密钥。没有发起真实收费采集或发送邮件。

首次尝试后的后续步骤是用户在本机config.json填写Key后重试；此步骤已经完成，实际重试与最终结果见下。密钥未在聊天或命令行提供。

### 用户保存凭证后的实际重试

用户已确认本地保存配置；已通过同一个Windows Bash脚本重新启动默认daily完整模式。文件预检通过，进程已进入采集，已有HF/GitHub及部分站点基线写入。中间一次只读检查时：静默运行约13.5分钟，6个状态快照，其中2个sitemap站点基线，配置共12站；当时进程仍存活、尚未写最终报告。该进度是历史快照，最终结果如下。

Windows脚本的**实际启动验证已通过**（预检、进入daily、进程持续执行且写出快照），不等于所有API调用成功。运行没有中止或重复启动；本地日志为reports/startup.log，没有读取环境密钥或切换免费模式。

### 最终结果：已结束，数据不完整

- 报告完成时间：2026-10-16 21:37:15（北京时间，由report.json文件修改时间转换）。进程最终退出码为**3**，启动器正确标记不完整结果。
- 已生成本地reports/report.md与report.json：15条候选线索、0条关键词研究结果；15个状态快照，其中11个sitemap基线。
- AIsa的X工具路由返回HTTP401、authentication_required；关键词研究接口返回HTTP401、invalid_api_key，提示应检查是否为完整AIsa Key、而非上游供应商Key。文件非空只证明预检通过，不证明远程认证有效。没有把真实Key写入此记录。
- toolify返回“no URLs read”；其他来源中HF模型/Spaces首次各读取100项，GitHub搜索193个仓库。部分周信号被调度跳过，GSC未配置关闭；这些与认证失败分开记录。
- 结论：启动脚本、文件凭证通路和错误退出行为已实际验证；AIsa完整业务链尚未成功验收。后续需用户在本地核对有效AIsa凭证，以及单独核验toolify的sitemap/可访问性；本轮未更换Key、未重复发起收费采集。

## 复核与限制

- 文件凭证不是通过环境变量桥接；JSON不会被source/eval；脚本不开启set-x；Python与pip分别忽略各自的环境配置覆盖。
- 单独的原生Linux执行环境不可用；Linux脚本仅完成Bash语法和共享逻辑检查，未冒称Linux端到端启动通过。
- 远程API有效性、余额/模型支持、真实OAuth/邮件/MCP客户端、CI和定时任务未验收。
- 原GitHub Actions/Skills环境注入示例尚未迁移，手册已警示不可直接沿用；本轮没有启用远程任务。
- 本机首轮Bash因Windows沙箱的MSYS初始化限制失败，改用获准的沙箱外Git Bash执行；此后安装、测试和实际启动均未使用PowerShell。
