import { useMutation } from "@tanstack/react-query";

import { submitAnalysis } from "@/services/analysisService";
import type { AnalysisRequest, AnalysisResponse } from "@/types/analysis";

export function useAnalyzeSubmission() {
  return useMutation<AnalysisResponse, Error, AnalysisRequest>({
    mutationFn: submitAnalysis
  });
}

