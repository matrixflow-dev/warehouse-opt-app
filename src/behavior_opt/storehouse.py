import functools
import sys
from typing import Literal, Optional, TypeAlias

import gym
import gym.spaces
import numpy as np
from gym.error import DependencyNotInstalled
from gym.utils import seeding
from pettingzoo import AECEnv
from pettingzoo.utils import agent_selector, wrappers
from pettingzoo.utils.conversions import parallel_wrapper_fn

# from .create_world_map import create_world_map
from behavior_opt.sh_core import ACTIONS, Agent, Direction, Item, Position, World
from behavior_opt.sh_core.store_point import StorePoint

# Type Definitions
RenderMode: TypeAlias = Literal["human", "ascii", "rgb_array"]


def env(**kwargs):
    env = raw_env(**kwargs)
    env = wrappers.CaptureStdoutWrapper(env)
    # env = wrappers.TerminateIllegalWrapper(env, illegal_reward=-50)
    env = wrappers.OrderEnforcingWrapper(env)
    return env


parallel_env = parallel_wrapper_fn(env)


class raw_env(AECEnv):
    metadata = {
        "render_modes": ["human", "rgb_array", "ansi"],
        "render_fps": 120,
    }
    masked = False

    CUI_RENDER_TYPE = {
        0: "\033[0m" + " " + "\033[0m",
        1: "\033[0m" + "█" + "\033[0m",
        2: "\033[44m" + "S" + "\033[0m",
        3: "\033[41m" + "G" + "\033[0m",
        4: "\033[43m" + "A" + "\033[0m",
        5: "\033[42m" + "I" + "\033[0m",
        6: "\033[0m" + "'" + "\033[0m",
    }

    def __init__(
        self,
        world: World,
        output_list: Optional[list],
        render_mode: Optional[RenderMode] = None,
        max_cycles=10000,
        mode="auto_move",
    ):
        super().__init__()
        self.seed()
        self.max_cycles = max_cycles
        self.world = world
        self.MAP = self.world.world_map
        self.display_map = self.MAP.copy()
        self.nrow, self.ncol = self.MAP.shape

        self.render_modes = ["human", "rgb_array", "ansi"]
        self.render_mode = render_mode
        # pygameの設定
        pixel_size = 800 // max(self.nrow, self.ncol)
        self.window_size = (
            self.ncol * pixel_size + 20,
            self.nrow * pixel_size + 20,
        )
        self.window = None
        self.clock = None

        # pygletの設定
        self.renderer = None
        # multi-agent
        self.n_agents = len(self.world.agents)
        self.agents = [a.name for a in self.world.agents]
        self.possible_agents = self.agents[:]

        # all-agent
        self.mode = mode

        # set spaces
        self.action_spaces = {
            a.name: gym.spaces.Discrete(len(ACTIONS) + 1) for a in self.world.agents
        }
        # obsevationをMAP+agent.pos(size:2)+agent.capacity(size:1)+agent.volume(size:1)にする
        self.observation_spaces = {
            a.name: gym.spaces.Box(
                low=0,
                high=self.MAP.shape[0],
                shape=(self.MAP.size + 4,),
                dtype=int,
            )
            for a in self.world.agents
        }
        self.output_list = output_list
        self.routes = {a.name: [] for a in self.world.agents}
        # set agent selector
        self._agent_selector = agent_selector(self.agents)
        self.agent_selection = self._agent_selector.reset()
        self.reset()

    @functools.lru_cache(maxsize=None)
    def observation_space(self, agent):
        return self.observation_spaces[agent]

    @functools.lru_cache(maxsize=None)
    def action_space(self, agent):
        return self.action_spaces[agent]

    def reset(self, seed=None, return_info=False, options=None):
        if seed is not None:
            self.seed(seed=seed)
        # 倉庫内を初期化
        self.world.reset()
        self.MAP = self.world.world_map
        self.n_flags = len(self.world.tasks)
        self.steps = 0

        if self.output_list is not None:
            for i, agent in enumerate(self.world.agents):
                agent.output_list = self.output_list[i]
        # pettingzooで必要な要素を初期化する
        self.agents = self.possible_agents[:]
        self.rewards = {agent_name: 0 for agent_name in self.agents}
        self._cumulative_rewards = {agent_name: 0 for agent_name in self.agents}
        self.dones = {agent_name: False for agent_name in self.agents}
        self.infos = {agent_name: {} for agent_name in self.agents}
        self.actions = {agent_name: {} for agent_name in self.agents}

        self._agent_selector.reinit(self.agents)
        self._agent_selector.reset()
        self.agent_selection = self._agent_selector.reset()

    def in_pos_list(self, pos_list, pos):
        if not pos_list:
            return []
        return list(*np.where((pos_list == np.array(pos)).all(axis=1)))

    def move_agent(self, agent: Agent, action: int):
        if agent.output_list:
            if not agent.output_list["path"]:
                return
            agent.pos = agent.output_list["path"].popleft()
            pickup_list = agent.output_list["pick_up"].popleft()
            if pickup_list != [""]:
                for pickup in pickup_list:
                    item_set = self.world.items[pickup]
                    self.pickup_item(agent, item_set.item)
            dropoff_list = agent.output_list["drop_off"].popleft()
            if dropoff_list != [""]:
                for dropoff in dropoff_list:
                    item_set = self.world.items[dropoff]
                    self.dropoff_item(agent, item_set.item)
        else:
            next_pos = (
                agent.pos[0] + ACTIONS[action][0],
                agent.pos[1] + ACTIONS[action][1],
            )
            if self.is_movable(next_pos):
                agent.pos = next_pos
                agent.direction = Direction(action)

    def pickup_item(self, agent: Agent, item: Item):
        self.world.picking(agent, item)

    def dropoff_item(self, agent: Agent, item: Item):
        self.world.dropping(agent, item)
        self.n_flags -= 1

    def step(self, action: Optional[int]):
        """一つのエージェントを１ステップ進める

        Args:
            action (Optional[int]): エージェントの行動(0~3)

        """
        # エージェントが終了してるか判定
        if self.dones[self.agent_selection]:
            self._was_done_step(action)
            if len(self.agents) > 0:
                self.agent_selection = self._agent_selector.next()
            return

        self._cumulative_rewards[self.agent_selection] = 0
        agent = self.world.agents[self.agent_selection]
        self.move_agent(agent, action)
        # 最後のエージェントの時にrewardとdoneを更新する
        if self._agent_selector.is_last():
            for agent_name in self.agents:
                agent = self.world.agents[agent_name]
                self.rewards[agent_name] = self.get_reward(agent)
                done = self.is_done(agent)
            self.dones = {agent_name: done for agent_name in self.agents}
            self.steps += 1
        else:
            self._clear_rewards()

        if len(self.agents) > 0:
            self.agent_selection = self._agent_selector.next()
        self._accumulate_rewards()

    def get_reward(self, agent: Agent):
        reward = 0
        if agent.goal == agent.pos and self.n_flags == 0:
            reward += 100
        else:
            reward -= 1

        return reward

    def is_movable(self, pos: Position):
        # マップの中にいるか、歩けない場所にいないか
        map_condition = (
            0 <= pos[0] < self.MAP.shape[0]
            and 0 <= pos[1] < self.MAP.shape[1]
            and self.MAP[tuple(pos)] != self.world.field_type["rack"]
            and self.MAP[tuple(pos)] != self.world.field_type["item"]
        )
        return map_condition

    def observe(self, agent_id: str):
        self.display_map = self.MAP.copy()
        for world_agent in self.world.agents:
            self.display_map[tuple(world_agent.pos)] = self.world.field_type["agent"]
        agent = self.world.agents[agent_id]
        flat_map = self.display_map.flatten()
        observation = np.concatenate(
            [flat_map, agent.pos, [agent.capacity, agent.volume]]
        )
        # return observation
        return observation

    def is_done(self, agent: Agent) -> bool:
        if (
            np.array_equal(agent.pos, agent.goal.pos)
            and self.n_flags == 0
            and agent.volume == 0
            or (len(agent.output_list["path"]) == 0)
        ):
            return True
        else:
            return False

    # render
    def render(self, mode: RenderMode = "human"):
        if self.render_mode is not None:
            return self.renderer.get_renders()
        else:
            return self._render(mode)

    def _render(self, mode: RenderMode = "human"):
        assert mode in self.metadata["render_modes"]
        if mode == "ansi":
            return self._render_cui()
        elif mode in {"human", "rgb_array", "single_rgb_array"}:
            return self._render_gui(mode)

    def _render_cui(self):
        outfile = sys.stdout
        outfile.write(
            "\n".join(
                " ".join(
                    (
                        (
                            self.CUI_RENDER_TYPE[elem]
                            if elem < 7
                            else self.CUI_RENDER_TYPE[6]
                        )
                        for elem in row
                    )
                )
                for row in self.display_map
            )
            + "\n\n"
        )
        return outfile

    def _render_gui(self, mode):
        try:
            import pygame  # dependency to pygame only if rendering with human
        except ImportError:
            raise DependencyNotInstalled(
                "pygame is not installed, run `pip install gym[toy_text]`"
            )
        if self.window is None:
            pygame.init()
            pygame.display.set_caption("StoreHouse")
            if mode == "human":
                self.window = pygame.display.set_mode(self.window_size)
            else:  # "rgb_array"
                self.window = pygame.Surface(self.window_size)

        if self.clock is None:
            self.clock = pygame.time.Clock()
        x_size, y_size = (
            self.window_size[0] // self.ncol,
            self.window_size[1] // self.nrow,
        )
        size = min(x_size, y_size)
        self.window.fill("white")
        for y_i, row in enumerate(self.display_map):  # 縦に10pxずつ線を引く
            for x_i, elem in enumerate(row):
                if elem == self.world.field_type["rack"]:
                    pygame.draw.rect(
                        self.window,
                        "gray",
                        (10 + x_i * size, 10 + y_i * size, size, size),
                    )

        for store_point in self.world.store_points:
            pygame.draw.rect(
                self.window,
                "gray50",
                (
                    10 + store_point.pos[1] * size,
                    10 + store_point.pos[0] * size,
                    size,
                    size,
                ),
            )
        for task in self.world.tasks:
            ship_point = task.target_store_point
            pygame.draw.rect(
                self.window,
                "green2",
                (
                    10 + ship_point.pos[1] * size,
                    10 + ship_point.pos[0] * size,
                    size,
                    size,
                ),
            )
            item: Item = task.item

            pygame.draw.rect(
                self.window,
                "yellow2",
                (
                    10 + item.pos[1] * size,
                    10 + item.pos[0] * size,
                    size,
                    size,
                ),
            )
        for store_point in self.world.store_points:
            if store_point.is_picked:
                pygame.draw.rect(
                    self.window,
                    "blue2",
                    (
                        10 + store_point.pos[1] * size,
                        10 + store_point.pos[0] * size,
                        size,
                        size,
                    ),
                )

        for agent in self.world.agents:
            pygame.draw.circle(
                self.window,
                "red2",
                (
                    10 + agent.pos[1] * size + size // 2,
                    10 + agent.pos[0] * size + size // 2,
                ),
                size * 0.8,
            )
            self.routes[agent.name].append(agent.pos)
        for route in self.routes.values():
            for i in range(len(route) - 1):
                pygame.draw.line(
                    self.window,
                    "red",
                    (
                        10 + route[i][1] * size + size // 2,
                        10 + route[i][0] * size + size // 2,
                    ),
                    (
                        10 + route[i + 1][1] * size + size // 2,
                        10 + route[i + 1][0] * size + size // 2,
                    ),
                    1,
                )
        # font = pygame.font.Font(None, 30)
        # for i, agent in enumerate(self.world.agents):
        #     agent_cap_text = font.render(
        #         f"{agent.volume: >3}/{agent.capacity: >3}", True, "black"
        #     )
        #     self.window.blit(agent_cap_text, (15 + i * 80, self.window_size[1] - 25))
        # step_text = font.render(f"steps:{self.steps}", True, "black")
        # self.window.blit(
        #     step_text, (self.window_size[0] - 150, self.window_size[1] - 25)
        # )
        if mode == "human":
            pygame.event.pump()
            pygame.display.update()
            self.clock.tick(self.metadata["render_fps"])
        else:  # rgb_array
            return np.transpose(
                np.array(pygame.surfarray.pixels3d(self.window)), axes=(1, 0, 2)
            )

    def close(self):
        if self.window is not None:
            import pygame

            pygame.display.quit()
            pygame.quit()
        if self.renderer:
            self.renderer.close()

    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
