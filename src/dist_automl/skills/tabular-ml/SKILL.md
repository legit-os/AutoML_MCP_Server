---
name: tabular-ml
description: Comprehensive pipeline discipline for tabular ML, covering feature diagnostics, target leakage, GBDTs, classification, regression, and time series forecasting.
---

# Tabular ML, Classification, Regression & Forecasting

> Complete discipline for tabular datasets, covering exploration, leakage prevention, feature engineering, tree-based models, classification, regression residuals, time series forecasting, and low-latency inference.

---

## 1. Tabular Dataset Diagnostics & Leakage Prevention

Inspect before serious training:
- **Feature Distributions & Cardinality**: Missingness percentages, high-cardinality categoricals, skewness, and out-of-range numericals.
- **Aggressive Leakage Prevention**: Tabular datasets easily produce suspiciously strong results from target-derived features or temporal contamination:
  - Verify no feature is computed using information from after the target event occurred.
  - Verify out-of-fold target encoding is computed strictly inside training folds without leaking validation fold labels.
  - Check feature correlations with target; an unusually high correlation ($> 0.95$) often indicates label leakage.
- **Split Methodology**:
  - *I.I.D. Data*: Stratified K-Fold for classification, standard K-Fold for regression.
  - *Grouped Entities*: GroupKFold (e.g. by `customer_id` or `hospital_id`) so samples from the same entity never span train and val.
  - *Temporal / Causal*: Chronological split. Future records must never enter training folds.

---

## 2. Feature Engineering & Preprocessing

- **Imputation**: Median/mean for continuous features, mode or explicit `"MISSING"` indicator for categoricals.
- **Categorical Encodings**: Out-of-fold target encoding with additive smoothing, frequency/count encoding, or one-hot encoding for cardinality $< 10$.
- **Transformations**: Power transformations (Log1p, Yeo-Johnson) for skewed distributions.
- **Interactions & Aggregations**: Domain-informed ratios, differences, and group-by rolling/window aggregations.

---

## 3. Architecture Selection: Baselines to GBDTs

1. **Establish Cheap Baseline**: Majority class for classification, mean/median target for regression, or Ridge/Lasso linear model.
2. **Gradient Boosted Decision Trees (GBDTs)**:
   - Primary workhorses: **LightGBM** (fastest, histogram-based), **XGBoost** (exact/approximate greedy trees), **CatBoost** (superior out-of-the-box categorical handling).
   - Tuning parameters: `learning_rate` (0.01 to 0.05), `num_leaves` / `max_depth` (3 to 8), `subsample` (0.7 to 0.9), `colsample_bytree` (0.6 to 0.8), `min_child_samples`.
3. **Tabular Deep Learning**:
   - TabNet, FT-Transformer, or dense residual MLPs when tabular inputs are combined with text/image embeddings.

---

## 4. Classification Discipline & Diagnostics

### Formulations:
- **Binary**: One binary target; Sigmoid / BCE loss.
- **Multiclass**: Exactly one mutually exclusive class; $C$-way logits with Cross-Entropy loss.
- **Multilabel**: Independent binary targets; independent Sigmoids with BCE loss (never use Softmax).

### Required Metrics & Curves:
- `loss/train` and `loss/val`
- Train and validation accuracy (only when class balance is meaningful)
- Precision, Recall, and Macro-F1
- Confusion matrix and per-class precision/recall breakdowns
- Precision-Recall (PR) curve for imbalanced problems; ROC curve where appropriate
- Calibration / reliability diagram when predicted probabilities drive downstream decision thresholds.

### Classification Failure Diagnosis:
- *Train good + Minority recall poor*: Class imbalance, uncalibrated threshold, missing cost weighting, or unrepresentative sampling.
- *Train near-perfect + Validation poor*: Overfitting, target leakage, memorization, or train/validation distribution shift.
- *Both train and validation poor*: Corrupted labels, incorrect loss formulation, optimization divergence, or insufficient model capacity.

---

## 5. Regression Discipline & Residual Diagnostics

### Required Metrics:
- `loss/train` and `loss/val`
- MAE, RMSE, and $R^2$ where meaningful
- Predicted-vs-Actual scatter plot
- Residual distribution histogram ($e = y - \hat{y}$)
- Residual-vs-Target scatter plot
- Error breakdown by target range and error percentiles (p50, p90, p99).

### Regression Failure Diagnosis:
- **Heteroscedasticity**: Error variance expands as target magnitude increases -> Apply log/box-cox transform to the target.
- **Target Range Blind Spots**: A low average loss can hide catastrophic errors in a specific target bracket.
- **Nonlinear Residuals**: Curved patterns in residual plots indicate the model missed key polynomial or interaction features.

---

## 6. Time Series & Forecasting Discipline

- **Causal Splitting**: Strictly use chronological splits. Never use random row splits that leak future time horizons.
- **Required Metrics**:
  - `loss/train` and `loss/val` over time
  - Forecast vs. actual trajectories
  - Residuals over time and rolling window errors
  - Error by forecast horizon: evaluate $MAE(h)$ and $RMSE(h)$ separately at each future step $h \in \{1, \dots, H\}$
  - Regime-wise performance (e.g. holiday vs. non-holiday, volatile vs. calm periods)
  - Prediction interval coverage for probabilistic forecasting.
- **Temporal Diagnostics**: Check for non-stationarity, seasonal drift, structural regime changes, and autocorrelated errors.

---

## 7. Explainability & Production Deployment

- **Feature Importance**: Compute TreeSHAP (SHapley Additive exPlanations) and permutation feature importance to verify physical plausibility.
- **Low-Latency Serving**:
  - Compile GBDT models to C++ runtime using **Treelite** or export to **ONNX Runtime** for microsecond inference.
  - Package data transformations with Scikit-Learn `Pipeline` or `ColumnTransformer` to eliminate train-serve skew.
