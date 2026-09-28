---
name: audio-speech
description: Comprehensive pipeline discipline for audio signal processing, acoustic classification, speech recognition (ASR), and keyword spotting (KWS).
---

# Audio, Speech Processing & Keyword Spotting (KWS)

> Complete discipline for audio signal processing, acoustic classification, Automatic Speech Recognition (ASR), and Keyword Spotting (KWS), spanning feature extraction, slice diagnostics, and streaming deployment.

---

## 1. Audio Data Ingestion & Pre-Training Checks

- **Audio Standardization**: Enforce uniform sample rate across all clips (e.g. 16 kHz), mono channel conversion, and bit-depth normalization (float32 normalized to $[-1.0, 1.0]$).
- **Acoustic Profiling**:
  - Duration distribution: Check for truncated utterances or excessively long audio clips.
  - Clipping & Amplitude Saturation: Detect clipped audio waveforms that introduce artificial high-frequency harmonics.
  - Noise Floor & Loudness: Measure Signal-to-Noise Ratio (SNR) and RMS loudness across splits.
  - Silence Trimming: Trim non-informative leading/trailing silence using an energy-based Voice Activity Detector (VAD).

---

## 2. Feature Representations & Augmentations

- **Time-Frequency Representations**:
  - Log-Mel Spectrograms: $n_{\text{fft}} = 400$ ($25\text{ms}$ window at $16\text{kHz}$), hop length $= 160$ ($10\text{ms}$ stride), $80\text{--}128$ Mel filterbanks.
  - Mel-Frequency Cepstral Coefficients (MFCCs): 13–40 coefficients for lightweight edge models.
- **Acoustic Augmentation (SpecAugment)**:
  - Time masking: Zeroing or replacing vertical spectrogram frames with noise.
  - Frequency masking: Zeroing horizontal frequency bands.
  - Acoustic perturbations: Additive background noise (musan / babble noise at $0\text{--}20\text{dB}$ SNR), room impulse response (RIR) reverberation convolutions, pitch shifting ($\pm 2$ semitones), and time stretching ($0.9\times\text{--}1.1\times$).

---

## 3. Architecture Selection: Baselines to Transformers

1. **Audio Classification & Sound Event Detection (SED)**:
   - Audio Spectrogram Transformer (AST), EfficientNet-B0/B2 on log-mel spectrograms.
2. **Automatic Speech Recognition (ASR)**:
   - Pretrained self-supervised speech encoders: **Whisper**, **Conformer-CTC**, **Wav2Vec 2.0 / WavLM**.
   - Loss: Connectionist Temporal Classification (CTC) for fast non-autoregressive decoding; Seq2Seq cross-entropy with teacher forcing for rich transcriptions.
3. **Keyword Spotting (KWS) & Wake Words**:
   - Lightweight temporal backbones: Depthwise Separable CNN (DS-CNN), CRNN, or BC-ResNet for sub-milliwatt edge devices.

---

## 4. Acoustic Telemetry & Slice Diagnostics

### A. Automatic Speech Recognition (ASR) Diagnostics:
- **Metrics**: Word Error Rate (WER) and Character Error Rate (CER).
- **WER Error Decomposition**: Decompose WER into Substitution ($S$), Deletion ($D$), and Insertion ($I$) errors:
  $$\text{WER} = \frac{S + D + I}{N}$$
  - High insertions ($I$): Model is hallucinating words or triggered by background noise.
  - High deletions ($D$): Model is skipping fast speech or trailing quiet words.
  - High substitutions ($S$): Acoustic model confusion between phonetically similar sounds.

### B. Keyword Spotting (KWS) Diagnostics:
- **Metrics**: False Alarm Rate (FAR), False Rejection Rate (FRR), and Equal Error Rate (EER).
- **Production Operating Metric**: False activations per hour under continuous realistic background noise / unprompted speech.
- **Production-Threshold Recall**: Recall at the operating decision threshold rather than area under ROC curve.

### C. Mandatory Acoustic Slice Evaluation:
Never judge speech models on aggregate metrics alone. Evaluate across:
- **SNR Slices**: Clean ($> 20\text{dB}$), moderate ($10\text{--}20\text{dB}$), and noisy ($< 10\text{dB}$).
- **Speaker Slices**: Seen vs. unseen speakers; diverse vocal pitch and accents.
- **Microphone & Device Slices**: Near-field vs. far-field array microphones; varying acoustic enclosures.
- **Speaking Rate**: Fast vs. slow speech rates.

---

## 5. Streaming Inference & Low-Latency Deployment

- **Causal Architecture Constraints**: Ensure convolutions and attention layers are strictly causal or use a bounded lookahead buffer (e.g. $160\text{ms}$).
- **Voice Activity Detection (VAD) Gating**: Gate acoustic model evaluation with a lightweight VAD (e.g. Silero VAD) to eliminate idle inference on silence.
- **Model Quantization**: Quantize weights to INT8 and export to **ONNX Runtime** or **TFLite** for real-time edge processing.
