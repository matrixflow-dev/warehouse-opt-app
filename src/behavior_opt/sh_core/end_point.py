from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Iterator

if TYPE_CHECKING:
    from behavior_opt.sh_core.store_point import StorePoint, StorePoints

from behavior_opt.sh_core.typing import (
    ACTIONS,
    Action,
    Length,
    Name,
    PickDirection,
    Position,
)


class EndPoint:
    def __init__(
        self, pos: Position, name: Name = "", store_point: StorePoint | None = None
    ) -> None:
        self.name: Name = name
        self.pos: Position = pos


class EndPoints:
    def __init__(self, end_points: list[EndPoint]) -> None:
        self._object_list = end_points
        self._names = [end_point.name for end_point in end_points]
        self._positions = [end_point.pos for end_point in end_points]

    def index(self, name: Name) -> int:
        return self._names.index(name)

    @property
    def names(self) -> list[Name]:
        return self._names[:]

    @property
    def positions(self) -> list[Position]:
        return self._positions[:]

    def __iter__(self) -> Iterator[EndPoint]:
        return iter(self._object_list)

    def __len__(self) -> int:
        return len(self._object_list)

    def __getitem__(self, key: Name | int | Position) -> EndPoint:
        if isinstance(key, Name):
            return self._object_list[self.index(key)]
        if isinstance(key, Position):
            return self._object_list[self._positions.index(key)]
        return self._object_list[key]

    def append(self, end_point: EndPoint) -> None:
        assert end_point.pos not in self._positions, "end_point.pos is duplicated."

        self._object_list.append(end_point)
        self._names.append(end_point.name)
        self._positions.append(end_point.pos)

    def remove(self, end_point: EndPoint) -> None:
        index = self.index(end_point.name)
        del self._object_list[index]
        del self._names[index]
        del self._positions[index]

    def sort_by_pos(self, max_width: Length) -> None:
        self._object_list.sort(key=lambda x: x.pos.row * max_width + x.pos.col)
        self._names = [item.name for item in self._object_list]
        self._positions = [item.pos for item in self._object_list]

    def reset(
        self,
        store_points: StorePoints,
        can_put: Callable[[Position], bool],
        map_width: Length,
    ) -> None:
        for sp in store_points:
            pos = self._select_position(sp, can_put, sp.pick_direction)
            if pos in self._positions:
                sp.end_point = self[pos]
            else:
                end_point = EndPoint(pos=pos)
                sp.end_point = end_point
                self.append(end_point)

            for item_set in sp.having_items:
                item_set.item.end_point = sp.end_point
        self.sort_by_pos(map_width)
        for i, ep in enumerate(self):
            ep.name = "{}".format(i)
        self._names = [ep.name for ep in self]
        self._positions = [ep.pos for ep in self]

    def _select_position(
        self,
        store_point: StorePoint,
        can_put: Callable[[Position], bool],
        pick_direction: PickDirection,
    ) -> Position:
        if pick_direction == "horizontal":
            action_list = (ACTIONS[Action.LEFT], ACTIONS[Action.RIGHT])
        elif pick_direction == "vertical":
            action_list = (ACTIONS[Action.UP], ACTIONS[Action.DOWN])
        elif pick_direction == "on":
            action_list = (ACTIONS[Action.NOOP], ACTIONS[Action.NOOP])
        else:
            raise ValueError("Invalid pick_direction: {}".format(pick_direction))

        action = action_list[0]
        tmp_pos = Position(
            store_point.pos.row + action.row, store_point.pos.col + action.col
        )
        if can_put(tmp_pos):
            pos = tmp_pos
        else:
            action = action_list[1]
            pos = Position(
                store_point.pos.row + action.row, store_point.pos.col + action.col
            )
        assert pos.row >= 0 and pos.col >= 0, "pos is invalid."
        return pos
