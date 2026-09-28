---
name: ml-systems-optimization
description: Training systems profiling, dataloader bottleneck elimination, deployment constraints, hyperparameter search strategy, checkpoint lifecycle, and experiment reproducibility.
---

# ML Systems, Runtime Optimization & Experiment Provenance

> Discipline for hardware profiling, eliminating dataloader and system bottlenecks, optimizing models under deployment constraints, hyperparameter search efficiency, and reproducibility.

---

## 1. Runtime & Systems Monitoring

Decompose each training step into its constituent timing components:
$$T_{\text{step}} = T_{\text{data}} + T_{\text{forward}} + T_{\text{backward}} + T_{\text{optimizer}}$$

Continuously monitor and log:
- **Throughput**: Samples/sec or tokens/sec across training epochs.
- **GPU & CPU Utilization**: Track GPU compute engine activity, VRAM allocation, and CPU load.
- **Component Breakdown**:
  - `T_data`: Time spent waiting for `DataLoader` batches.
  - `T_forward`: Model forward pass compute time.
  - `T_backward`: Gradient backpropagation compute time.
  - `T_optimizer`: Optimizer update and gradient reduction latency.
  - Host-to-device memory transfer overhead and CUDA synchronization stalls.

### Diagnosing Low GPU Utilization:
If GPU utilization is low ($< 60\%$), do not alter model architecture. Isolate data pipeline bottlenecks:
1. Increase `num_workers` in `DataLoader` (typically $2 \times \text{CPU cores}$ per GPU).
2. Set `pin_memory=True` for pinned host-to-device memory copies.
3. Pre-fetch batches (`prefetch_factor=2`).
4. Shift heavy pre-processing (resizing, tokenization, spectrograms) offline or to batched GPU kernels.
5. Increase batch size or use gradient accumulation.

---

## 2. Deployment Constraints & Constrained Optimization

In production, models must operate within hard resource budgets. Treat model development as constrained optimization:
$$\max_{\theta} \text{Quality}(\theta) \quad \text{subject to} \quad \text{Latency} \le L_{\max},\; \text{Memory} \le M_{\max},\; \text{Size} \le S_{\max}$$

Jointly track and benchmark:
- **Model Size on Disk**: Uncompressed and compressed parameter footprint.
- **Peak RAM / VRAM**: Memory consumption during peak inference batch sizes.
- **Latency**: Measure p50, p95, and p99 inference latency on the target hardware.
- **Throughput**: Maximum queries per second (QPS) under batched requests.
- **Energy / Compute Budget**: Wattage and FLOPs for edge or battery-powered devices.

Never optimize validation accuracy in isolation when hard latency or memory boundaries exist.

---

## 3. Disciplined Hyperparameter Search

Do not launch broad, unconstrained random or grid sweeps before establishing a working baseline configuration.

### Search Protocol:
1. **Establish Reasonable Baseline Bounds**:
   - Learning rate (bracket with a learning rate range test).
   - Batch size (largest power-of-two that fits comfortably in VRAM).
   - Weight decay ($10^{-4}$ to $10^{-1}$ for AdamW).
   - Scheduler (cosine annealing with 5–10% warmup).
2. **Search Only High-Impact Variables**: Focus tuning on learning rate, loss scale/temperature, and architecture depth/width.
3. **Early Pruning**: Terminate clearly stagnant or underperforming trials early (e.g. via Optuna Hyperband / Median pruners) after $15\text{--}20\%$ of training budget.
4. **Mandatory Smoke Test**: Every hyperparameter configuration must pass the smoke test before execution.

---

## 4. Checkpoint Lifecycle & Trajectory Tracking

Never rely solely on saving weights from the final training epoch.

Maintain:
- **Latest Checkpoint**: Enables seamless recovery from spot-instance interruptions or unexpected crashes.
- **Best Validation Loss Checkpoint**: Weights corresponding to the lowest evaluation loss.
- **Best Primary Task Metric Checkpoint**: Weights corresponding to the peak application metric (e.g. highest F1, lowest WER, highest Recall@1).
- **Periodic Trajectory Checkpoints**: For long-duration runs, preserve checkpoints at regular intervals to analyze representation trajectories and delayed generalization (grokking).

---

## 5. Experiment Provenance & Reproducibility

Every experimental result must be reproducible and trace back to its origin.

Record in metadata / logs:
- **Random Seeds**: PyTorch, NumPy, and Python standard library random seeds (`torch.manual_seed`, `np.random.seed`).
- **Data & Preprocessing Versions**: Dataset commit hash, split hash, and preprocessing pipeline version.
- **Code State**: Git commit hash, dirty flag status, and configuration files.
- **Environment & Hardware**: PyTorch version, CUDA version, OS, GPU model, and driver version.
- **Training Hyperparameters**: Peak learning rate, optimizer parameters, batch size, gradient accumulation steps, precision (FP32, FP16, BF16), and total duration.
