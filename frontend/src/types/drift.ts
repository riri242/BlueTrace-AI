export interface DriftRequest {
  date: string;
  time: string;
  latitude: number;
  longitude: number;
  hours: number;
}

export interface DriftPoint {
  observed_at: string;
  latitude: number;
  longitude: number;
}

export interface DriftResponse {
  status: "experimental" | "unavailable";
  observation_date: string;
  observation_time: string;
  hours_requested: number;
  hours_traced: number;
  anchor_time: string | null;
  observation_offset_minutes: number | null;
  coastline_status: "not_checked" | "potential_land_crossing" | "clear_on_reference_map";
  source: string;
  method: string;
  path: DriftPoint[];
  message: string;
  limitations: string;
}
