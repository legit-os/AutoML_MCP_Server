---
name: embeddings-retrieval
description: Comprehensive pipeline discipline for representation learning, dense retrieval, metric learning, and similarity search across multimodal data.
---

# Embedding Models, Dense Retrieval & Metric Learning

> Complete discipline for embedding models, contrastive representation learning, hard negative mining, collapse diagnostics, similarity distributions, and vector search indexing.

---

## 1. Problem Formulation & Similarity Objectives

- **Hypersphere Mapping**: Map semantically similar entities close together and dissimilar entities far apart on a unit hypersphere:
  $$\text{sim}(q, p) = \frac{q \cdot p}{\|q\|_2 \|p\|_2} = \cos(\theta)$$
- **Data Pairs & Triplets**: Formulate training pairs $(q, d^+)$ or triplets $(q, d^+, d^-)$.
- **Label Hygiene & Collisions**: Detect and purge false negatives in training batches (e.g. semantically equivalent queries or duplicate documents marked as negative).

---

## 2. In-Batch & Hard Negative Mining

- **In-Batch Negatives**: Train with large batch sizes where all other documents in the batch serve as negative distractors for each query.
- **Hard Negative Mining**:
  - Mine top approximate nearest neighbors (from BM25 or previous checkpoint embeddings) that are true negatives.
  - Train cross-encoders to filter false negatives from the mined pool before bi-encoder fine-tuning.
- **Loss Formulations**:
  - InfoNCE / MultipleNegativesRankingLoss with temperature $\tau$:
    $$\mathcal{L} = -\log \frac{\exp(s(q, d^+) / \tau)}{\sum_{j} \exp(s(q, d_j) / \tau)}$$
  - TripletMarginLoss with margin parameter $m$:
    $$\mathcal{L} = \max(0, s(q, d^-) - s(q, d^+) + m)$$
  - ArcFace / CosFace for closed-set face/audio speaker identification.

---

## 3. Retrieval Metrics & Similarity Diagnostics

Never evaluate retrieval or contrastive models by loss alone.

### Required Retrieval Metrics:
- **Recall@K**: Track Recall@1, Recall@5, and Recall@10.
- **Ranking Metrics**: Mean Reciprocal Rank (MRR) and Normalized Discounted Cumulative Gain (NDCG@10).
- **Median Rank**: Median position of the true positive document in the candidate corpus.

### Similarity Distribution Diagnostics:
Continuously track histograms of:
- **Positive Similarity**: $s(q, d^+)$ distribution (should shift toward $+1.0$).
- **Random Negative Similarity**: $s(q, d^-_{\text{random}})$ distribution.
- **Hard Negative Similarity**: $s(q, d^-_{\text{hard}})$.
- **Margin Distribution**: $\Delta = s(q, d^+) - s(q, d^-_{\text{hard}})$.
- **Hard-Negative Violation Rate**: Fraction of samples where margin is violated: $P(\Delta < 0)$.

### Dot-Product Norm Alert:
For dot-product retrieval ($q^T d = \|q\| \|d\| \cos\theta$), explicitly monitor vector norms. A model can artificially reduce loss by inflating embedding magnitudes rather than improving angular separation. Normalize embeddings ($L_2$) unless magnitude explicitly encodes confidence.

---

## 4. Representation Collapse & Isotropy Monitoring

Periodically inspect embedding geometries in TensorBoard:
- **Norm Distribution**: Check for collapsing norms ($\to 0$) or runaway norm growth.
- **Per-Dimension Variance**: If the variance along any dimension drops to zero, that dimension is dead. If variance across all dimensions drops to zero, the model has undergone **complete representation collapse**.
- **Effective Rank & Isotropy**: Compute singular values via SVD on the batch embedding matrix. Rapid singular value decay indicates representation anisotropy (cone effect), where all vectors cluster in a narrow subspace.
- **Dimensionality Reduction**: Use PCA and UMAP as qualitative diagnostics to check cluster separation, but never treat 2D projections as proof of representation quality.

### Critical Diagnostic:
If retrieval loss improves while Recall@K stagnates, inspect hard negatives, similarity distributions, embedding collapse, and objective/metric alignment before changing architecture.

---

## 5. Two-Stage Retrieval Architecture & Vector Indexing

1. **Bi-Encoder (Dense Indexing)**:
   - Encodes queries and documents into independent vector embeddings.
   - **Matryoshka Representation Learning (MRL)**: Train embeddings so truncating from 768 dimensions down to 128 or 256 dimensions preserves $> 95\%$ of retrieval precision while saving $70\%$ vector memory.
2. **Cross-Encoder (Reranking)**:
   - Full joint cross-attention across (query, candidate) pairs for the top 50–100 candidates to produce final relevance scores.
3. **Vector Search Indexing**:
   - Build **HNSW** (Hierarchical Navigable Small World) or **IVF-PQ** (Inverted File with Product Quantization) indices.
   - Apply scalar INT8 quantization to dense vectors to reduce RAM requirements by $75\%$.
