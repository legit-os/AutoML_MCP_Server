---
name: neural-nets
description: Comprehensive pipeline discipline for Neural Networks and Deep Learning, covering architecture selection rules, numerical stability, gradient clipping, optimization, and quantization.
---

# Neural Networks & Deep Learning Architecture Optimization

> Complete discipline for deep neural networks, custom PyTorch architectures, hypothesis-driven architecture selection, numerical stability safeguards, gradient clipping telemetry, and post-training quantization.

---

## 1. Architectural Compatibility & Capacity Budget

Before writing deep learning layers, explicitly verify:
- **Receptive Field & Context**: Ensure the network context or receptive field mathematically covers the required input span.
- **Output Activation vs. Loss Formulation**:
  - *Binary Classification*: 1 logit with `BCEWithLogitsLoss` (no Sigmoid in model forward pass).
  - *Multiclass Classification*: $C$ logits with `CrossEntropyLoss` (no Softmax in model forward pass).
  - *Regression*: Linear output matching physical bounds (or custom activations, e.g. Softplus for positive-only values).
  - *Continuous Targets*: Never discretize continuous targets into artificial classification bins without empirical justification.
- **Compute Feasibility**: Estimate parameter counts, forward activation memory footprint, optimizer state size, and batch VRAM requirements.

---

## 2. Hypothesis-Driven Architecture Selection Rule

Never blindly iterate through architectures (`CNN -> ResNet -> ViT -> ConvNeXt`) without a formal hypothesis.

Before training Candidate Architecture B after Architecture A, explicitly answer all 5 questions:
1. **What specific failure did Architecture A demonstrate?** (e.g. inability to capture long-range dependencies, gradient vanishing, or high-frequency aliasing).
2. **What architectural property of B directly resolves that failure?** (e.g. self-attention global receptive field, residual skip connections, or anti-aliased downsampling).
3. **Why should B solve it mathematically or empirically?** (e.g. effective context length grows from 16 to 512 timesteps).
4. **What exact metric or diagnostic curve should change if the hypothesis is correct?** (e.g. validation loss on long-sequence slice decreases from 0.82 to $< 0.45$).
5. **What is the additional parameter and compute cost of B over A?**

---

## 3. Deep Learning Optimization & Schedules

- **Optimizer Selection**: Default to **AdamW** with decoupled weight decay ($\lambda \in [10^{-4}, 10^{-1}]$). Use SGD with Nesterov momentum ($0.9$) for standard convolutional vision networks.
- **Learning Rate Warmup & Schedulers**:
  - Linearly warm up the learning rate for the initial 5–10% of total training steps to stabilize early gradient variances.
  - Follow with `CosineAnnealingLR` down to a minimum rate ($\approx 10^{-6}$) or `OneCycleLR`.
- **Normalization & Activations**:
  - Prefer modern activations (**GELU**, **SiLU**) over standard ReLU to prevent dead neuron collapse.
  - Insert normalization layers (**LayerNorm**, **RMSNorm**, or **BatchNorm1d**) after linear/convolutional projections to stabilize internal covariate shift.

---

## 4. Numerical Stability Safeguards

Continuously monitor:
- **NaN / Inf Detection**: Check loss, gradient norms, and parameter weights at every step.
- **Mixed-Precision Scaler Dynamics**: When using FP16 automatic mixed precision (`torch.cuda.amp.GradScaler`), monitor the scaler scale factor. Frequent underflow scale reductions indicate unstable gradients (switch to BF16 if supported by hardware).
- **Activation & Weight Ranges**: Inspect layer activation distributions to catch overflow/underflow early.

### Stabilizing Interventions:
If numerical instability occurs, test interventions one at a time (never apply everything simultaneously):
`Lower learning rate -> Add gradient clipping -> Use numerically stable log-sum-exp loss -> Safe initialization (Kaiming/Xavier) -> LayerNorm / RMSNorm -> BF16 precision`

---

## 5. Gradient Clipping Telemetry

Never treat gradient clipping as a silent magic fix for unstable architectures.

When clipping is enabled (`torch.nn.utils.clip_grad_norm_`), log both:
1. **Gradient norm before clipping**: $\|\nabla L_{\text{unclipped}}\|$.
2. **Gradient norm after clipping**: $\|\nabla L_{\text{clipped}}\|$.
3. **Clipping frequency**: Percentage of steps where clipping was active.

### Critical Diagnostic:
If clipping occurs on $> 80\%$ of steps, the underlying optimization or loss landscape is poorly conditioned. Investigate learning rate, loss formulation, or weight initialization rather than masking the problem with clipping.

---

## 6. Overfit Testing & Post-Training Quantization

- **Tiny-Set Overfit Test**: Overfit a fixed batch of 16–32 samples with regularizers disabled. The model must reach near-zero loss in $< 100$ epochs. If it fails, inspect computation graph, label alignment, and learning rate.
- **Residual Regularization**: Use Dropout ($0.1\text{--}0.3$) and weight decay. Add residual connections if depth exceeds 4 dense layers to eliminate vanishing gradients.
- **Inference Optimization**:
  - Compile with `torch.compile(model, mode="reduce-overhead")`.
  - Apply Post-Training Quantization (PTQ) to INT8 or FP16 for low-latency serving on CPU/edge hardware.
  - Export to **ONNX Runtime** or **TorchScript**.
