# Isaac Lab engineering practices

## Compatibility and structure

- Maintain an explicit matrix for Isaac Lab, Isaac Sim, Python, PyTorch/RL
  library, CUDA/GPU driver, OS/container, and asset versions. Do not combine
  examples from incompatible documentation branches.
- Choose manager-based environments for configurable reusable term pipelines
  and direct environments for intentionally custom control; do not mix both
  styles without an ownership reason.
- Separate environment/task definition, scene/assets, agent/training config,
  evaluation, scripts/entrypoints, checkpoints, and result artifacts.

## Task and experiment contract

- Specify observation meaning/shape/frame/range/history/noise, action meaning/
  scale/limits/control rate, reward terms/scales, termination vs truncation,
  reset distribution, event/randomization timing, and curriculum transitions.
- Keep physics step, decimation/control frequency, render/sensor rate, and
  episode time semantics consistent. Record units and coordinate frames.
- Validate randomization distributions and bounds; separate training
  randomization from evaluation scenarios. Treat sim-to-real assumptions as
  QAS with measurable validation, not a slogan.
- Record seeds for framework/environment/library, but report nondeterministic
  GPU/physics behavior honestly. Pin datasets/assets/config and checkpoint plus
  code revision for every material result.

## Training, evaluation, and verification

- Separate training and evaluation entrypoints/configuration. Define baseline,
  metric aggregation, success/failure distribution, evaluation seeds/scenarios,
  checkpoint selection, and stopping criteria before comparing agents.
- Bound vectorized environment memory, GPU utilization, logging, checkpoint,
  and artifact retention. Headless/container/HPC execution is a separate
  deployment profile with license, device, mount, and output ownership.
- Verify import/startup, small headless environment smoke, observation/action
  shape/range, reset/termination, reward sanity, short train step, checkpoint
  save/resume, fixed evaluation, performance/memory, and documented
  reproducibility limitations.
- Reject reward terms with hidden units, evaluation on training-only scenarios,
  cherry-picked seeds, unversioned assets/config, silent NaNs, and claims based
  only on one learning curve.

Primary sources: the exact Isaac Lab release documentation/reference
architecture, compatible Isaac Sim documentation, selected RL library docs, and
project experiment policy.
