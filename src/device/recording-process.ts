import type { ChildProcess } from "child_process";

const recordingProcesses = new Set<ChildProcess>();
const terminationTimers = new Map<ChildProcess, NodeJS.Timeout[]>();

export const trackRecordingProcess = (child: ChildProcess): void => {
  recordingProcesses.add(child);
};

export const untrackRecordingProcess = (child: ChildProcess): void => {
  recordingProcesses.delete(child);
  const timers = terminationTimers.get(child) || [];
  timers.forEach(clearTimeout);
  terminationTimers.delete(child);
};

export const stopRecordingProcess = (child: ChildProcess): void => {
  if (!recordingProcesses.has(child) || terminationTimers.has(child)) return;

  console.log("Killing recording process", child.pid);
  try {
    child.kill("SIGINT");
  } catch (e) { }

  const terminateTimer = setTimeout(() => {
    if (!recordingProcesses.has(child)) return;
    try {
      child.kill("SIGTERM");
    } catch (e) { }
  }, 250);
  const killTimer = setTimeout(() => {
    if (!recordingProcesses.has(child)) return;
    try {
      child.kill("SIGKILL");
    } catch (e) { }
  }, 1000);
  terminateTimer.unref();
  killTimer.unref();
  terminationTimers.set(child, [terminateTimer, killTimer]);
};

export const stopAllRecordingProcesses = (): void => {
  Array.from(recordingProcesses).forEach(stopRecordingProcess);
};

export const hasRecordingProcesses = (): boolean =>
  recordingProcesses.size > 0;

export const isRecordingProcessTracked = (child: ChildProcess): boolean =>
  recordingProcesses.has(child);
