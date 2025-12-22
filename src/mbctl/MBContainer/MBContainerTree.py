from __future__ import annotations

from typing import Dict, List, Mapping, Sequence, Set

from .MBContainer import MBContainer


class MBContainerTree:
	"""
	根据 `MBContainer.require` 构建依赖树（森林），并提供自底向上的层序遍历以解析引用。

	使用方法：
	- 初始化时传入一组尚未解析的 `MBContainer` 对象。
	- 调用 `resolve_all()`，将按依赖树的最底层到最上层顺序依次调用每个容器的 `resolve_references()`，最终原地解析完毕。
	- 如需观察层次结构，可调用 `levels()` 获取从叶子到根的分层列表。
	"""

	def __init__(self, containers: Sequence[MBContainer]):
		self._name_to_container: Dict[str, MBContainer] = {c.name: c for c in containers}
		# 依赖映射：容器名 -> 其直接依赖的容器名集合
		self._deps: Dict[str, Set[str]] = {
			c.name: set(c.require) for c in containers
		}

		# 校验：所有依赖都必须在输入集合中出现
		for name, reqs in self._deps.items():
			missing = [r for r in reqs if r not in self._name_to_container]
			if missing:
				raise ValueError(
					f"Container '{name}' requires missing containers: {missing}"
				)

		# 校验：不得存在环（要求依赖必须为树/森林结构）
		self._assert_acyclic()

	def _assert_acyclic(self) -> None:
		# 使用 Kahn 算法检测环
		deps_copy: Dict[str, Set[str]] = {k: set(v) for k, v in self._deps.items()}
		remaining: Set[str] = set(deps_copy.keys())
		progress = True
		while progress and remaining:
			progress = False
			# 找到当前叶子（无依赖）
			leaves = [n for n in remaining if len(deps_copy[n]) == 0]
			if not leaves:
				# 若没有叶子却仍有剩余节点，说明存在环
				break
			progress = True
			for leaf in leaves:
				remaining.remove(leaf)
				# 从其他节点依赖集合中移除该叶子
				for other in remaining:
					if leaf in deps_copy[other]:
						deps_copy[other].remove(leaf)
		if remaining:
			raise ValueError(
				f"Dependency graph contains cycles among: {sorted(list(remaining))}"
			)

	def levels(self) -> List[List[MBContainer]]:
		"""
		返回从叶子到根的层次列表，每一层是若干 `MBContainer`。
		"""
		deps_copy: Dict[str, Set[str]] = {k: set(v) for k, v in self._deps.items()}
		remaining: Set[str] = set(deps_copy.keys())
		levels: List[List[MBContainer]] = []

		while remaining:
			# 叶子：无依赖的容器
			leaf_names = [n for n in remaining if len(deps_copy[n]) == 0]
			if not leaf_names:
				# 正常情况下不会发生，_assert_acyclic 已经保证无环
				raise RuntimeError("No leaves found while building levels; graph inconsistent.")
			level_containers = [self._name_to_container[n] for n in leaf_names]
			levels.append(level_containers)
			# 移除叶子并更新依赖
			for leaf in leaf_names:
				remaining.remove(leaf)
				for other in remaining:
					deps_copy[other].discard(leaf)
		return levels

	def resolve_all(self) -> None:
		"""
		自底向上层序遍历，依次调用每个容器的 `resolve_references()`，
		将其 `require` 对应的容器作为参考传入，从而完成就地解析。
		"""
		# 从最底层（叶子）到最顶层依次解析
		for level in self.levels():
			for container in level:
				ref_containers: Mapping[str, MBContainer] = {
					dep_name: self._name_to_container[dep_name]
					for dep_name in container.require
				}
				container.resolve_references(ref_containers)

