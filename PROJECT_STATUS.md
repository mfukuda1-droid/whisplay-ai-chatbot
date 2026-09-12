# Whisplay AI Chatbot — Project Status

Last updated: 2026-09-12

This document records the current real-device status and recent project decisions so ChatGPT, Codex, and human developers can share the same working context. For architecture and permanent coding-agent instructions, also read `AGENTS.md`.

## Primary Target

- Raspberry Pi 5
- PiSugar WhisPlay HAT / WM8960 audio
- Node.js 20 + TypeScript
- Python 3
- Primary runtime AI configuration currently uses Gemini for LLM/TTS/Vision and Vosk for ASR.

## Current Volume Configuration

Startup speaker volume is currently set to **80%**.

The value is configured in `.env`. Runtime/startup code should respect the `.env` value rather than introducing another hard-coded default that overrides it.

Do not commit `.env` or API keys/secrets to Git.

## Voice Interaction Baseline

The following real-device flow has previously been confirmed working:

1. Single click starts voice interaction.
2. Audio is recorded from WhisPlay.
3. Vosk performs ASR.
4. Gemini generates the response.
5. Gemini TTS produces speech.
6. Audio is played through WhisPlay.

Preserve this flow when modifying camera, face-recognition, state-machine, ASR, or TTS behavior.

## Camera / Vision

Double-click is used for camera/vision interaction.

A previous issue caused a black camera screen and/or recording to continue around camera transitions. Recording lifecycle and state-transition handling have been modified to reduce these races.

Image capture followed by a Gemini Vision response has previously worked on the device. Continue real-device verification after camera/state-machine changes.

## Async / Recording Race Fixes

Generation-based cancellation has been introduced in asynchronous paths including ASR, TTS, and external reply handling so stale async results do not affect a newer interaction.

Recording lifecycle handling was also changed so a tracked SoX recording process is not forgotten immediately after a stop signal. Preserve the principle that termination should be confirmed before process tracking is cleared.

When changing these areas, avoid replacing generation-based cancellation with simple shared booleans unless there is a clear reason and equivalent race protection.

## Face Recognition

Face-recognition error handling has been improved so failures do not leave recognition/state flags permanently active.

### Web Face Registration

Face-recognition registration is now available through a **Web application**. Treat this as a supported project feature.

When changing face-registration behavior, verify compatibility between:

- Web registration UI/API
- captured/uploaded face data
- identity metadata
- Raspberry Pi face-recognition runtime

Face images and identity information are sensitive biometric data. Do not expose registration endpoints publicly without appropriate access controls, and avoid unnecessary biometric logging.

## Local UI / Display Communication

The local Python UI server and Node display client have previously been configured to use localhost (`127.0.0.1`) for local communication rather than exposing the UI socket on all interfaces unless remote access is intentionally required.

## Audio Notes

WhisPlay audio has previously appeared under the ALSA card name `whisplaysound` with WM8960 hardware.

Prefer stable device/card names over numeric ALSA card indexes where possible because card indexes can change between boots.

Useful diagnostics include:

```bash
aplay -l
cat /proc/asound/cards
cat /proc/asound/pcm
amixer -c whisplaysound scontrols
fuser /dev/snd/*
```

Historical audio troubleshooting involved WM8960 device-tree/driver configuration, ALSA enumeration, PipeWire, and applications holding audio devices. Do not assume every complete-audio failure is an application-code regression.

## Battery Service

The chatbot has previously logged battery-service `ECONNREFUSED` errors while the core chatbot continued running. Treat this as a separate/non-blocking issue unless battery functionality is the task being investigated.

## Verification After Code Changes

At minimum, inspect the repository state and run the relevant project checks:

```bash
git status
npm test
npm run build
git diff
```

Do not claim Raspberry Pi/WhisPlay hardware verification unless the change was actually tested on the device.

For hardware-sensitive changes, verify as applicable:

- startup and configured 80% speaker volume
- single-click voice interaction
- ASR → LLM → TTS round trip
- repeated voice interactions
- double-click camera transition
- visible camera preview/capture
- Vision response
- return from camera to voice interaction
- Web face registration
- recognition of a Web-registered face
- recognition failure does not lock the application

## Codex Working Procedure

Before implementing a task:

1. Read `AGENTS.md`.
2. Read this `PROJECT_STATUS.md`.
3. Run `git status` and inspect recent relevant code/history.
4. Make the smallest reasonable change that preserves known-good behavior.
5. Run relevant tests and `npm run build`.
6. Review `git diff`.
7. Clearly distinguish automated verification from real-device verification.
8. Update this document when the project state materially changes.

## Codex Completion Report

When practical, summarize completed work using:

```text
Task:
<requested work>

Files changed:
- ...

Implementation:
- ...

Tests:
- npm test: PASS / FAIL / NOT RUN
- npm run build: PASS / FAIL / NOT RUN

Hardware test:
- Raspberry Pi: PASS / NOT TESTED
- WhisPlay audio: PASS / NOT TESTED
- Camera: PASS / NOT TESTED
- Face recognition: PASS / NOT TESTED
- Web face registration: PASS / NOT TESTED

Git:
- branch:
- commit:

Remaining issues:
- ...

Recommended next step:
- ...
```

Paste or otherwise share this report with ChatGPT when using ChatGPT as the project-planning/context side of the workflow.