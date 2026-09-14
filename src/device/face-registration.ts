import fs from "fs";
import path from "path";
import { randomUUID } from "crypto";
import { Socket } from "net";
import { spawn } from "child_process";
import { dataDir } from "../utils/dir";

const NAME_PATTERN = /^[\p{L}\p{N}][\p{L}\p{N}\p{M} ._'’・-]{0,39}$/u;

export type FaceRegistrationFailure =
  | "invalid_name"
  | "camera_disabled"
  | "camera_unavailable"
  | "camera_capture_failed"
  | "no_face_detected"
  | "multiple_faces_detected"
  | "registration_failed";

export interface FaceRegistrationResult {
  ok: boolean;
  name?: string;
  sampleCount?: number;
  reason?: FaceRegistrationFailure;
}

interface FaceRegistrationServiceOptions {
  pythonBinary?: string;
  scriptPath?: string;
  captureDir?: string;
  encodingsPath?: string;
  captureImage?: (targetPath: string) => Promise<void>;
}

interface CameraDaemonResponse {
  ok?: boolean;
  error?: string;
  [key: string]: unknown;
}

export function normalizeFaceName(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const name = value.trim().replace(/\s+/g, " ");
  return NAME_PATTERN.test(name) ? name : null;
}

export function requestPiCamera(
  command: "status" | "start_stream" | "stop_stream" | "capture",
  payload: Record<string, unknown> = {},
): Promise<CameraDaemonResponse> {
  return new Promise((resolve, reject) => {
    const port = parseInt(process.env.WHISPLAY_CAMERA_DAEMON_PORT || "18765", 10);
    const socket = new Socket();
    let response = "";
    let settled = false;

    const finishWithError = (error: Error) => {
      if (settled) return;
      settled = true;
      socket.destroy();
      reject(error);
    };

    socket.setTimeout(5000);
    socket.connect(port, "127.0.0.1", () => {
      socket.write(`${JSON.stringify({ cmd: command, ...payload })}\n`);
    });
    socket.on("data", (chunk) => {
      response += chunk.toString();
      const newline = response.indexOf("\n");
      if (newline < 0 || settled) return;
      try {
        const result = JSON.parse(response.slice(0, newline));
        settled = true;
        socket.end();
        resolve(result);
      } catch {
        finishWithError(new Error("Invalid camera daemon response"));
      }
    });
    socket.on("error", (error) => finishWithError(error));
    socket.on("timeout", () => finishWithError(new Error("Camera daemon timeout")));
    socket.on("close", () => {
      if (!settled) finishWithError(new Error("Camera daemon closed without a response"));
    });
  });
}

export class FaceRegistrationService {
  private readonly pythonBinary: string;
  private readonly scriptPath: string;
  private readonly captureDir: string;
  private readonly encodingsPath: string;
  private readonly captureImage: (targetPath: string) => Promise<void>;
  private readonly usesInjectedCamera: boolean;

  constructor(options: FaceRegistrationServiceOptions = {}) {
    const projectRoot = path.resolve(__dirname, "../..");
    this.pythonBinary =
      options.pythonBinary || process.env.FACE_RECOGNITION_PYTHON_PATH || "python3";
    this.scriptPath =
      options.scriptPath || path.join(projectRoot, "python", "register_face.py");
    this.captureDir =
      options.captureDir || path.join(dataDir, "known_faces", ".captures");
    this.encodingsPath =
      options.encodingsPath ||
      process.env.FACE_ENCODINGS_PATH ||
      path.join(dataDir, "known_faces", "encodings.pkl");
    this.usesInjectedCamera = Boolean(options.captureImage);
    this.captureImage = options.captureImage || (async (targetPath) => {
      const response = await requestPiCamera("capture", { path: targetPath });
      if (!response.ok) throw new Error(response.error || "Pi camera capture failed");
    });
  }

  async registerFromPiCamera(nameValue: unknown): Promise<FaceRegistrationResult> {
    const name = normalizeFaceName(nameValue);
    if (!name) return { ok: false, reason: "invalid_name" };
    if (process.env.ENABLE_CAMERA !== "true" && !this.usesInjectedCamera) {
      return { ok: false, reason: "camera_disabled" };
    }

    await fs.promises.mkdir(this.captureDir, { recursive: true });
    const capturePath = path.join(this.captureDir, `${randomUUID()}.jpg`);
    try {
      try {
        await this.captureImage(capturePath);
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        console.error("[face-registration] Pi camera capture failed:", message);
        return {
          ok: false,
          reason: /ECONNREFUSED|timeout|closed/i.test(message)
            ? "camera_unavailable"
            : "camera_capture_failed",
        };
      }
      if (!fs.existsSync(capturePath)) {
        return { ok: false, reason: "camera_capture_failed" };
      }
      return await this.runRegistration(name, capturePath);
    } finally {
      await fs.promises.unlink(capturePath).catch(() => {});
    }
  }

  private runRegistration(name: string, imagePath: string): Promise<FaceRegistrationResult> {
    return new Promise((resolve) => {
      const child = spawn(this.pythonBinary, [this.scriptPath, name, imagePath], {
        env: { ...process.env, FACE_ENCODINGS_PATH: this.encodingsPath },
        stdio: ["ignore", "pipe", "pipe"],
      });
      let stdout = "";
      let stderr = "";
      child.stdout.on("data", (chunk) => {
        if (stdout.length < 16_384) stdout += chunk.toString();
      });
      child.stderr.on("data", (chunk) => {
        if (stderr.length < 16_384) stderr += chunk.toString();
      });
      child.on("error", (error) => {
        console.error("[face-registration] failed to start:", error.message);
        resolve({ ok: false, reason: "registration_failed" });
      });
      child.on("close", () => {
        try {
          const result = JSON.parse(stdout.trim());
          if (result?.ok === true) {
            resolve({ ok: true, name, sampleCount: Number(result.sample_count) || 1 });
            return;
          }
          if (result?.reason === "no_face_detected" || result?.reason === "multiple_faces_detected") {
            resolve({ ok: false, reason: result.reason });
            return;
          }
        } catch {}
        if (stderr.trim()) console.error("[face-registration] script error:", stderr.trim());
        resolve({ ok: false, reason: "registration_failed" });
      });
    });
  }
}

export const faceRegistrationService = new FaceRegistrationService();
