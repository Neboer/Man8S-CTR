# 命令行

## 自动重启


下表总结了，NerdCTL容器的各种不同状态在Man8S容器中执行对应动作时的具体行为。

| 指令执行\容器状态 | Never | Created | Up     | Exited | Restarting |
| ----------------- | ----- | ------- | ------ | ------ | ---------- |
| enable            | Write config | Write config (no runtime change) | Update restart policy | Update restart policy | Update restart policy |
| disable           | Write config | Write config | Update restart policy | Update restart policy | Update restart policy |
| enable --now      | Create & start (run) | Start (nerdctl start) | Update restart policy (already running) | Update restart policy & start | Update restart policy (skip immediate start) |
| disable --now     | Write config | Write config | Update restart policy + stop | Update restart policy | Update restart policy + stop |
| autostart         | No-op (no runtime) | Start (nerdctl start) | No-op | Start (nerdctl start) | Skip (do not force start while restarting) |

说明：
- 本项目不依赖于不存在的 `--no-start` 选项；对于 `Created` 状态的容器，默认只修改磁盘配置（写入 `autostart: true/false`），不强行重建或修改 containerd 的 task。这样避免对 containerd 在没有 task 情况下执行 `update` 导致的错误。
- 当用户传入 `--now` 时：
	- 若容器在主机上不存在（Never），`enable --now` 会创建并启动容器（相当于 compose up）；`disable --now` 仅写配置，不会创建容器。
	- 若容器处于 `Created`（已创建但未启动），`enable --now` 会调用 `nerdctl start` 启动该容器；`disable --now` 仍只写配置（没有运行时可停止）。
	- 若容器处于 `Up`，`enable`/`disable` 会优先通过 `nerdctl update --restart` 同步重启策略；`--now` 会在 `disable` 时同时停止容器（`nerdctl stop` + `nerdctl wait`），在 `enable` 时若容器已运行则不重复启动。
- `autostart` 命令用于主机启动或恢复时运行：它按配置中的依赖树自底向上遍历，尝试对那些配置了 `autostart: true` 且在运行时不是 `Up` 的容器执行 `nerdctl start`（对 `Created` 与 `Exited` 状态进行启动），而不会对 `Restarting` 状态强制启动或重建。
- 这一区分的目的是把“修改配置文件”与“影响运行时 task”分开：常规的 `enable`/`disable` 先保证配置被写回磁盘，再根据容器当前 runtime 状态决定是否立即同步 runtime（仅在用户显式指定 `--now` 或在 `autostart` 场景下按需启动）。