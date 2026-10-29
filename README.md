# ChatGPT Windows Runtime Repair

用于补齐 Windows 版 ChatGPT / Codex 的运行组件缓存，针对应用实际安装在 D 盘等非系统盘时，WindowsApps 加密文件复制异常导致的特定启动问题。

**这是非官方、按需手动运行的修复辅助工具，不是安装器，也不保证能解决所有“没有窗口”的启动故障。**

## 用途与适用现象

- 应用包名称为 `OpenAI.Codex`，显示名称可能为 ChatGPT。
- 从开始菜单或原 Applications 入口启动时没有界面，只出现后台进程。
- 直接运行安装目录中的可执行文件可能正常。
- 日志可能停在 `Launching app` 附近，尚未出现 Node 运行组件解析成功的记录。
- 从受保护的 WindowsApps 安装包复制文件时，Node 的普通文件复制可能返回 `UNKNOWN -4094`，而读取内容再写入可以成功。

上述症状并不能单独证明根因。此工具只针对 `cua_node` 组件缓存缺失或不完整这一环节。

## 环境要求

- Windows，当前用户已安装并注册 `OpenAI.Codex` 应用。
- Python **3.11 或更高版本**，`python` 命令可用。
- Windows PowerShell 可用；不需要额外 Python 库。
- 修复前完全退出 ChatGPT。工具不会自动终止任何应用进程，也不需要管理员运行。

## 使用步骤

1. 下载仓库 ZIP 并解压，或下载仓库内的 `ChatGPT-runtime-repair.zip` 并解压。
2. 完全退出 ChatGPT，确认任务管理器没有 `ChatGPT.exe`。
3. 双击 `Repair-ChatGPT.cmd`，等待完成。
4. 从**原来的 Applications / 开始菜单应用入口**重新启动。

程序本体可以继续安装在 D 盘。该工具不会移动应用。

也可以在终端中运行：

```powershell
# 默认仅检查，不修改任何缓存；ChatGPT 正在运行时也可以检查。
python repair_runtime.py

# 修复：需先完全退出 ChatGPT。
python repair_runtime.py --repair
```

如果提示 `Cache is already complete. No changes needed.`，说明缓存检查通过，工具不会强制重建。此时若仍无法启动，应继续检查其他原因。

## 工作方式与修改范围

1. 使用 `Get-AppxPackage` 找到当前安装包。
2. 根据当前包内 `manifest.json`、`bin/node.exe`、`bin/node_repl.exe` 的内容计算组件缓存标识，不写死版本号。
3. 检查三个关键文件的 SHA-256，以及源组件文件在缓存中的存在性和大小。
4. 如需修复，在缓存目录内建立临时目录，通过二进制读取、写入复制组件，避免复制安装包的加密元数据。
5. 检查复制结果和源组件标识，再发布到当前版本的缓存目录。
6. 若已存在不完整缓存，先重命名为 `.backup-<随机标识>` 保留，不直接删除。

写入范围为：

```text
%LOCALAPPDATA%\OpenAI\Codex\runtimes\cua_node\
```

工具不修改 WindowsApps 安装文件、应用注册、权限设置、登录信息、聊天记录或 `.codex` 配置；不联网、不上传任何文件，也不创建自动运行任务。

## 验证范围与限制

- 已通过模拟文件测试：缓存标识、组件复制、关键文件损坏检测、旧缓存备份保留。
- 已在问题机器验证：普通复制受保护文件失败，而读取再写入成功。
- 问题机器通过在 C 盘完成组件准备、再移动回 D 盘后恢复启动。
- **尚未在故障复发时，以本工具完成一次端到端恢复测试。** 不应把工具测试通过等同于已经证明所有启动失败均由此问题造成。
- 非关键文件检查使用存在性和大小，不逐个校验 SHA-256。
- 应用后续版本可能改变目录或缓存标识算法。工具按当前观察到的版本行为编写；若结构变化，应先更新工具。
- 修复期间请保持 ChatGPT 关闭，不要并行更新或移动应用。
- 异常中断可能留下 `repair-staging-*` 临时目录；工具不会自动清理它们，以便保留诊断和恢复材料。
- 只应在故障出现并与此问题相符时运行；无需每次更新都主动运行。

## 测试

```powershell
python tests/test_runtime_repair.py
```

测试使用测试目录下的临时模拟组件，不操作真实应用缓存。

## 相关公开问题

- [非系统盘安装时 Applications 启动无窗口，移动到系统盘后恢复：#41093](https://github.com/openai/codex/issues/41093)
- [运行组件准备失败，手动补齐后恢复启动：#42501](https://github.com/openai/codex/issues/42501)
- [Applications 入口失败、直接运行程序正常：#25221](https://github.com/openai/codex/issues/25221)

这些是不同用户、不同版本的案例，不代表官方确认了本机故障的唯一原因。
