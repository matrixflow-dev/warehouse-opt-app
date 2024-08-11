from __future__ import annotations

from copy import copy
from typing import TYPE_CHECKING, Iterator

if TYPE_CHECKING:
    from behavior_opt.sh_core.agent import Agent
    from behavior_opt.sh_core.end_point import EndPoint
    from behavior_opt.sh_core.store_point import StorePoint

from behavior_opt.sh_core.typing import Length, Name, Position


class Item:
    def __init__(
        self,
        name: Name,
        volume: int,
        pos: Position,
        current_owner: Agent | StorePoint | None = None,
    ) -> None:
        self.name: str = name
        self.volume: int = volume
        self.pos: Position = pos
        # TODO: ItemSetに移動
        self.current_owner: Agent | StorePoint | None = current_owner
        self.end_point: EndPoint | None = None
        # simulation用
        self.is_picked = False
        # ship target
        self.ship_target: StorePoint | None = None

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, Item):
            return NotImplemented
        return self.name == __o.name and self.pos == __o.pos

    def get_dist(self, pos: Position) -> int:
        """Calculate Manhattan distance between item and pos."""
        return abs(self.pos.row - pos.row) + abs(self.pos.col - pos.col)


class ItemSet:
    def __init__(self, item: Item, amount: int) -> None:
        self.item = item
        self.amount = amount
        self.dist: Length | None = None
        # self.current_owner: Agent | StorePoint | None = None

    def pop(self) -> Item | None:
        if self.amount > 0:
            self.amount -= 1
            return copy(self.item)
        return None

    def calculate_dist(self) -> None:
        ship_target = self.item.ship_target
        if ship_target is not None:
            self.dist = self.item.get_dist(ship_target.pos)


class Items:
    def __init__(self, item_set_list: list[ItemSet]) -> None:
        self._object_list = item_set_list
        self._names = [item_set.item.name for item_set in self._object_list]
        self._positions = [item_set.item.pos for item_set in self._object_list]

    def index(self, name: Name) -> int:
        return self._names.index(name)

    @property
    def names(self) -> list[str]:
        return self._names[:]

    @property
    def positions(self) -> list[Position]:
        return self._positions[:]

    def __iter__(self) -> Iterator[ItemSet]:
        return iter(self._object_list)

    def __len__(self) -> int:
        return len(self._object_list)

    def __getitem__(self, key: Name | int) -> ItemSet:
        if isinstance(key, int):
            return self._object_list[key]
        return self._object_list[self.index(key)]

    def pop(self, key: Name | int) -> Item | None:
        if len(self) == 0:
            return None
        if isinstance(key, int):
            item_set = self._object_list[key]
        else:
            item_set = self._object_list[self.index(key)]
        item = item_set.pop()
        if item_set.amount == 0:
            self.remove(item_set)
        return item

    def add(self, item: Item) -> None:
        if item.name in self._names:
            self._object_list[self.index(item.name)].amount += 1
        else:
            self.append(ItemSet(item, 1))

    def append(self, item_set: ItemSet) -> None:
        self._object_list.append(item_set)
        self._names.append(item_set.item.name)
        self._positions.append(item_set.item.pos)

    def remove(self, item_set: ItemSet) -> None:
        index = self._object_list.index(item_set)
        del self._object_list[index]
        del self._names[index]
        del self._positions[index]

    def calculate_dists(self) -> None:
        for item_set in self._object_list:
            item_set.calculate_dist()

    def sort(self) -> None:
        self.calculate_dists()
        dists = [item_set.dist for item_set in self if item_set.dist is not None]
        if len(dists) == 0:
            return
        max_dist = max(dists)
        self._object_list.sort(
            key=lambda item_set: item_set.dist
            if item_set.dist is not None
            else max_dist + 1
        )
        self._names = [item_set.item.name for item_set in self._object_list]
        self._positions = [item_set.item.pos for item_set in self._object_list]

    def reset(self) -> None:
        self._object_list = [
            ItemSet(item_set.item, item_set.amount) for item_set in self._object_list
        ]
        self._names = [item_set.item.name for item_set in self._object_list]
        self._positions = [item_set.item.pos for item_set in self._object_list]
        self.sort()
