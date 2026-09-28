---
name: dataset-diagnostics
description: Dataset analysis and quality discipline for ML agents. Audit data validity, hard leakage gates, label quality, group-aware splits, distribution coverage, data slice monitoring, redundancy, sampling, synthetic data, and dataset experiments.
---

# Dataset Analysis, Diagnostics & Data Selection Discipline

> Treat data quality, leakage prevention, and data selection as first-class components of the ML system. Maximize useful information per unit of total compute.

The default data loop:
```text
Valid Data -> Valid Split -> Zero Unacceptable Leakage -> Reliable Labels ->
Deployment Distribution -> Sufficient Coverage -> Redundancy Removal ->
Intelligent Sampling -> Validate Data Decision Experimentally -> Train
```

$$\boxed{\text{Maximize useful information per unit of total compute}}$$

---

## 1. Understand the Data & Run a Data Audit

Before expensive training, determine whether the dataset is valid for the task, correctly labeled, correctly split, and free of contamination.

### Pre-Training Audit Checklist:
- **Schema & Corruption**: Detect malformed samples, truncated bytes, missing/NaN/Inf values, unreadable headers, and encoding artifacts.
- **Contradictory & Duplicate Samples**: Detect exact feature duplicates with conflicting labels ($x_i = x_j$ but $y_i \neq y_j$) and near-duplicate variations across splits.
- **Input Scales & Outliers**: Profile extreme values, unnormalized ranges, and domain violations. Note: *an outlier is not automatically corrupt or useless*.
- **Sequence Lengths**: Profile p50, p90, p95, p99, and max lengths to set non-destructive truncation boundaries ($< 1\%$ truncation).
- **Modality-Specific Health**:
  - *Audio*: Sample rate uniformity (e.g. 16 kHz), duration distributions, amplitude clipping/saturation, SNR floor, silence trimming.
  - *Vision*: Resolution, aspect ratios, color channels (RGB/grayscale), bounding box bounds ($0 \le x_{\min} < x_{\max} \le W$).
  - *Text*: Subword token lengths, vocabulary coverage, HTML/markdown formatting noise, language identification.
  - *Tabular*: Missingness mechanisms (MCAR, MAR, MNAR), high-cardinality features, multicollinearity.

Record findings as `INFO`, `WARNING`, or `CRITICAL`.

---

## 2. Leakage Is a Hard Gate

Explicitly inspect and close all potential data leakage pathways:
- **Duplicate / Semantic Near-Duplicates**: Ensure identical or paraphrased samples do not bridge train and validation partitions.
- **Shared Entities**: Samples sharing the same underlying entity (user, patient, speaker) must never be split across train and val.
- **Temporal / Future Information**: In time series and causal tasks, future information must never leak into training folds.
- **Metadata Identifiers**: Ensure IDs, timestamps, or sensor IDs correlated with the target are removed from feature sets.
- **Preprocessing & Statistics Contamination**: Fit all scalers, encoders, and normalizers *strictly on training folds*; never compute dataset-wide statistics prior to splitting.
- **Target-Derived Features**: Verify no feature is calculated using post-event or target information.

**Rule**: If leakage invalidates evaluation: **STOP, REPAIR, and RERUN**. Never optimize models against contaminated validation.

---

## 3. Make the Split Match the Generalization Problem

Never default blindly to random row splitting. Determine what must remain strictly unseen at evaluation:

```text
Future Horizon       -> Chronological / Temporal separation
New Users/Customers  -> User entity separation (GroupKFold)
New Speakers/Voices  -> Speaker entity separation
New Medical Patients -> Patient / Subject separation
New Hardware/Devices -> Device / Sensor separation
New Environments     -> Location / Geographic separation
```

Verify the final split after preprocessing and dataset construction are completed.

---

## 4. Treat Label Quality as a Dataset Problem

Search systematically for mislabeled, ambiguous, noisy, or inconsistent ground truth:
- **Disagreement Signals**: Flag high cross-validation prediction error, ensemble disagreement, or high persistent cross-entropy loss.
- **Distinguish Hard vs. Corrupt**: High loss or outlier status does *not* imply a corrupt sample. An informative, edge-case sample is highly valuable.
- **Audit Workflow**:
  $$\text{Inspect} \;\to\; \text{Rank by suspicion} \;\to\; \text{Validate} \;\to\; \text{Quarantine or Correct}$$
- Preserve suspicious sample IDs and rationale in experiment logs.

---

## 5. Distribution Coverage & Data Slice Monitoring

- **Deployment Alignment**: Compare train, validation, and test distributions against the intended deployment population ($P_{\text{deploy}}(x)$). If distribution shift exists, determine whether it is expected, harmful, intentional, or accidental.
- **Never Let Aggregate Metrics Hide Subgroup Failures**:
  - Define deployment-relevant slices before training: demographic slices, sensor/device models, noise/SNR levels, sequence lengths, temporal regimes.
  - For each slice $s$, compute and report the primary metric $M_s$. An aggregate score of 95% is unacceptable if a critical minority slice collapses to 30%.
- **Out-of-Distribution (OOD) Testing**: Explicitly evaluate temporal shift, user shift, device shift, noise shift, and domain shift.

---

## 6. Redundancy, Data Value & Intelligent Sampling

When compute or scale matters, identify exact/near duplicates, redundant regions, and informative hard cases.

### Sampling Strategies:
- **Choose the Simplest Strategy**: Random/stratified, diversity/core-set, uncertainty sampling, hard negative mining, or domain mixture weighting.
- **Controlled Benchmark Comparison**: When reducing dataset size or pruning, always benchmark:
  $$\text{[Full Dataset]} \quad \text{vs.} \quad \text{[Random Subset]} \quad \text{vs.} \quad \text{[Proposed Subset]}$$
  Measure both task performance **and total computational cost** (including selection, embedding, and indexing time). A smaller dataset is not an optimization if selection costs more than it saves.

---

## 7. Hard Examples & Hard Negatives

For retrieval, metric learning, ranking, and classification:
- Identify genuinely informative hard examples; distinguish them from mislabeled or corrupted samples.
- Screen for false negatives in mined negative pools.
- Prevent repeated selection of identical hard samples across epochs.
- Confirm improvements on the true task metric (e.g. Recall@K) rather than training loss alone.

---

## 8. Scalability, Multi-Domain & Synthetic Data

- **Large Datasets**: Avoid $O(N^2)$ pairwise operations. Use streaming DataLoaders, approximate nearest neighbor (ANN) search, and approximate deduplication (MinHash / SimHash).
- **Multi-Source / Multi-Domain Data**:
  - Measure per-source contributions, dominance, and negative transfer.
  - Test domain mixture weights rather than assuming proportional sampling is optimal.
  - Surface per-domain performance tradeoffs rather than obscuring them in aggregate numbers.
- **Synthetic & Generated Data**:
  - Treat synthetic data as a distinct source. Audit diversity, prompt artifacts, mode collapse, and contamination against evaluation sets.
  - Compare real-only, synthetic-only, and mixed configurations on clean real evaluation data.

---

## 9. Controlled Dataset Experiments

For every consequential data decision, execute a cheap controlled experiment first:
- *New Split*: Run short training runs comparing baseline vs. proposed split.
- *Label Filtering*: Measure validation performance before and after quarantine.
- *Pruning / Reduction*: Compare full vs. random vs. selected subset.
- *Domain Mixture*: Compare uniform vs. importance-weighted mixtures.
- *Augmentation / Hard Mining*: Compare baseline vs. augmented/mined runs under identical seeds and hyperparameters.

---

## 10. Stop -> Diagnose -> Repair -> Retry Protocol

- **Immediate Stop Conditions**: Evaluation leakage discovered, invalid split, benchmark contamination, systematically corrupt labels, or data pipeline preprocessing applied before splitting.
- **Diagnose**: Isolate affected samples, entity groups, splits, sources, and labels.
- **Repair**: Rebuild leak-free splits, correct/quarantine noisy labels, adjust domain mixtures, or fix preprocessing code.
- **Retry**: Validate fixes with a fast proxy experiment before launching full training.
- **Reproducibility**: Record dataset versions, split definitions, random seeds, deduplication rules, and filtering criteria.
