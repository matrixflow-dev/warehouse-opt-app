from typing import Iterator

from behavior_opt.sh_core.typing import Length, Name, PickDirection, Position


class Rack:
    def __init__(
        self,
        pos: Position,
        name: Name = "",
        width: Length = 1,
        height: Length = 1,
        pick_direction: PickDirection = "horizontal",
    ) -> None:
        self.name = name
        self.pos = pos
        self.width = width
        self.height = height
        self.pick_direction: PickDirection = pick_direction


class Racks:
    def __init__(self, racks: list[Rack]) -> None:
        self._object_list = racks
        self._names = [rack.name for rack in racks]
        self._positions = [rack.pos for rack in racks]

    def index(self, name: Name) -> int:
        return self._names.index(name)

    @property
    def names(self) -> list[str]:
        return self._names[:]

    @property
    def positions(self) -> list[Position]:
        return self._positions[:]

    def __iter__(self) -> Iterator[Rack]:
        return iter(self._object_list)

    def __len__(self) -> int:
        return len(self._object_list)

    def __getitem__(self, key: Name | int) -> Rack:
        if isinstance(key, Name):
            return self._object_list[self.index(key)]
        return self._object_list[key]

    def append(self, item: Rack) -> None:
        self._object_list.append(item)
        self._names.append(item.name)
        self._positions.append(item.pos)

    def remove(self, item: Rack) -> None:
        index = self.index(item.name)
        del self._object_list[index]
        del self._names[index]
        del self._positions[index]

    def reset(self) -> None:
        for i, rack in enumerate(self):
            rack.name = "rack_{}".format(i)
