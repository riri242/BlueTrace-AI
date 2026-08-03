import axios from "axios";

import { apiClient } from "@/services/apiClient";
import type { AnalysisRequest, AnalysisResponse } from "@/types/analysis";

function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;

    if (typeof detail === "string") {
      return detail;
    }

    if (Array.isArray(detail)) {
      const messages = detail
        .map((item) => {
          if (item && typeof item === "object" && "msg" in item) {
            return String(item.msg);
          }

          return null;
        })
        .filter(Boolean);

      if (messages.length > 0) {
        return messages.join(" ");
      }
    }

    return error.message || "The analysis request failed.";
  }

  return error instanceof Error ? error.message : "The analysis request failed.";
}

export async function submitAnalysis(
  payload: AnalysisRequest
): Promise<AnalysisResponse> {
  const formData = new FormData();
  formData.append("image", payload.image);
  formData.append("date", payload.date);
  formData.append("time", payload.time);
  formData.append("latitude", String(payload.latitude));
  formData.append("longitude", String(payload.longitude));

  try {
    const response = await apiClient.post<AnalysisResponse>(
      "/api/v1/analyze",
      formData
    );

    return response.data;
  } catch (error) {
    throw new Error(getApiErrorMessage(error));
  }
}

