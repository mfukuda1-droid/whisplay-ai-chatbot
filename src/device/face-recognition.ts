import { spawn } from "child_process";

const pythonBinary = process.env.FACE_RECOGNITION_PYTHON_PATH || "python3";
const scriptPath = "python/recognize_face.py"; // プロジェクトルートからの相対パス（chatbotはルートで起動される想定）

export interface FaceRecognitionResult {
  name: string | null;
  distance?: number;
  reason?: string;
}

export function recognizeFace(imagePath: string): Promise<FaceRecognitionResult> {
  return new Promise((resolve) => {
    const proc = spawn(pythonBinary, [scriptPath, imagePath]);
    let output = "";
    let errOutput = "";

    proc.stdout.on("data", (d) => (output += d.toString()));
    proc.stderr.on("data", (d) => (errOutput += d.toString()));

    proc.on("close", (code) => {
      if (code !== 0) {
        console.error("[face-recognition] script exited with error:", errOutput);
        resolve({ name: null, reason: "script_error" });
        return;
      }
      try {
        resolve(JSON.parse(output.trim()));
      } catch (e) {
        console.error("[face-recognition] failed to parse output:", output);
        resolve({ name: null, reason: "parse_error" });
      }
    });

    proc.on("error", (err) => {
      console.error("[face-recognition] failed to spawn python process:", err);
      resolve({ name: null, reason: "spawn_error" });
    });
  });
}
