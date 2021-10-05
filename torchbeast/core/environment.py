# Copyright (c) Facebook, Inc. and its affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""The environment class for MonoBeast."""

import torch
import numpy as np

def _format_frame(frame):
    frame = torch.from_numpy(frame)
    return frame.view((1, 1) + frame.shape)  # (...) -> (T,B,...).

def _format_VKB(vkb):
    # only one arity
    vkb = np.array(vkb)
    vkb = torch.from_numpy(vkb)
    return vkb.view((1, 1) + vkb.shape)  # (...) -> (T,B,...).

class Environment:
    def __init__(self, gym_env, obs_type):
        """
        :param gym_env:
        :param obs_type: image, KB or VKB
        """
        self.gym_env = gym_env
        self.episode_return = None
        self.episode_step = None
        self.obs_type = obs_type
        if obs_type == "image":
            self.obs_shape = gym_env.observation_space.shape
        elif obs_type in ["VKB", "absVKB"]:
            self.obs_shape = self.gym_env.obs_shape

    def initial(self):
        initial_reward = torch.zeros(1, 1)
        # This supports only single-tensor actions ATM.
        initial_last_action = torch.zeros(1, 1, dtype=torch.int64)
        self.episode_return = torch.zeros(1, 1)
        self.episode_step = torch.zeros(1, 1, dtype=torch.int32)
        initial_done = torch.ones(1, 1, dtype=torch.uint8)
        obs = self.gym_env.reset()
        result = dict(
                reward=initial_reward,
                done=initial_done,
                episode_return=self.episode_return,
                episode_step=self.episode_step,
                last_action=initial_last_action,
            )
        if self.gym_env.__module__ == 'minihack.envs.corridor' or self.gym_env.env_type == "minihack":  # TODO is dimensionality a problem here?
            frame = _format_frame(obs["glyphs_crop"])
        else:
            frame = _format_frame(obs["image"])
        result["frame"] = frame
        if self.obs_type == "image":
            if "direction" in obs:
                result["direction"] = _format_VKB(obs["direction"])

        if "VKB" in obs:
            nullary_tensor, unary_tensor, binary_tensor = obs["VKB"]
            result["nullary_tensor"] = _format_VKB(nullary_tensor)
            result["unary_tensor"] = _format_VKB(unary_tensor)
            result["binary_tensor"] = _format_VKB(binary_tensor)
        return result

    def step(self, action):
        obs, reward, done, unused_info = self.gym_env.step(action)
        self.episode_step += 1
        self.episode_return += reward
        episode_step = self.episode_step
        episode_return = self.episode_return
        if done:
            obs = self.gym_env.reset()
            self.episode_return = torch.zeros(1, 1)
            self.episode_step = torch.zeros(1, 1, dtype=torch.int32)

        reward = torch.tensor(reward).view(1, 1)
        done = torch.tensor(done).view(1, 1)
        result = dict(
                reward=reward,
                done=done,
                episode_return=episode_return,
                episode_step=episode_step,
                last_action=action,
            )
        if self.gym_env.env_type == "minihack":  # TODO is dimensionality a problem here?
            frame = _format_frame(obs["glyphs_crop"])
        else:
            frame = _format_frame(obs["image"])
        result["frame"] = frame
        if self.obs_type == "image":
            if "direction" in obs:
                result["direction"] = _format_VKB(obs["direction"])

        if "VKB" in obs:
            nullary_tensor, unary_tensor, binary_tensor = obs["VKB"]
            result["nullary_tensor"] = _format_VKB(nullary_tensor)
            result["unary_tensor"] = _format_VKB(unary_tensor)
            result["binary_tensor"] = _format_VKB(binary_tensor)
        return result

    def close(self):
        self.gym_env.close()
