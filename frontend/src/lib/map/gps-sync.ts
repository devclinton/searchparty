/**
 * Sync GPS tracks from local IndexedDB to the server.
 */

import {
  getTrackPoints,
  getUnsyncedTracks,
  markTrackSynced,
} from "./gps-store";

export async function syncGpsTracks(
  apiBase: string,
  accessToken: string,
): Promise<number> {
  const unsynced = await getUnsyncedTracks();
  let synced = 0;

  for (const track of unsynced) {
    if (!track.endedAt) continue; // Only sync completed tracks

    const points = await getTrackPoints(track.id);
    if (points.length === 0) continue;

    try {
      const response = await fetch(`${apiBase}/api/v1/gps/tracks`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          track_id: track.id,
          incident_id: track.incidentId,
          team_id: track.teamId,
          started_at: new Date(track.startedAt).toISOString(),
          ended_at: track.endedAt
            ? new Date(track.endedAt).toISOString()
            : null,
          points: points.map((p) => ({
            lat: p.lat,
            lon: p.lon,
            altitude: p.altitude,
            accuracy: p.accuracy,
            timestamp: new Date(p.timestamp).toISOString(),
          })),
        }),
      });

      if (response.ok) {
        await markTrackSynced(track.id);
        synced++;
      }
    } catch {
      // Network error — will retry on next sync
    }
  }

  return synced;
}
