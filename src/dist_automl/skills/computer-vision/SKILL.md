---
name: computer-vision
description: Comprehensive pipeline discipline for computer vision, covering visual diagnostics, classification, object detection, semantic/instance segmentation, and edge deployment.
---

# Computer Vision, Object Detection & Segmentation

> Complete discipline for computer vision workflows, covering image diagnostics, augmentations, classification inspection, object detection metrics, segmentation masks, and high-performance inference.

---

## 1. Visual Data Ingestion & Pre-Training Checks

- **Image Geometry & Channels**: Inspect image dimensions, aspect ratios, and color spaces (RGB, grayscale, RGBA). Normalize pixel values uniformly ($[0, 1]$ or standardized with ImageNet mean/std).
- **Dataset Health & Corruptions**: Detect truncated bytes, unreadable headers, blurriness (Laplacian variance), extreme over/underexposure, and duplicate image hashes.
- **Annotation Integrity**:
  - *Detection*: Validate bounding boxes satisfy $0 \le x_{\min} < x_{\max} \le W$ and $0 \le y_{\min} < y_{\max} \le H$. Filter out collapsed boxes ($w=0$ or $h=0$).
  - *Segmentation*: Check polygon closure, mask pixel bounds, and class index consistency.

---

## 2. Preprocessing & Augmentation Pipelines

- **Geometric Augmentations**: RandomResizedCrop, HorizontalFlip, RandomAffine, Perspective shifts.
- **Photometric Augmentations**: ColorJitter (brightness, contrast, saturation, hue), GaussianBlur, ISO noise.
- **Regularization Augmentations**: CutMix and MixUp to prevent memorization and improve out-of-distribution robustness.
- **Aspect-Ratio Preserving Letterboxing**: Preserve aspect ratios during resizing by padding borders rather than distorting image aspect ratios.

---

## 3. Computer Vision Classification & Visual Diagnostics

### Required Telemetry & Metrics:
- `loss/train` and `loss/val`
- Top-1 and Top-5 accuracy, Macro-F1, per-class metrics
- Confusion matrix and calibration curves when probabilities guide decisions.

### Mandatory Visual Prediction Inspection:
Never rely solely on scalar loss or accuracy curves. Inspect:
1. **High-Confidence Errors**: Predictions where the model was $> 90\%$ confident but wrong. These almost always expose mislabeled ground truth, optical illusions, or severe ambiguity.
2. **Low-Confidence Correct Predictions**: Expose boundary confusion.
3. **Representative Correct Samples**: Confirm predictions match human intuition.
4. **False Positives & False Negatives**: Categorize systematic errors by background, lighting, and object scale.
5. **Saliency / Attention Maps**: Inspect Grad-CAM to confirm attention is focused on the target object rather than incidental background cues.

---

## 4. Object Detection Discipline & Diagnostics

Never evaluate or select object detectors using training loss alone.

### Required Metrics & Telemetry:
- **Losses**: Jointly log classification loss, box regression loss (CIoU / GIoU / Smooth L1), and objectness loss (where applicable).
- **Detection Metrics**:
  - Mean Average Precision: mAP@50 and COCO-standard mAP@50:95
  - High-precision threshold metric: AP75
  - Scale-Specific Performance: $AP_{\text{small}}$ ($\text{area} < 32^2$), $AP_{\text{medium}}$ ($32^2 \le \text{area} \le 96^2$), and $AP_{\text{large}}$ ($\text{area} > 96^2$)
  - Per-class Average Precision to uncover class-specific blindness.

### Detection Failure Diagnosis:
- Visualize predicted bounding boxes overlaid against ground truth.
- Disentangle errors into:
  - *Localization error*: Correct class, but IoU between 0.1 and 0.5.
  - *Classification error*: Bounding box correctly placed, but wrong label assigned.
  - *Background false positive*: Box placed on empty background or clutter.
  - *Missed detections*: Ground truth objects completely undetected (often small or occluded).

---

## 5. Segmentation Discipline & Mask Diagnostics

### Required Metrics:
- `loss/train` and `loss/val` (e.g. combination of Cross-Entropy and Dice loss)
- Mean Intersection-over-Union (mIoU) and mean Dice coefficient
- Per-class IoU and Dice scores to monitor rare categories.

### Visual Error Inspection:
Construct a 4-panel visual dashboard for evaluation batches:
$$\text{[Input Image]} \quad \text{[Ground Truth Mask]} \quad \text{[Predicted Mask]} \quad \text{[Error / Difference Mask]}$$
- Specifically inspect small objects, thin boundary structures, and occluded boundaries.

---

## 6. Architecture Selection & Production Serving

- **Classification**: ConvNeXt / EfficientNetV2 for fast inductive bias; ViT / Swin Transformers for large compute budgets.
- **Detection**: YOLOv8/v10/v11, RT-DETR for real-time edge processing; Faster R-CNN for high-precision scenarios.
- **Segmentation**: SegFormer, UNet / UNet++ for biomedical/scientific images; Mask2Former for general panoptic segmentation.
- **Inference Acceleration**:
  - Export to **TensorRT** with FP16 / INT8 post-training quantization.
  - Export to **ONNX Runtime** for cross-platform CPU/GPU inference.
  - Optimize video decoding pipelines using NVIDIA DALI or hardware-accelerated video frames.
