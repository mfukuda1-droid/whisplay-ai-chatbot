const assert = require("node:assert/strict");
const test = require("node:test");

require("ts-node/register/transpile-only");

const {
  splitSentences: realSplitSentences,
  splitTextByLength: realSplitTextByLength,
} = require("../src/utils");

const mockModule = (request, exports) => {
  const id = require.resolve(request);
  require.cache[id] = {
    id,
    filename: id,
    loaded: true,
    exports,
  };
};

const deferred = () => {
  let resolve;
  let reject;
  const promise = new Promise((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
};

const flushPromises = () => new Promise((resolve) => setImmediate(resolve));

let buttonPressedCallback = () => {};
let buttonReleasedCallback = () => {};
let buttonDoubleClickCallback = () => {};
let buttonDown = false;
let dynamicVoiceDetect = async () => 30;
let automaticRecording = async () => "";
let manualRecording = () => ({ result: Promise.resolve(""), stop: () => {} });
let stopRecordingCallCount = 0;
let cameraReleaseCallCount = 0;
const playedAudio = [];

mockModule("../src/device/display", {
  display: () => Promise.resolve(),
  getCurrentStatus: () => ({ text: "", capture_image_path: "" }),
  isButtonDown: () => buttonDown,
  DOUBLE_CLICK_MAX_PRESS_MS: 20,
  onButtonPressed: (callback) => {
    buttonPressedCallback = callback;
  },
  onButtonReleased: (callback) => {
    buttonReleasedCallback = callback || (() => {});
  },
  onButtonDoubleClick: (callback) => {
    buttonDoubleClickCallback = callback || (() => {});
  },
  onCameraCapture: () => {},
  onTextInput: () => {},
});

mockModule("../src/device/audio", {
  getDynamicVoiceDetectLevel: () => dynamicVoiceDetect(),
  playAudioData: async (params) => {
    playedAudio.push(params);
  },
  recordAudio: (...args) => automaticRecording(...args),
  recordAudioManually: (...args) => manualRecording(...args),
  recordFileFormat: "wav",
  stopRecording: () => {
    stopRecordingCallCount += 1;
  },
  stopPlaying: () => {},
});

mockModule("../src/cloud-api/server", {
  chatWithLLMStream: async () => {},
  ttsProcessor: async () => ({ duration: 0 }),
  ttsServer: "test",
});
mockModule("../src/cloud-api/llm", {
  isImMode: false,
  summaryTextWithLLM: async () => "",
});
mockModule("../src/core/Knowledge", {
  getSystemPromptWithKnowledge: async () => "",
});
mockModule("../src/cloud-api/knowledge", { enableRAG: false });
mockModule("../src/utils/dir", { cameraDir: "/tmp" });
mockModule("../src/utils/image", {
  clearPendingCapturedImgForChat: () => {},
  getLatestGenImg: () => "",
  getLatestDisplayImg: () => "",
  setLatestCapturedImg: () => {},
  setPendingCapturedImgForChat: () => {},
});
mockModule("../src/cloud-api/whisplay-im/whisplay-im", {
  sendWhisplayIMMessage: async () => true,
});
mockModule("../src/core/chat-flow/camera-mode", {
  enterCameraMode: () => {},
  handleCameraModePress: () => {},
  handleCameraModeRelease: () => {
    cameraReleaseCallCount += 1;
  },
  onCameraModeExit: () => {},
  resetCameraModeControl: () => {},
});
mockModule("../src/utils", {
  DEFAULT_EMOJI: "😊",
  extractEmojis: () => "",
  getCurrentTimeTag: () => "test",
  getRecordFileDurationMs: async () => 1000,
  purifyTextForTTS: (text) => text,
  splitSentences: realSplitSentences,
  splitTextByLength: realSplitTextByLength,
});
mockModule("../src/device/face-recognition", {
  recognizeFace: async () => ({ name: null }),
});
mockModule("../src/device/music-player", {
  getCurrentTrackTitle: () => "",
  isMusicPlaying: () => false,
  onMusicPlaybackEnd: () => {},
  onMusicTrackChange: () => {},
  startPendingMusicPlayback: () => {},
  stopMusicPlayback: () => {},
});
mockModule("../src/config/local-memory", {
  autoSaveExchange: () => {},
  prepareMemoryPrompt: async () => "",
});
mockModule("../src/device/wakeword", {
  WakeWordListener: class {
    on() {}
    start() {}
    stop() {}
  },
});
mockModule("../src/device/im-bridge", {
  WhisplayIMBridgeServer: class {
    on() {}
    start() {}
  },
});

const {
  flowStates,
  stopActiveRecordingFlow,
} = require("../src/core/chat-flow/states");
const { StreamResponser } = require("../src/core/StreamResponsor");
const ChatFlow = require("../src/core/ChatFlow").default;
const {
  hasRecordingProcesses,
  stopAllRecordingProcesses,
  trackRecordingProcess,
  untrackRecordingProcess,
} = require("../src/device/recording-process");

const createRecordingContext = (initialFlowName) => {
  const transitions = [];
  const ctx = {
    currentFlowName: initialFlowName,
    recordingsDir: "/tmp",
    currentRecordFilePath: "",
    enterMusicAfterAnswer: false,
    musicDisplayText: "",
    isFromWakeListening: false,
    answerId: 0,
    wakeSessionActive: true,
    endAfterAnswer: false,
    wakeRecordMaxSec: 60,
    endWakeSession: () => {},
    transitionTo: (flowName) => {
      if (
        flowName !== ctx.currentFlowName &&
        (ctx.currentFlowName === "listening" ||
          ctx.currentFlowName === "wake_listening")
      ) {
        stopActiveRecordingFlow();
      }
      transitions.push(flowName);
      ctx.currentFlowName = flowName;
    },
  };
  return { ctx, transitions };
};

const createSleepContext = (enableCamera = true) => {
  const transitions = [];
  const ctx = {
    currentFlowName: "sleep",
    enableCamera,
    answerId: 0,
    asrText: "",
    transitionTo: (flowName) => {
      transitions.push(flowName);
      ctx.currentFlowName = flowName;
      if (flowName === "listening" || flowName === "camera") {
        flowStates[flowName](ctx);
      }
    },
  };
  return { ctx, transitions };
};

const createExternalReplyFlow = () => {
  const flow = new ChatFlow();
  const partials = [];
  let endPartialCallCount = 0;
  flow.stateMachine.transitionTo = (flowName) => {
    flow.currentFlowName = flowName;
  };
  flow.currentFlowName = "external_answer";
  flow.streamResponser = {
    partial: (text) => partials.push(text),
    endPartial: () => {
      endPartialCallCount += 1;
    },
  };
  return {
    flow,
    partials,
    getEndPartialCallCount: () => endPartialCallCount,
  };
};

test("日本語の文末記号直後に空白がなくても文を分割する", () => {
  const result = realSplitSentences("こんにちは。今日はどうですか？元気です！");
  assert.deepEqual(result, {
    sentences: ["こんにちは。", "今日はどうですか？", "元気です！"],
    remaining: "",
  });
});

test("LLM8850 MeloTTSでは長い実例を複数TTS単位へ分割する", async () => {
  const calls = [];
  const responder = new StreamResponser(
    async (text) => {
      calls.push(text);
      return { duration: 1, buffer: Buffer.from(text) };
    },
    undefined,
    undefined,
    undefined,
    { maxTTSChunkChars: 45 },
  );
  const text = "こんにちは！ お話しできてとっても嬉しいな！ 今日はどんな一日ですか？私に何かお手伝いできることや、楽しくおしゃべりしたいことがあれば、なんでも気軽に言ってね！";

  responder.partial(text);
  responder.endPartial();
  await responder.getPlayEndPromise();

  assert.deepEqual(calls.map((chunk) => Array.from(chunk).length), [6, 15, 12, 45]);
  assert.equal(calls.join(""), text.replace(/\s+/g, ""));
});

test("LLM8850 MeloTTSでは句読点のない長文もfallback上限以下に分割する", async () => {
  const calls = [];
  const responder = new StreamResponser(
    async (text) => {
      calls.push(text);
      return { duration: 1, buffer: Buffer.from(text) };
    },
    undefined,
    undefined,
    undefined,
    { maxTTSChunkChars: 45 },
  );
  const text = "あ".repeat(100);

  responder.partial(text);
  responder.endPartial();
  await responder.getPlayEndPromise();

  assert.deepEqual(calls.map((chunk) => Array.from(chunk).length), [45, 45, 10]);
  assert.equal(calls.join(""), text);
});

test("LLM8850 MeloTTSでも短い日本語1文は1回だけTTSする", async () => {
  const calls = [];
  const responder = new StreamResponser(
    async (text) => {
      calls.push(text);
      return { duration: 1, buffer: Buffer.from(text) };
    },
    undefined,
    undefined,
    undefined,
    { maxTTSChunkChars: 45 },
  );

  responder.partial("短い文章です。");
  responder.endPartial();
  await responder.getPlayEndPromise();

  assert.deepEqual(calls, ["短い文章です。"]);
});

test("他のTTS Providerには長さfallbackを適用しない", async () => {
  const calls = [];
  const responder = new StreamResponser(async (text) => {
    calls.push(text);
    return { duration: 1, buffer: Buffer.from(text) };
  });
  const text = "あ".repeat(100);

  responder.partial(text);
  responder.endPartial();
  await responder.getPlayEndPromise();

  assert.deepEqual(calls, [text]);
});

test("複数TTS chunkは生成完了順に関係なく元文章順で再生する", async () => {
  playedAudio.length = 0;
  const delays = new Map([
    ["一文目です。", 1],
    ["二文目です。", 30],
    ["三文目です。", 5],
  ]);
  const responder = new StreamResponser(async (text) => {
    await new Promise((resolve) => setTimeout(resolve, delays.get(text) || 1));
    return { duration: 1, buffer: Buffer.from(text) };
  });

  responder.partial("一文目です。二文目です。三文目です。");
  responder.endPartial();
  await responder.getPlayEndPromise();

  assert.deepEqual(
    playedAudio.map((item) => item.buffer.toString()),
    ["一文目です。", "二文目です。", "三文目です。"],
  );
});

test("キャンセル済みASRの古い結果をanswerへ反映しない", async () => {
  const asrA = deferred();
  const asrB = deferred();
  const asrPromises = [asrA.promise, asrB.promise];
  const transitions = [];
  const ctx = {
    currentFlowName: "asr",
    currentRecordFilePath: "/tmp/test.wav",
    isFromWakeListening: false,
    asrText: "",
    endAfterAnswer: false,
    wakeSessionActive: false,
    recognizeAudio: () => asrPromises.shift(),
    shouldEndAfterAnswer: () => false,
    shouldContinueWakeSession: () => false,
    endWakeSession: () => {},
    transitionTo: (flowName) => {
      transitions.push(flowName);
      ctx.currentFlowName = flowName;
    },
  };

  flowStates.asr(ctx);
  buttonPressedCallback();
  await flushPromises();
  assert.equal(ctx.currentFlowName, "listening");

  ctx.currentFlowName = "asr";
  flowStates.asr(ctx);
  asrA.resolve("古い認識結果");
  await flushPromises();

  assert.equal(ctx.asrText, "");
  assert.equal(ctx.currentFlowName, "asr");
  assert.equal(transitions.includes("answer"), false);

  asrB.resolve("新しい認識結果");
  await flushPromises();

  assert.equal(ctx.asrText, "新しい認識結果");
  assert.equal(ctx.currentFlowName, "answer");
});

test("stop済みTTSの古い音声を再生しない", async () => {
  playedAudio.length = 0;
  const ttsA = deferred();
  const ttsB = deferred();
  const responder = new StreamResponser((text) =>
    text === "A." ? ttsA.promise : ttsB.promise,
  );

  responder.partial("A.");
  responder.stop();
  responder.partial("B.");

  ttsA.resolve({ duration: 100, buffer: Buffer.from("old") });
  await flushPromises();
  assert.equal(playedAudio.length, 0);

  ttsB.resolve({ duration: 100, buffer: Buffer.from("new") });
  await flushPromises();
  await flushPromises();

  assert.equal(playedAudio.length, 1);
  assert.deepEqual(playedAudio[0].buffer, Buffer.from("new"));
});

test("古いTTSのfinallyが新しい世代のカウンターを変更しない", async () => {
  const ttsA = deferred();
  const ttsB = deferred();
  let callCount = 0;
  const responder = new StreamResponser(() =>
    ++callCount === 1 ? ttsA.promise : ttsB.promise,
  );

  const generationA = responder.generation;
  const promiseA = responder.enqueueLimitedTTS("A", generationA);
  responder.stop();
  const generationB = responder.generation;
  const promiseB = responder.enqueueLimitedTTS("B", generationB);

  assert.equal(responder.activeTTSCount, 1);
  ttsA.resolve({ duration: 100, buffer: Buffer.from("old") });
  await flushPromises();
  assert.equal(responder.activeTTSCount, 1);

  ttsB.resolve({ duration: 100, buffer: Buffer.from("new") });
  await Promise.all([promiseA, promiseB]);
  await flushPromises();
  assert.equal(responder.activeTTSCount, 0);
});

test("wake_listening離脱後は遅延した音量測定から自動録音を開始しない", async () => {
  const voiceLevel = deferred();
  let automaticRecordingCallCount = 0;
  dynamicVoiceDetect = () => voiceLevel.promise;
  automaticRecording = async () => {
    automaticRecordingCallCount += 1;
    return "";
  };
  stopRecordingCallCount = 0;
  const { ctx } = createRecordingContext("wake_listening");

  flowStates.wake_listening(ctx);
  buttonPressedCallback();
  voiceLevel.resolve(30);
  await flushPromises();

  assert.equal(ctx.currentFlowName, "listening");
  assert.equal(automaticRecordingCallCount, 0);
  assert.equal(stopRecordingCallCount, 1);
});

test("wake_listening離脱後は古い自動録音完了からasrへ遷移しない", async () => {
  const recording = deferred();
  let automaticRecordingCallCount = 0;
  dynamicVoiceDetect = async () => 30;
  automaticRecording = () => {
    automaticRecordingCallCount += 1;
    return recording.promise;
  };
  stopRecordingCallCount = 0;
  const { ctx, transitions } = createRecordingContext("wake_listening");

  flowStates.wake_listening(ctx);
  await flushPromises();
  assert.equal(automaticRecordingCallCount, 1);

  buttonPressedCallback();
  recording.resolve("");
  await flushPromises();

  assert.equal(ctx.currentFlowName, "listening");
  assert.equal(transitions.includes("asr"), false);
  assert.equal(stopRecordingCallCount, 1);
});

test("listening任意離脱後は古い手動録音完了からasrへ遷移しない", async () => {
  const recording = deferred();
  let manualStopCallCount = 0;
  buttonDown = true;
  manualRecording = () => ({
    result: recording.promise,
    stop: () => {
      manualStopCallCount += 1;
    },
  });
  stopRecordingCallCount = 0;
  const { ctx, transitions } = createRecordingContext("listening");

  flowStates.listening(ctx);
  ctx.transitionTo("external_answer");
  recording.resolve("");
  await flushPromises();

  assert.equal(ctx.currentFlowName, "external_answer");
  assert.equal(transitions.includes("asr"), false);
  assert.equal(stopRecordingCallCount, 1);
  assert.equal(manualStopCallCount, 0);
  buttonDown = false;
});

test("camera遷移後の古いlistening処理は手動録音を開始しない", () => {
  let manualRecordingCallCount = 0;
  buttonDown = true;
  manualRecording = () => {
    manualRecordingCallCount += 1;
    return { result: Promise.resolve(""), stop: () => {} };
  };
  const { ctx } = createRecordingContext("camera");

  flowStates.listening(ctx);

  assert.equal(ctx.currentFlowName, "camera");
  assert.equal(manualRecordingCallCount, 0);
  buttonDown = false;
});

test("listeningからcameraへ遷移すると録音を停止し古い完了を無視する", async () => {
  const recording = deferred();
  buttonDown = true;
  manualRecording = () => ({ result: recording.promise, stop: () => {} });
  stopRecordingCallCount = 0;
  const { ctx, transitions } = createRecordingContext("listening");

  flowStates.listening(ctx);
  ctx.transitionTo("camera");
  flowStates.camera(ctx);
  recording.resolve("");
  await flushPromises();

  assert.equal(ctx.currentFlowName, "camera");
  assert.equal(transitions.includes("asr"), false);
  assert.equal(stopRecordingCallCount, 2);
  buttonDown = false;
});

test("通常の長押し録音はrelease後にasrへ遷移する", async () => {
  const recording = deferred();
  buttonDown = true;
  manualRecording = () => ({
    result: recording.promise,
    stop: () => recording.resolve("/tmp/manual.wav"),
  });
  const { ctx, transitions } = createRecordingContext("listening");
  const originalDateNow = Date.now;
  let now = 1000;
  Date.now = () => now;

  try {
    flowStates.listening(ctx);
    now = 1600;
    buttonReleasedCallback();
    await flushPromises();
  } finally {
    Date.now = originalDateNow;
    buttonDown = false;
  }

  assert.equal(ctx.currentFlowName, "asr");
  assert.equal(transitions.includes("asr"), true);
});

test("停止シグナル送信後もexitまではSoX録音プロセスを追跡する", () => {
  const signals = [];
  const fakeProcess = {
    pid: 12345,
    kill: (signal) => {
      signals.push(signal);
      return true;
    },
  };

  trackRecordingProcess(fakeProcess);
  stopAllRecordingProcesses();

  assert.deepEqual(signals, ["SIGINT"]);
  assert.equal(hasRecordingProcesses(), true);

  untrackRecordingProcess(fakeProcess);
  assert.equal(hasRecordingProcesses(), false);
});

test("sleepのダブルクリックでは録音せずcameraへ1回だけ遷移する", async () => {
  let manualRecordingCallCount = 0;
  manualRecording = () => {
    manualRecordingCallCount += 1;
    return { result: Promise.resolve(""), stop: () => {} };
  };
  const { ctx, transitions } = createSleepContext();
  flowStates.sleep(ctx);

  buttonDown = true;
  buttonPressedCallback();
  buttonDown = false;
  buttonReleasedCallback();
  buttonDown = true;
  buttonPressedCallback();
  buttonDown = false;
  buttonReleasedCallback();
  buttonDoubleClickCallback();
  await new Promise((resolve) => setTimeout(resolve, 50));

  assert.equal(manualRecordingCallCount, 0);
  assert.equal(transitions.filter((flow) => flow === "camera").length, 1);
  assert.equal(ctx.currentFlowName, "camera");
});

test("sleepの長押しではlistening録音を開始してrelease後にasrへ進む", async () => {
  const recording = deferred();
  let manualRecordingCallCount = 0;
  manualRecording = () => {
    manualRecordingCallCount += 1;
    return {
      result: recording.promise,
      stop: () => recording.resolve("/tmp/manual.wav"),
    };
  };
  const { ctx, transitions } = createSleepContext();
  const originalDateNow = Date.now;
  let now = 1000;
  Date.now = () => now;

  try {
    flowStates.sleep(ctx);
    buttonDown = true;
    buttonPressedCallback();
    await new Promise((resolve) => setTimeout(resolve, 50));
    assert.equal(manualRecordingCallCount, 1);
    now = 1600;
    buttonDown = false;
    buttonReleasedCallback();
    await flushPromises();
  } finally {
    Date.now = originalDateNow;
    buttonDown = false;
  }

  assert.equal(transitions.includes("listening"), true);
  assert.equal(ctx.currentFlowName, "asr");
});

test("sleepの短い単クリックでは録音せずsleepを維持する", async () => {
  let manualRecordingCallCount = 0;
  manualRecording = () => {
    manualRecordingCallCount += 1;
    return { result: Promise.resolve(""), stop: () => {} };
  };
  const { ctx, transitions } = createSleepContext();
  flowStates.sleep(ctx);

  buttonDown = true;
  buttonPressedCallback();
  buttonDown = false;
  buttonReleasedCallback();
  await new Promise((resolve) => setTimeout(resolve, 50));

  assert.equal(manualRecordingCallCount, 0);
  assert.deepEqual(transitions, []);
  assert.equal(ctx.currentFlowName, "sleep");
});

test("camera状態のクリックでは従来どおりcapture処理を呼ぶ", () => {
  cameraReleaseCallCount = 0;
  const { ctx } = createSleepContext();
  ctx.currentFlowName = "camera";
  flowStates.camera(ctx);

  buttonPressedCallback();
  buttonReleasedCallback();

  assert.equal(cameraReleaseCallCount, 1);
});

test("external_answer離脱後は残りの文章を投入しない", async () => {
  const { flow, partials, getEndPartialCallCount } = createExternalReplyFlow();

  const producer = flow.streamExternalReply("文1。文2。文3。");
  assert.deepEqual(partials, ["文1。"]);
  flow.transitionTo("listening");
  await producer;

  assert.deepEqual(partials, ["文1。"]);
  assert.equal(getEndPartialCallCount(), 0);
});

test("新しいexternal replyは古いproducerの残りとendPartialを無効化する", async () => {
  const { flow, partials, getEndPartialCallCount } = createExternalReplyFlow();

  const producerA = flow.streamExternalReply("A1。A2。");
  const producerB = flow.streamExternalReply("B1。B2。");
  await Promise.all([producerA, producerB]);

  assert.deepEqual(partials, ["A1。", "B1。", "B2。"]);
  assert.equal(getEndPartialCallCount(), 1);
});

test("通常のexternal replyは全文を順番に投入してendPartialする", async () => {
  const { flow, partials, getEndPartialCallCount } = createExternalReplyFlow();

  await flow.streamExternalReply("文1。文2。文3。");

  assert.deepEqual(partials, ["文1。", "文2。", "文3。"]);
  assert.equal(getEndPartialCallCount(), 1);
});
