---
mem_id: 82f2b8f3-a286-4efc-8285-ef9e4736b727
title: "Lightspeed Level 2 Visual Parsing / AI Trading Infrastructure"
source: mem (uncollected, AI-trading; PII-scrubbed for project scope)
redactions: 0
---

# Lightspeed Level 2 Visual Parsing / AI Trading Infrastructure

## Core Project Concept

Investigating whether a Ross Cameron-style small-cap momentum trading assistant/system could visually parse Level 2 market data from the Lightspeed Trader desktop application in real time.

Primary insight: generalized OCR and desktop AI agents are likely the wrong abstraction for this problem. Because Level 2 data is highly structured, fixed-position, repetitive, and low-symbol-count, specialized computer vision pipelines may be dramatically more effective and lower latency.

## Key Architectural Conclusions

### What NOT to Use

- Claude/Cowork style "computer use" agents are too slow for fast market data due to screenshot -> reasoning -> action loops.
- Screenpipe is not appropriate for sub-second Level 2 parsing; it is optimized for human productivity memory workflows, not high-frequency visual telemetry.
- Generalized OCR (especially document-oriented OCR like Tesseract in default modes) introduces unnecessary overhead and complexity.

### Preferred Direction

Treat the problem as constrained visual signal extraction rather than generalized AI vision.

Potential pipeline:

1. High-speed GPU-backed screen capture (DXcam / Desktop Duplication API)
2. Region-of-interest cropping of exact Level 2 cells
3. Frame differencing / delta tracking
4. Specialized digit recognition
5. Structured order book reconstruction
6. Signal generation
7. Optional higher-level AI reasoning layer

Important distinction:

- The core parsing loop likely should NOT use LLMs.
- LLMs may still be useful for higher-level reasoning, pattern summarization, labeling, analysis, or strategy refinement.

## Important Technical Insights

### Why the Problem May Be Easier Than Expected

Lightspeed Level 2 is:

- fixed font
- fixed coordinates
- fixed semantic structure
- low symbol count
- repetitive visual layout
- stable colors and formatting

This makes the problem closer to reading a digital instrument panel than solving generalized OCR.

### Likely Better Than OCR

Potential approaches better suited than generic OCR:

- template matching
- digit classifiers
- tiny CNNs
- lightweight object detectors
- custom segmentation models
- delta-based state tracking

Potentially only \~10 numeric glyphs plus a few colors/arrows need classification.

### Temporal Continuity Insight

A major insight: the system should not treat each frame independently.

Instead of:\
"What does the entire frame say?"

Use:\
"What changed since the previous frame?"

This could massively reduce compute requirements and latency.

## Practical Development Plan

### Phase 1 — Offline Validation

Record Lightspeed sessions using standard desktop capture tools (OBS or similar).

Goals:

- determine font stability
- verify frame readability
- test ROI extraction
- test template matching
- benchmark achievable FPS
- determine whether OCR is even necessary

This avoids premature live-system complexity.

### Phase 2 — Prototype Parser

Build:

- ROI cropping
- grayscale/thresholding
- frame differencing
- basic digit extraction

Prefer fixed-coordinate deterministic parsing before ML.

### Phase 3 — ML Upgrade Only If Necessary

If template matching becomes unreliable:

- train tiny CNN/digit classifier on exact Lightspeed glyphs
- keep model extremely small and specialized
- optimize for low latency and deterministic behavior

## Important Strategic Conclusions

The difficult part is likely NOT the visual parsing.

Harder problems likely include:

- discovering predictive signals
- avoiding overfitting
- dealing with spoofing/liquidity games
- execution quality/slippage
- market regime shifts
- strategy robustness

## Platform-Specific Notes

Lightspeed Trader may actually be relatively favorable for this project because its UI appears more stable and traditional than many modern WebGL-heavy trading applications.

No evidence currently identified suggesting aggressive detection of standard desktop capture APIs (OBS, DXcam, Desktop Duplication API), though automation/TOS considerations may still matter.

## Important Framing

This is not true HFT.

Ross Cameron-style momentum trading operates on human-scale timing (often seconds rather than microseconds), meaning:

- moderate FPS may be sufficient
- specialized visual parsing may be feasible
- retail-level latency constraints may be achievable

## Current Open Questions

- Required FPS for meaningful signal extraction
- Whether template matching alone is sufficient
- Whether color changes carry predictive value
- Whether direct feed/API alternatives exist for Lightspeed
- Which exact Level 2 regions contain the highest signal density
- How stable Lightspeed rendering remains across sessions and monitors
