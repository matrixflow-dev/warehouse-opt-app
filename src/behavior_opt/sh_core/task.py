from typing import Iterator, NamedTuple

from behavior_opt.sh_core.item import Item
from behavior_opt.sh_core.store_point import StorePoint
from behavior_opt.sh_core.typing import Name

# そのアイテムと運ぶポイントを保持するクラス
# エージェントに割り振られていないタスクを保持する
class Task(NamedTuple):
    item: Item
    target_store_point: StorePoint


class Tasks:
    def __init__(self, task_list: list[Task]) -> None:
        self._tasks: list[Task] = task_list
        self._item_ids: list[Name] = [task.item.name for task in task_list]

    def index(self, item_id: Name) -> int:
        return self._item_ids.index(item_id)

    @property
    def items(self) -> list[Name]:
        return self._item_ids[:]

    def __len__(self) -> int:
        return len(self._tasks)

    def __getitem__(self, key: Name | Item | int) -> Task:
        if isinstance(key, Name):
            return self._tasks[self.index(key)]
        if isinstance(key, Item):
            return self._tasks[self.index(key.name)]
        return self._tasks[key]

    def __iter__(self) -> Iterator[Task]:
        return iter(self._tasks)

    def append(self, task: Task) -> None:
        self._tasks.append(task)
        self._item_ids.append(task.item.name)

    def remove(self, task: Task) -> None:
        index = self._tasks.index(task)
        del self._tasks[index]
        del self._item_ids[index]

    def pop(self, index: int) -> Task:
        task = self._tasks.pop(index)
        del self._item_ids[index]
        return task
