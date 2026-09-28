---
name: generative-llms
description: Comprehensive pipeline discipline for LLMs and generative models, covering instruction tuning, QLoRA, generative telemetry, mode collapse, decoding strategies, and quantized serving.
---

# Generative LLMs & Autoregressive Model Discipline

> Complete discipline for autoregressive Large Language Models (LLMs) and generative pipelines, spanning dataset formatting, parameter-efficient fine-tuning (QLoRA), generative telemetry, decoding controls, and low-latency serving.

---

## 1. Task Formalization & Instruction Formatting

- **Data Formatting**: Standardize conversations into consistent templates: ChatML (`<|im_start|>user\n...<|im_end|>\n<|im_start|>assistant\n...<|im_end|>`), ShareGPT, or Alpaca schema.
- **Masking User Prompts**: Compute cross-entropy loss *only* on the assistant / completion tokens (assign label `-100` to all prompt/user tokens). Training models to predict user inputs degrades generation quality and wastes capacity.
- **Context Length & Packing**: Profile token length histograms. Pack multiple short conversations into a single sequence (multipack / sequence packing) using block-diagonal attention to eliminate padding waste.

---

## 2. Parameter-Efficient Fine-Tuning (PEFT / QLoRA)

- **4-bit NormalFloat (NF4)**: Load frozen base weights with bitsandbytes NF4 quantization, double quantization, and FP16/BF16 compute dtype to fit 7B–14B models on consumer VRAM.
- **LoRA Hyperparameters**:
  - Target modules: Apply LoRA adapters to all projection layers (`q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`).
  - Rank and Alpha: Set $r = 16\text{--}32$, $\alpha = 2r$.
- **System Optimizations**:
  - Enable **FlashAttention-2** or PyTorch SDPA for memory-efficient multi-head attention.
  - Enable gradient checkpointing to allow larger effective micro-batch sizes.
  - Use paged AdamW optimizer (`paged_adamw_8bit`) to prevent memory spikes during backward passes.

---

## 3. Generative Telemetry & Downstream Diagnostics

Never rely solely on training loss or validation perplexity.

### Required Telemetry:
- `loss/train` and `loss/val`
- Perplexity: $\text{PPL} = \exp(\text{loss})$
- Learning rate, gradient norm, and GPU memory utilization
- Token throughput (tokens/sec).

### Critical Generative Diagnostics:
1. **The SFT Loss Trap**: A lower cross-entropy validation loss does *not* automatically equate to superior conversational quality or factual correctness.
2. **Instruction-Following & Formatting**: Periodically generate responses on a fixed evaluation prompt suite. Check structure, tone, and adherence to negative constraints.
3. **Capability Regression & Catastrophic Forgetting**: Evaluate periodically against general benchmarks (MMLU, GSM8K, HumanEval) to detect regression on core reasoning, coding, or safety capabilities.
4. **Mode Collapse & Degeneration**: Inspect generated samples for repetitive loops (repeating n-grams) or degenerate short responses.
5. **Diversity & Conditioning Correctness**: Validate that responses accurately ground on provided context documents without hallucinations.

---

## 4. Decoding Strategies & Generation Control

- **Sampling Parameters**:
  - Creative generation: Temperature $0.7\text{--}0.9$, top-p $0.9$, min-p $0.05$.
  - Factual / Reasoning / Coding: Temperature $0.0\text{--}0.2$ (greedy decoding) with top-p $1.0$.
  - Repetition penalty: $1.05\text{--}1.15$ to suppress repetitive token loops.
- **Grammar-Constrained Generation**: Use finite-state machine (FSM) or JSON schema decoding (e.g. Outlines, Guidance, llama.cpp grammars) when deterministic output structure is required.

---

## 5. Inference Optimization & Model Deployment

- **Adapter Merging**: Merge LoRA adapter weights directly into base model weights for zero-overhead inference.
- **Quantization Formats**:
  - **AWQ / GPTQ**: For high-throughput GPU serving.
  - **GGUF (Q4_K_M, Q5_K_M)**: For CPU and edge memory environments (Ollama, llama.cpp).
  - **FP8**: For modern GPUs (Ada Lovelace, Hopper) with native 8-bit floating point matrix multiplication.
- **Serving Engines**: Deploy endpoints using **vLLM** or **SGLang** with continuous batching and PagedAttention for maximum token throughput.
