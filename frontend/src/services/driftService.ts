import axios from "axios";

import { apiClient } from "@/services/apiClient";
import type { DriftRequest, DriftResponse } from "@/types/drift";

export async function submitDriftEstimate(payload: DriftRequest): Promise<DriftResponse> {
  try {
    const response = await apiClient.post<DriftResponse>("/api/v1/drift/estimate", payload);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const detail = error.response?.data?.detail;
      if (typeof detail === "string") throw new Error(detail);
      if (Array.isArray(detail)) {
        const messages = detail.map((item) => item?.msg).filter(Boolean);
        if (messages.length) throw new Error(messages.join(" "));
      }
      throw new Error(error.message || "Drift estimate request failed.");
    }
    throw error instanceof Error ? error : new Error("Drift estimate request failed.");
  }
}
