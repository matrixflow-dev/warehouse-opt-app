from copy import deepcopy

import numpy as np

from behavior_opt.sh_core.agent import Agent, Agents, Goal
from behavior_opt.sh_core.end_point import EndPoints
from behavior_opt.sh_core.item import Item, Items, ItemSet
from behavior_opt.sh_core.rack import Rack, Racks
from behavior_opt.sh_core.store_point import StorePoint, StorePoints
from behavior_opt.sh_core.task import Task, Tasks
from behavior_opt.sh_core.typing import (
    FIELD_TYPE,
    AgentConfig,
    Amount,
    ItemConfig,
    Length,
    MapConfig,
    Name,
    PickDirection,
    PickingTask,
    Position,
    PreconversionPosition,
    Volume,
)


class World:
    def __init__(
        self,
        map_config: MapConfig,
        item_configs: list[ItemConfig],
        agent_configs: list[AgentConfig],
        picking_list: list[PickingTask],
    ) -> None:
        self.map_config: MapConfig = MapConfig(**map_config)
        self.agent_configs: list[AgentConfig] = agent_configs
        self.item_configs: list[ItemConfig] = item_configs
        self.map_height: int = self.map_config["map_height"]
        self.map_width: int = self.map_config["map_width"]
        self.picking_list = picking_list
        self.field_type = FIELD_TYPE
        self.reset()

    def reset(self) -> None:
        self.world_map = np.zeros(
            (self.map_config["map_height"], self.map_config["map_width"]), dtype=int
        )
        self.agents = Agents([])
        self.items = Items([])
        self.goals: list[Goal] = []
        self.racks = Racks([])  # obstacles
        self.store_points: StorePoints = StorePoints([])
        self.end_points: EndPoints = EndPoints([])
        for w in self.map_config["racks"]:
            self._add_rack(**w)
        self.create_plain_map()
        for i in self.item_configs:
            self._add_item(**i)
        for a in self.agent_configs:
            self._add_agent(**a)
        self._reset_objects()
        self.n_agents = len(self.agents)

    def picking(self, agent: Agent, item: Item) -> None:
        store_point = item.current_owner
        assert isinstance(
            store_point, StorePoint
        ), f"item's owner is not StorePoint. {item.current_owner}"
        assert store_point.end_point is not None, "store_point's end_point is None"
        assert (
            store_point.end_point.pos == agent.pos
        ), f"item is different from agent's pos {store_point.end_point.pos} != {agent.pos}"
        taken_out_item = store_point.taken_out(item.name)
        assert taken_out_item is not None, f"item is None. item_id: {item.name}"
        agent.pick_up(taken_out_item)

    def dropping(self, agent: Agent, item: Item) -> None:
        task: Task = self.tasks[item]
        store_point = task.target_store_point
        assert isinstance(store_point, StorePoint), "item's target is not StorePoint"
        assert store_point.end_point is not None, "store_point's end_point is None"
        assert (
            store_point.end_point.pos == agent.pos
        ), f"item is different from agent's pos {agent.pos} != {store_point.end_point.pos}, task: {task.item.name}"
        drop_off_item = agent.drop_off(item)
        assert drop_off_item is not None, f"item is None. item_id: {item.name}"
        store_point.stored(drop_off_item)

    def _reset_objects(self) -> None:
        self._reset_agents()
        self._reset_items()
        self._reset_racks()
        self._reset_store_points()
        self._reset_end_points()
        self._reset_tasks()

    def _reset_agents(self) -> None:
        self.agents.reset()
        for agent in self.agents:
            assert agent.goal is not None, "agent's goal is None"
            self.goals.append(agent.goal)

    def _reset_items(self) -> None:
        for item_id, target_pos, _ in self.picking_list:
            store_point = self._create_store_point(Position(*target_pos))
            for item_index in iter(*np.where(np.array(self.items.names) == item_id)):  # type: ignore
                self.items[int(item_index)].item.ship_target = store_point
        self.items.reset()

    def _reset_store_points(self) -> None:
        self.store_points.reset()

    def _reset_end_points(self) -> None:
        self.end_points.reset(
            self.store_points, self._can_put_end_point, self.map_width
        )
        for pos in self.end_points.positions:
            self._add_block(1, 1, pos, self.field_type["end_point"])

    def _can_put_end_point(self, pos: Position) -> bool:
        if self._find_rack(pos) is None and self._in_world(pos):
            return True
        return False

    def _reset_tasks(self) -> None:
        tasks: list[Task] = []
        items = deepcopy(self.items)
        for item_id, target_pos, amount in self.picking_list:
            store_point = self.store_points[Position(*target_pos)]
            for _ in range(amount):
                item = items.pop(item_id)
                assert item is not None, f"item is None. item_id: {item_id}"
                tasks.append(Task(item, store_point))
        self.tasks = Tasks(tasks)

    def _reset_racks(self) -> None:
        self.racks.reset()

    def create_plain_map(self) -> None:
        self.plain_map = self.world_map.copy()

    def _in_world(self, pos: Position) -> bool:
        return 0 <= pos.col < self.map_width and 0 <= pos.row < self.map_height

    def _add_block(
        self, width: Length, height: Length, pos: Position, val: int
    ) -> None:
        block = np.full((height, width), val, dtype=int)
        self.world_map[pos.row : pos.row + height, pos.col : pos.col + width] = block

    def _add_rack(
        self,
        width: Length,
        height: Length,
        pos: PreconversionPosition,
        pick_direction: PickDirection = "horizontal",
    ) -> None:
        self._add_block(width, height, Position(*pos), self.field_type["rack"])
        self.racks.append(
            Rack(
                pos=Position(*pos),
                width=width,
                height=height,
                pick_direction=pick_direction,
            )
        )

    def _add_item(
        self,
        pos: PreconversionPosition,
        amount: Amount,
        volume: Volume = 1,
        name: Name = "",
    ) -> None:
        self._add_block(1, 1, Position(*pos), self.field_type["item"])
        self._add_item_object(
            name=name, amount=amount, pos=Position(*pos), volume=volume
        )

    def _add_store_point_object(
        self, pos: Position, pick_direction: PickDirection = "horizontal"
    ) -> StorePoint:
        store_point = self._find_store_point(pos)
        if store_point is None:
            store_point = StorePoint(pos=pos, pick_direction=pick_direction)
            self.store_points.append(store_point)
        return store_point

    def _add_item_object(
        self, pos: Position, amount: Amount, volume: Volume = 1, name: Name = ""
    ) -> None:
        current_owner = self._create_store_point(pos)

        item = Item(
            name=name,
            pos=pos,
            volume=volume,
            current_owner=current_owner,
        )
        item_set = ItemSet(item, amount)
        current_owner.having_items.append(item_set)
        self.items.append(item_set)

    def _add_agent(
        self, name: Name, pos: PreconversionPosition, capacity: int = 5
    ) -> None:

        self._add_block(1, 1, Position(*pos), self.field_type["agent"])
        self.agents.append(Agent(name=name, pos=Position(*pos), capacity=capacity))

    def _create_store_point(self, pos: Position) -> StorePoint:
        rack = self._find_rack(pos)
        if rack:
            pick_direction = rack.pick_direction
        else:
            pick_direction = "on"
        store_point = self._find_store_point(pos)
        if not store_point:
            store_point = self._add_store_point_object(
                pos=pos, pick_direction=pick_direction
            )
        return store_point

    def _find_store_point(self, pos: Position) -> StorePoint | None:
        for sp in self.store_points:
            if np.array_equal(sp.pos, pos):  # type: ignore
                return sp
        return None

    def _find_rack(self, pos: Position) -> Rack | None:
        for r in self.racks:
            assert r.pos is not None, "rack's pos is None"
            if (
                r.pos.row <= pos.row < r.pos.row + r.height
                and r.pos.col <= pos.col < r.pos.col + r.width
            ):
                return r
        return None
