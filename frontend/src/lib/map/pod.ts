/**
 * Probability of Detection (POD) calculations for the frontend.
 */

/**
 * Calculate POD from coverage: POD = 1 - e^(-coverage)
 */
export function calculatePod(coverage: number): number {
  return 1.0 - Math.exp(-coverage);
}

/**
 * Calculate cumulative POD after an additional search pass.
 * P_cum = 1 - (1 - P_existing) * (1 - P_new)
 */
export function cumulativePod(existingPod: number, newPassPod: number): number {
  return 1.0 - (1.0 - existingPod) * (1.0 - newPassPod);
}

/**
 * Calculate coverage from ESW, distance, and area.
 * Coverage = (ESW * distance) / area
 */
export function coverageFromEsw(
  eswMeters: number,
  distanceMeters: number,
  areaSqMeters: number,
): number {
  if (areaSqMeters <= 0) return 0;
  return (eswMeters * distanceMeters) / areaSqMeters;
}

/**
 * Generate a color for a POD value (0-1) on a green-yellow-red gradient.
 * Low POD = red, medium = yellow, high = green.
 */
export function podToColor(pod: number): string {
  const clamped = Math.max(0, Math.min(1, pod));
  if (clamped < 0.5) {
    // Red to yellow
    const r = 255;
    const g = Math.round(clamped * 2 * 255);
    return `rgb(${r}, ${g}, 0)`;
  }
  // Yellow to green
  const r = Math.round((1 - (clamped - 0.5) * 2) * 255);
  const g = 255;
  return `rgb(${r}, ${g}, 0)`;
}

/**
 * Generate a grid of cells for a bounding box with given spacing.
 */
export interface GridCell {
  id: string;
  row: number;
  col: number;
  bounds: {
    north: number;
    south: number;
    east: number;
    west: number;
  };
  searched: boolean;
}

export function generateGrid(
  bounds: { north: number; south: number; east: number; west: number },
  spacingMeters: number,
): GridCell[] {
  // Approximate degrees per meter at the center latitude
  const centerLat = (bounds.north + bounds.south) / 2;
  const latDegPerMeter = 1 / 111320;
  const lonDegPerMeter = 1 / (111320 * Math.cos((centerLat * Math.PI) / 180));

  const latStep = spacingMeters * latDegPerMeter;
  const lonStep = spacingMeters * lonDegPerMeter;

  const cells: GridCell[] = [];
  let row = 0;

  for (let lat = bounds.south; lat < bounds.north; lat += latStep) {
    let col = 0;
    for (let lon = bounds.west; lon < bounds.east; lon += lonStep) {
      cells.push({
        id: `${row}-${col}`,
        row,
        col,
        bounds: {
          south: lat,
          north: Math.min(lat + latStep, bounds.north),
          west: lon,
          east: Math.min(lon + lonStep, bounds.east),
        },
        searched: false,
      });
      col++;
    }
    row++;
  }

  return cells;
}
