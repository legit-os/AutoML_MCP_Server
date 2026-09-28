---
name: nlp
description: Comprehensive pipeline discipline for Natural Language Processing (NLP), covering tokenization diagnostics, text classification, Named Entity Recognition (NER), span extraction, encoder fine-tuning, and ONNX serving.
---

# Natural Language Processing (NLP) & Sequence Diagnostics

> Complete discipline for NLP applications, spanning subword tokenization, text classification, token-level sequence labeling (NER), span extraction (QA), transformer encoders, and optimized inference.

---

## 1. Corpus Diagnostics & Subword Tokenization

Inspect and profile before model training:
- **Sequence Length Profiling**: Compute length percentiles (p50, p90, p95, p99, max). Set `max_seq_length` to maintain truncation rate $< 1\%$. Avoid aggressive truncation that cuts critical semantic context.
- **Subword Vocabulary Alignment**: Align tokenization with backbone vocabulary (WordPiece for BERT, BPE for RoBERTa/DeBERTa, SentencePiece for multilingual backbones). Check for vocabulary mismatches or excessive out-of-vocabulary (`[UNK]`) tokens.
- **Corpus Quality & Normalization**: Strip HTML/markdown noise, normalize Unicode (NFKC), remove duplicate or near-duplicate texts, and verify language/dialect consistency.
- **Dynamic Batch Padding**: Pad sequences only to the longest sample *in the current batch* rather than global static padding. Reduces wasted self-attention FLOPs by up to $50\%$.
- **Attention Mask Verification**: Verify attention masks assign $0$ to padded tokens to avoid attention distribution pollution.

---

## 2. Text Classification & Sentence-Pair Tasks

### Formulation Alignment:
- **Binary Classification**: 1 output logit + `BCEWithLogitsLoss`.
- **Multiclass Classification**: $C$ output logits + `CrossEntropyLoss` (mutually exclusive labels).
- **Multilabel Classification**: Independent binary targets + `BCEWithLogitsLoss` (never use Softmax).
- **Sentence-Pair & NLI Tasks**: Concatenate premise and hypothesis with separator tokens (`[CLS] A [SEP] B [SEP]`) for Natural Language Inference or semantic equivalence verification.

### Required Metrics:
- Macro-F1 and Balanced Accuracy for imbalanced label distributions.
- Confusion matrix and per-class precision/recall breakdowns.
- Expected Calibration Error (ECE) and temperature scaling when prediction probabilities drive downstream actions.

---

## 3. Token Classification & Named Entity Recognition (NER)

For sequence tagging, entity extraction, and slot filling:
- **Label Alignment with Subwords**: When words are split into subwords (e.g. `['transform', '##ers']`), apply the entity label to the initial subword and assign label `-100` (ignored by CrossEntropy) to subsequent subwords to prevent gradient skew.
- **Tagging Schemes**: Standardize on **BIO** (`B-PER`, `I-PER`, `O`) or **BIOES** schemes.
- **Entity-Level Evaluation (Seqeval)**: Never evaluate NER using raw token-level accuracy. Use entity-level Precision, Recall, and F1 (an entity is only correct if the boundary span and entity type are both exact matches).
- **Label Transition Constraints**: Add a linear-chain CRF (Conditional Random Field) layer over transformer emissions if illegal label transitions (e.g. `O -> I-PER`) occur frequently.

---

## 4. Extractive Question Answering & Span Extraction

For span selection tasks (SQuAD format):
- **Objective Formulation**: Predict start and end token positions within the context paragraph:
  $$\mathcal{L} = \text{CrossEntropy}(\text{start\_logits}, y_{\text{start}}) + \text{CrossEntropy}(\text{end\_logits}, y_{\text{end}})$$
- **Sliding Window for Long Documents**: For documents exceeding `max_seq_length`, apply a sliding window with overlap (stride $= 128$ tokens) and track global document offsets.
- **Metrics**: Exact Match (EM) and token-level Macro-F1 across predicted answer spans.

---

## 5. Architecture Selection & Baselines

1. **TF-IDF + Linear Benchmark**: Always run an n-gram TF-IDF + LogisticRegression / LinearSVC benchmark. If transformer models do not clearly surpass this baseline, input texts or labels contain substantial noise.
2. **Pretrained Transformer Encoders**:
   - Modern backbones: **DeBERTa-v3** (disentangled attention, superior NLI/classification), **ModernBERT** (native unpadded FlashAttention, 8k context), **RoBERTa**.
   - Layer-wise Learning Rate Decay (LLRD): Use lower LR for bottom encoder layers ($1\times 10^{-5}$) and higher LR for classification/tagging heads ($5\times 10^{-5}$).
3. **Parameter-Efficient Adaptation (LoRA)**:
   - For resource-constrained settings, freeze encoder weights and apply LoRA adapters to attention projection matrices ($r=8\text{--}16, \alpha=16\text{--}32$).

---

## 6. Inference Optimization & Serving

- **Graph Optimization**: Export encoder models to **ONNX Runtime** with fused attention and LayerNorm kernels.
- **Dynamic INT8 Quantization**: Quantize feedforward linear projection weights for $2\times\text{--}3\times$ speedups on CPU.
- **Length-Bucketed Serving**: Group incoming inference requests into sequence-length buckets to minimize padding overhead during batched serving.
