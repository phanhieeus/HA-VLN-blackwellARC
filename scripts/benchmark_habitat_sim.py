#!/usr/bin/env python3
"""Measure Habitat-Sim 0.1.7 RGB-D step latency on a supplied GLB scene."""
import argparse
import platform
import importlib.metadata
import statistics
import time

import numpy as np
import torch
import habitat_sim


def make_config(scene, width, height):
    sim_cfg = habitat_sim.SimulatorConfiguration()
    sim_cfg.scene_id = scene
    sim_cfg.enable_physics = False
    sim_cfg.gpu_device_id = 0

    agent_cfg = habitat_sim.AgentConfiguration()
    sensors = []
    for uuid, sensor_type in (("rgb", habitat_sim.SensorType.COLOR), ("depth", habitat_sim.SensorType.DEPTH)):
        spec = habitat_sim.SensorSpec()
        spec.uuid = uuid
        spec.sensor_type = sensor_type
        spec.resolution = [height, width]
        spec.position = [0.0, 1.5, 0.0]
        sensors.append(spec)
    agent_cfg.sensor_specifications = sensors
    return habitat_sim.Configuration(sim_cfg, [agent_cfg])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", required=True, help="Path to a Matterport/Habitat GLB scene")
    parser.add_argument("--width", type=int, default=224)
    parser.add_argument("--height", type=int, default=224)
    parser.add_argument("--warmup", type=int, default=20)
    parser.add_argument("--steps", type=int, default=200)
    args = parser.parse_args()
    if args.steps < 1 or args.warmup < 0:
        parser.error("--steps must be positive and --warmup non-negative")

    config = make_config(args.scene, args.width, args.height)
    latencies_ms = []
    with habitat_sim.Simulator(config) as sim:
        sim.initialize_agent(0)
        for _ in range(args.warmup):
            sim.step("turn_left")
        for _ in range(args.steps):
            start = time.perf_counter()
            observations = sim.step("turn_left")
            latencies_ms.append((time.perf_counter() - start) * 1000)
            if not {"rgb", "depth"}.issubset(observations):
                raise RuntimeError(f"Expected RGB-D observations, got {list(observations)}")
    values = np.asarray(latencies_ms)
    print(f"Python: {platform.python_version()} | PyTorch: {torch.__version__} | CUDA: {torch.version.cuda}")
    print(f"GPU: {torch.cuda.get_device_name(0)} | Habitat-Sim: {importlib.metadata.version('habitat-sim')}")
    print(f"Scene: {args.scene} | resolution: {args.width}x{args.height} RGB-D | warmup: {args.warmup} | steps: {args.steps}")
    print(f"step latency ms: median={np.median(values):.4f} p95={np.percentile(values, 95):.4f} mean={statistics.mean(values):.4f}")
    print(f"throughput: {1000.0 / statistics.mean(values):.1f} steps/s")


if __name__ == "__main__":
    main()
