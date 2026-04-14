/**
 * Export incident data to a JSON file for offline handoff via USB/file transfer.
 * Also supports importing data from an exported file.
 */

import { getAll, getByIncident, putMany } from "./store";
import { getQueuedActions } from "./action-queue";

export interface ExportedData {
  version: 1;
  exportedAt: string;
  incidentId: string;
  incidents: Record<string, unknown>[];
  teams: Record<string, unknown>[];
  segments: Record<string, unknown>[];
  hazards: Record<string, unknown>[];
  clues: Record<string, unknown>[];
  members: Record<string, unknown>[];
  briefings: Record<string, unknown>[];
  pendingActions: Record<string, unknown>[];
}

/**
 * Export all data for an incident to a downloadable JSON file.
 */
export async function exportIncidentData(incidentId: string): Promise<Blob> {
  const [
    incidents,
    teams,
    segments,
    hazards,
    clues,
    members,
    briefings,
    actions,
  ] = await Promise.all([
    getByIncident("incidents", incidentId),
    getByIncident("teams", incidentId),
    getByIncident("segments", incidentId),
    getByIncident("hazards", incidentId),
    getByIncident("clues", incidentId),
    getByIncident("members", incidentId),
    getByIncident("briefings", incidentId),
    getQueuedActions(),
  ]);

  const data: ExportedData = {
    version: 1,
    exportedAt: new Date().toISOString(),
    incidentId,
    incidents,
    teams,
    segments,
    hazards,
    clues,
    members,
    briefings,
    pendingActions: actions.filter((a) =>
      a.url.includes(incidentId),
    ) as unknown as Record<string, unknown>[],
  };

  return new Blob([JSON.stringify(data, null, 2)], {
    type: "application/json",
  });
}

/**
 * Trigger download of exported data.
 */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * Import data from an exported JSON file into local IndexedDB.
 */
export async function importIncidentData(file: File): Promise<string> {
  const text = await file.text();
  const data = JSON.parse(text) as ExportedData;

  if (data.version !== 1) {
    throw new Error(`Unsupported export version: ${data.version}`);
  }

  const incidentId = data.incidentId;

  await Promise.all([
    putMany("incidents", data.incidents, incidentId),
    putMany("teams", data.teams, incidentId),
    putMany("segments", data.segments, incidentId),
    putMany("hazards", data.hazards, incidentId),
    putMany("clues", data.clues, incidentId),
    putMany("members", data.members, incidentId),
    putMany("briefings", data.briefings, incidentId),
  ]);

  return incidentId;
}
