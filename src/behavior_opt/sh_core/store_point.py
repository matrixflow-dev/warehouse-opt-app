from typing import Iterator

from behavior_opt.sh_core.end_point import EndPoint
from behavior_opt.sh_core.item import Item, Items
from behavior_opt.sh_core.typing import Name, PickDirection, Position


class StorePoint:
    def __init__(
        self,
        pos: Position,
        name: Name = "",
        pick_direction: PickDirection = "horizontal",
    ) -> None:
        self.pos: Position = pos
        self.name = name
        self.pick_direction: PickDirection = pick_direction
        self.end_point: EndPoint | None = None
        self.having_items: Items = Items([])

        self.is_picked = False

    def stored(self, item: Item) -> None:
        self.having_items.add(item)
        item.current_owner = self

    def taken_out(self, item_name: Name) -> Item | None:
        self.is_picked = True
        taken_out_item = self.having_items.pop(item_name)
        return taken_out_item


class StorePoints:
    def __init__(self, store_points: list[StorePoint]) -> None:
        self._object_list = store_points
        self._names = [store_point.name for store_point in store_points]
        self._positions = [store_point.pos for store_point in store_points]
        self._pick_directions: list[PickDirection] = [
            store_point.pick_direction for store_point in store_points
        ]

    def index(self, name: Name) -> int:
        return self._names.index(name)

    @property
    def names(self) -> list[Name]:
        return self._names[:]

    @property
    def positions(self) -> list[Position]:
        return self._positions[:]

    @property
    def pick_directions(self) -> list[PickDirection]:
        return self._pick_directions[:]

    def __iter__(self) -> Iterator[StorePoint]:
        return iter(self._object_list)

    def __len__(self) -> int:
        return len(self._object_list)

    def __getitem__(self, key: Name | int | Position) -> StorePoint:
        if isinstance(key, Name):
            return self._object_list[self.index(key)]
        if isinstance(key, Position):
            return self._object_list[self._positions.index(key)]
        return self._object_list[key]

    def append(self, store_point: StorePoint) -> None:
        self._object_list.append(store_point)
        self._names.append(store_point.name)
        self._positions.append(store_point.pos)
        self._pick_directions.append(store_point.pick_direction)

    def remove(self, store_point: StorePoint) -> None:
        index = self.index(store_point.name)
        del self._object_list[index]
        del self._names[index]
        del self._positions[index]
        del self._pick_directions[index]

    def reset(self) -> None:
        for i, sp in enumerate(self):
            sp.name = "store_point_{}".format(i)
        self._names = [sp.name for sp in self]
        self._pick_directions = [sp.pick_direction for sp in self]
        self._positions = [sp.pos for sp in self]
