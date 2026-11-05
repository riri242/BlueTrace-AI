import { useMutation } from "@tanstack/react-query";

import { submitDriftEstimate } from "@/services/driftService";
import type { DriftRequest, DriftResponse } from "@/types/drift";

export function useDriftEstimate() {
  return useMutation<DriftResponse, Error, DriftRequest>({
    mutationFn: submitDriftEstimate
  });
}
