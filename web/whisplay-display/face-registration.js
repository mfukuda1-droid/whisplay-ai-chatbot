const form = document.getElementById("registrationForm");
const disabledPanel = document.getElementById("disabledPanel");
const disabledMessage = document.getElementById("disabledMessage");
const nameInput = document.getElementById("personName");
const preview = document.getElementById("cameraPreview");
const emptyPreview = document.getElementById("emptyPreview");
const startButton = document.getElementById("startCamera");
const consent = document.getElementById("consent");
const registerButton = document.getElementById("registerButton");
const message = document.getElementById("message");
const cameraHint = document.getElementById("cameraHint");

let previewTimer = null;
let cameraReady = false;
let isSubmitting = false;

function showMessage(text, type = "") {
  message.textContent = text;
  message.className = `message ${type}`.trim();
}

function updateSubmitState() {
  registerButton.disabled = !cameraReady || isSubmitting;
}

function refreshPreview() {
  preview.src = `/camera?revision=${Date.now()}`;
}

async function startPiCameraPreview() {
  startButton.disabled = true;
  emptyPreview.hidden = false;
  emptyPreview.textContent = "Piカメラに接続しています…";
  try {
    const response = await fetch("/api/faces/camera/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
    const result = await response.json();
    if (!response.ok || !result.ok) throw new Error(result.reason || "camera_unavailable");
    cameraReady = true;
    preview.hidden = false;
    refreshPreview();
    if (previewTimer) clearInterval(previewTimer);
    previewTimer = setInterval(refreshPreview, 300);
    cameraHint.textContent = "登録ボタンを押した時点で、Piカメラから新しい写真を撮影します。";
    showMessage("");
  } catch {
    cameraReady = false;
    preview.hidden = true;
    emptyPreview.textContent = "Piカメラのプレビューを開始できませんでした";
    cameraHint.textContent = "カメラdaemonと接続を確認してから、再接続してください。";
    showMessage("Piカメラに接続できません。", "error");
  } finally {
    startButton.disabled = false;
    updateSubmitState();
  }
}

preview.addEventListener("load", () => {
  cameraReady = true;
  emptyPreview.hidden = true;
  updateSubmitState();
});
preview.addEventListener("error", () => {
  emptyPreview.hidden = false;
  emptyPreview.textContent = "Piカメラの映像を待っています…";
});

const errorMessages = {
  invalid_name: "名前には文字、数字、空白、一部の記号のみ使用できます（40文字以内）。",
  camera_disabled: "ENABLE_CAMERA=true を設定してチャットボットを再起動してください。",
  camera_unavailable: "Piカメラdaemonに接続できません。",
  camera_capture_failed: "Piカメラで撮影できませんでした。カメラの接続を確認してください。",
  no_face_detected: "顔を検出できませんでした。明るい場所で正面を向いてください。",
  multiple_faces_detected: "複数の顔が写っています。登録する1人だけがカメラに入るようにしてください。",
  registration_disabled: "サーバー側で顔登録機能が無効になっています。",
  registration_failed: "登録処理に失敗しました。サーバーのログを確認してください。",
};

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!cameraReady) {
    showMessage("Piカメラの接続を待ってください。", "error");
    return;
  }
  isSubmitting = true;
  updateSubmitState();
  showMessage("Piカメラで撮影し、顔を登録しています…");
  try {
    const response = await fetch("/api/faces/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: nameInput.value }),
    });
    const result = await response.json();
    if (!response.ok || !result.ok) throw new Error(result.reason || "registration_failed");
    showMessage(`${result.name}さんを登録しました（登録画像 ${result.sampleCount} 枚）。`, "success");
  } catch (error) {
    showMessage(errorMessages[error.message] || errorMessages.registration_failed, "error");
  } finally {
    isSubmitting = false;
    updateSubmitState();
  }
});

startButton.addEventListener("click", startPiCameraPreview);
window.addEventListener("pagehide", () => {
  if (previewTimer) clearInterval(previewTimer);
  fetch("/api/faces/camera/stop", { method: "POST", keepalive: true }).catch(() => {});
});

fetch("/api/faces/status")
  .then((response) => response.json())
  .then(({ enabled, cameraEnabled }) => {
    const available = enabled && cameraEnabled;
    form.hidden = !available;
    disabledPanel.hidden = available;
    if (!enabled) {
      disabledMessage.innerHTML = "<code>FACE_REGISTRATION_WEB_ENABLED=true</code> を設定してチャットボットを再起動してください。";
    } else if (!cameraEnabled) {
      disabledMessage.innerHTML = "<code>ENABLE_CAMERA=true</code> を設定してチャットボットを再起動してください。";
    } else {
      startPiCameraPreview();
    }
  })
  .catch(() => {
    form.hidden = true;
    disabledPanel.hidden = false;
    disabledMessage.textContent = "サーバーの状態を確認できませんでした。";
  });
