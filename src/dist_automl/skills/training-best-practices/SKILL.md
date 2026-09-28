---
name: training_best_practices
description: General-purpose ML training discipline for agents. Enforces problem formalization, feasibility checks, baselines, 5 mandatory validation stages, TensorBoard telemetry, live stop/diagnose/retry rules, automatic diagnosis matrix, diagnostic hierarchy, required final report, and non-negotiable agent rules.
---

# Training Best Practices & Core Discipline

## 1. Mission

Train models scientifically and efficiently. Do not behave like a blind model-sweeper.

The default loop is:
> Understand task -> formalize objective -> validate data/splits -> check mathematical feasibility -> choose justified architecture -> smoke test -> tiny-set test -> short diagnostic run -> full training -> monitor continuously -> diagnose -> stop or continue -> targeted retry -> final evaluation.

Every expensive run must answer a question. Never train multiple architectures merely because they are popular. Optimize the actual application objective under compute, memory, latency, parameter-count, and throughput constraints.

---

## 2. First Formalize the Problem

Before training, identify:
- Input modality and shape.
- Target and output structure.
- Prediction type: classification, multilabel, regression, ranking, retrieval, detection, segmentation, forecasting, generation.
- Dataset size and label distribution.
- Sequence / temporal / group structure.
- Expected deployment distribution.
- Train / validation / test methodology.
- Latency, memory, parameter, throughput, and hardware constraints.

Write the mathematical mapping:
- **Classification**: $f_\theta(x) \to p(y|x)$
- **Regression**: $f_\theta(x) \to \hat{y} \in \mathbb{R}^d$
- **Retrieval**: $q \to z_q,\; x \to z_x,\; s(q,x) = \text{sim}(z_q, z_x)$
- **Forecasting**: $f_\theta(x_{t-k:t}) \to \hat{y}_{t+1:t+h}$
- **Detection**: $x \to \{(\text{box}_i, \text{class}_i, \text{score}_i)\}$
- **Segmentation**: $x \to \text{pixel/voxel labels}$

If the task cannot be expressed clearly, do not launch expensive training.

---

## 3. Feasibility Gate — Before Any Expensive Training

### 3.1 Architecture Compatibility
Reject candidates that cannot naturally represent the required mapping:
- Context / receptive field is sufficient for the task.
- Output representation matches the target.
- Sequence order is preserved when needed; causality is respected when required.
- Variable-length inputs are handled correctly without illegal truncations.
- Multilabel targets are not accidentally treated as single-label softmax.
- Continuous targets are not treated as classification.
- Retrieval objectives are not used when calibrated probabilities are required without an explicit calibration strategy.
- Architecture does not discard information required by the task.

### 3.2 Mathematical Impossibility / Identifiability
- Ask whether the information needed for the target exists in the input.
- If identical inputs have contradictory labels, perfect deterministic prediction is mathematically impossible.
- If deployment requires unseen conditions absent from training, changing architecture alone cannot manufacture missing information.
- If future information leaks into a causal task, fix the data pipeline rather than tuning the model.

### 3.3 Compute Feasibility
Estimate: parameter count, trainable parameter count, activation memory, optimizer-state memory, batch memory, approximate FLOPs, expected training time, inference latency, and peak memory. Reject models that violate hard constraints.

---

## 4. Baseline First

Establish a cheap baseline before an expensive architecture:
- Majority class / constant prediction
- Linear / logistic regression
- Small MLP or shallow tree
- Nearest-neighbor or simple heuristic
- Simple CNN / fast retrieval benchmark

A baseline tells the agent whether usable signal exists and whether additional model complexity is empirically justified.

---

## 5. Mandatory Training Stages

Never launch a long, expensive run directly. Progress through all stages:

### Stage 1 — Smoke Test (1-2 Batches)
Verify end-to-end functionality: forward pass, loss calculation, backward pass, gradients, optimizer step, metrics logging, checkpoint saving, TensorBoard writing, and mixed precision.

### Stage 2 — Tiny-Set Overfit Test (16–64 Samples)
Train on a small, fixed subset with no regularizers or augmentations. If the model cannot memorize 16–64 samples to near-zero loss, inspect:
`data -> labels -> preprocessing -> forward -> loss -> gradients -> optimizer -> frozen parameters -> architecture`
Do not launch full runs until this passes.

### Stage 3 — Short Diagnostic Run (2–5 Epochs)
Train long enough to observe early dynamics: loss trajectory, task metric, validation behavior, gradient norms, learning rate, memory, throughput, and sample predictions.

### Stage 4 — Full Run
Execute full training only after stages 1–3 pass cleanly.

### Stage 5 — Targeted Experiments
Change the smallest number of variables necessary to test an explicit hypothesis.

---

## 6. Universal TensorBoard Dashboard

Log the following telemetry for every serious run:

- **Optimization**:
  - `loss/train`, `loss/val`
  - `optimization/learning_rate`, `optimization/gradient_norm`
  - `optimization/update_norm`, `optimization/update_to_weight_ratio`
  - global parameter norm, layer-wise gradient and weight norms
- **Generalization**:
  - Primary train metric and primary validation metric
  - Task-specific robustness metrics and important data-slice metrics
- **Runtime**:
  - Step time, samples/sec or tokens/sec, GPU utilization, GPU memory, dataloader time, forward time, backward time, optimizer time
- **Distributions (Histograms)**:
  - Per-example loss, gradients, activations, weights, embeddings, and prediction scores

---

## 7. Core Graph Interpretation

- **Train Loss vs. Validation Loss**:
  - *Train down + Val down*: Useful learning is occurring.
  - *Train down + Val flat*: Investigate generalization, distribution mismatch, objective mismatch, or capacity.
  - *Train down + Val up*: Overfitting, data leakage, or train/val distribution shift.
  - *Both poor*: Investigate data, objective, optimization, and architecture before scaling.
- **Gradient Norm**:
  - Monitor $\|\nabla L\|$. Use a log y-axis.
  - Large unstable gradients indicate excessive LR, bad conditioning, unstable numerics, or architecture bugs.
  - Tiny gradients indicate convergence, saturation, dead activations, or a disconnected computation graph.
- **Update-to-Weight Ratio**:
  - Monitor $\|\theta_{t+1} - \theta_t\| / (\|\theta_t\| + \epsilon)$.
  - Ratio $> 10^{-1}$: Overly aggressive updates, risking instability.
  - Ratio $< 10^{-5}$: Parameters are barely moving.
- **Learning Rate**: Always log LR. Distinguish whether a training transition was caused by a scheduler step or model dynamics.

---

## 8. Live Stop / Diagnose / Retry Rules

Do not blindly burn compute on failing runs.

### Stop Immediately:
- Loss becomes NaN / Inf.
- Gradients or parameters contain NaN / Inf.
- Clear numerical divergence or exploding gradients.
- Broken labels or preprocessing discovered.
- Data leakage discovered.
- Architecture is incompatible with the task.
- Metric calculation code is buggy.

### Stop After Reasonable Warmup:
- Training loss is effectively unchanged.
- Primary task metric is unchanged.
- Gradients are healthy but parameter updates are negligible.
- Gradients are zero throughout a supposedly trainable module.
- Model capacity / context is demonstrably insufficient.
- The run is dominated by a known bottleneck that cannot be resolved by continuing.

### Retry Protocol:
1. Stop the run.
2. Classify the likely failure: data, split, objective, optimization, architecture, generalization, or infrastructure.
3. Inspect discriminating graphs.
4. Change the smallest necessary set of variables to test the fix.
5. Run a short diagnostic retry before allocating a larger compute budget.

---

## 9. Automatic Diagnosis Matrix

| Observation | First Investigations & Interventions |
| :--- | :--- |
| **NaN / Inf** | Input data anomalies, excessive LR, mixed precision underflow/overflow, numerically unstable loss. |
| **Loss explodes** | Excessive LR, unscaled gradients, missing gradient clipping, bad weight initialization. |
| **Loss constant** | Target labels detached, loss function mismatch, frozen parameters, zero gradients, LR too small. |
| **Train loss slow** | Insufficient LR, bad loss conditioning, inadequate model capacity, data bottleneck. |
| **Loss drops, Metric stalls** | Objective/metric misalignment (e.g. cross-entropy drops from calibration without changing rank order). |
| **Train strong, Val poor** | Overfitting, data leakage, split contamination, train/val distribution shift. |
| **Both Train & Val poor** | Corrupted data, wrong objective, optimization failure, inadequate architecture. |
| **High accuracy, poor minority recall** | Severe class imbalance, threshold uncalibrated, unweighted loss, random sampling. |
| **Retrieval loss good, Recall@K poor** | Ineffective negative mining, embedding collapse, loss/metric mismatch. |
| **Embeddings collapse** | Objective temperature, normalization missing, feature collapse in inputs. |
| **Hard negatives remain strong** | Ambiguous ground truth labels, mining false negatives, insufficient representation capacity. |
| **GPU underutilized** | DataLoader bottlenecks, slow CPU preprocessing, missing pinned memory, small batch size. |
| **Latency too high** | Sequence length, model architecture, lack of kernel fusion, missing quantization. |
| **Memory too high** | Activation caching, large batch size, missing mixed precision, gradient checkpointing needed. |
| **Model too large** | Architecture redesign, knowledge distillation, pruning, post-training quantization. |
| **Validation changes suddenly** | Learning rate scheduler transition, checkpoint reload, data corruption, evaluation distribution shift. |

---

## 10. Universal Diagnostic Hierarchy

When training behaves unexpectedly, investigate in this strict sequence:
`Data -> Labels -> Split -> Objective -> Forward pass -> Gradients -> Optimizer -> Architecture -> Regularization -> Scaling`

Never modify the architecture when the underlying fault is in the data, labels, or loss function.

---

## 11. Required Final Training Report

Document for every production model:
- **Dataset**: Sizes, split methodology, class/target distributions, leakage checks, important slices.
- **Model**: Architecture name, total parameter count, trainable parameter count, input/output shapes, compute estimates.
- **Optimization**: Optimizer, peak LR, scheduler, batch size, gradient accumulation, weight decay, precision, clipping.
- **Curves**: Train loss, validation loss, primary train metric, validation task metric, LR, gradient norms, update/weight ratio.
- **Generalization**: Validation/test metrics, important slice performances, out-of-distribution robustness results.
- **Deployment**: Model size on disk, latency (p50, p95, p99), throughput, peak memory.
- **Diagnosis**: Explicitly state what worked, what failed, supporting evidence, what was changed, and future directions.

---

## 12. Non-Negotiable Agent Rules

1. Never train before understanding the task and formalizing the objective.
2. Never use training loss as the sole success criterion.
3. Never launch a long run before a smoke test passes.
4. Use a tiny-set overfit test when theoretically appropriate.
5. Reject mathematically incompatible architectures before training.
6. Stop clearly failed runs early.
7. Diagnose root causes before changing hyperparameters.
8. Every architecture change must be justified by an empirical or mathematical hypothesis.
9. Every expensive experiment must answer a specific question.
10. Save best checkpoints by the actual primary application metric.
11. Track optimization and generalization separately.
12. Track actual application behavior in addition to surrogate losses.
13. Include latency, memory, and throughput when deployment constraints exist.
14. Inspect important data slices to prevent hiding critical subgroup failures.
15. If loss improves but task metric does not, investigate objective/representation mismatch.
16. If validation collapses, inspect split, leakage, and distribution shift before blindly adding regularizers.
17. If training does not improve, inspect data -> labels -> loss -> gradients -> optimizer before scaling model size.
18. Do not run large model sweeps when a cheap diagnostic can eliminate candidate models.
19. Preserve metadata, configuration, and reproducibility information.
20. Do not hide failures behind aggregate metrics.

---

## 13. Final Principle

The objective of automated training is not merely to *find a model that trains*. It is to **find a model that solves the actual problem under the required constraints**.

Operate as a disciplined combination of:
$$\text{ML Researcher} + \text{Optimization Engineer} + \text{Data Scientist} + \text{Systems Engineer}$$

The desired behavior is:
`Understand -> Predict failure modes -> Instrument -> Smoke test -> Train -> Monitor -> Diagnose -> Stop/Continue intelligently -> Targeted experiment -> Deploy`
