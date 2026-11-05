import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useForm } from "react-hook-form";

import { FileUpload } from "@/components/forms/FileUpload";
import { MontereyMap } from "@/components/map/MontereyMap";
import { DriftPathMap } from "@/components/map/DriftPathMap";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { LoadingScreen } from "@/components/ui/LoadingScreen";
import { useAnalyzeSubmission } from "@/hooks/useAnalyzeSubmission";
import { useDriftEstimate } from "@/hooks/useDriftEstimate";
import { useImagePreview } from "@/hooks/useImagePreview";
import type { Coordinates } from "@/types/analysis";

interface AnalysisFormValues {
  date: string;
  image: File | null;
  location: Coordinates | null;
  time: string;
}

const maxPhotoDate = new Date().toISOString().slice(0, 10);

export function AnalysisPage() {
  const mutation = useAnalyzeSubmission();
  const driftMutation = useDriftEstimate();
  const [driftHours, setDriftHours] = useState(24);
  const {
    formState: { errors },
    handleSubmit,
    register,
    setValue,
    watch
  } = useForm<AnalysisFormValues>({
    defaultValues: {
      date: "",
      image: null,
      location: null,
      time: ""
    },
    mode: "onChange"
  });

  useEffect(() => {
    register("image", {
      validate: (value) => value instanceof File || "Image is required."
    });
    register("location", {
      validate: (value) => Boolean(value) || "Observation site is required."
    });
  }, [register]);

  const selectedImage = watch("image");
  const selectedDate = watch("date");
  const selectedTime = watch("time");
  const selectedLocation = watch("location");
  const previewUrl = useImagePreview(selectedImage);
  const canAnalyze =
    selectedImage instanceof File &&
    Boolean(selectedDate) &&
    Boolean(selectedTime) &&
    Boolean(selectedLocation);

  const runDrift = () => {
    if (!selectedDate || !selectedTime || !selectedLocation) return;
    driftMutation.mutate({
      date: selectedDate,
      time: selectedTime,
      latitude: selectedLocation.latitude,
      longitude: selectedLocation.longitude,
      hours: driftHours
    });
  };

  const onSubmit = (values: AnalysisFormValues) => {
    if (!(values.image instanceof File) || !values.location) {
      return;
    }

    mutation.mutate({
      date: values.date,
      image: values.image,
      latitude: values.location.latitude,
      longitude: values.location.longitude,
      time: values.time
    });
  };

  return (
    <div className="mx-auto max-w-7xl px-5 py-10 sm:px-8 lg:py-14">
      {mutation.isPending ? <LoadingScreen /> : null}

      <motion.div
        animate={{ opacity: 1, y: 0 }}
        className="mb-8 max-w-3xl"
        initial={{ opacity: 0, y: 12 }}
        transition={{ duration: 0.45, ease: "easeOut" }}
      >
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-ocean-600">
          California coast observation
        </p>
        <h1 className="mt-3 text-4xl font-semibold tracking-tight text-research-ink sm:text-5xl">
          Analysis Intake
        </h1>
        <p className="mt-4 text-lg leading-8 text-research-muted">
          Provide the field image, observation time, and a single coastal
          location for the Milestone 1 API workflow.
        </p>
      </motion.div>

      <form className="space-y-6" onSubmit={handleSubmit(onSubmit)}>
        <div className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
          <Card>
            <FileUpload
              error={errors.image?.message}
              file={selectedImage}
              onFileSelect={(file) => {
                mutation.reset();
                driftMutation.reset();
                setValue("image", file, {
                  shouldDirty: true,
                  shouldValidate: true
                });
              }}
              previewUrl={previewUrl}
            />
          </Card>

          <Card className="lg:row-span-2">
            <div className="mb-5">
              <p className="text-sm font-semibold uppercase tracking-[0.18em] text-ocean-600">
                Observation Site
              </p>
              <h2 className="mt-2 text-2xl font-semibold text-research-ink">
                California Coast Map
              </h2>
            </div>
            <MontereyMap
              error={errors.location?.message}
              onChange={(coordinates) => {
                mutation.reset();
                driftMutation.reset();
                setValue("location", coordinates, {
                  shouldDirty: true,
                  shouldValidate: true
                });
              }}
              value={selectedLocation}
            />
          </Card>

          <Card>
            <div className="grid gap-5 sm:grid-cols-2">
              <label className="space-y-2" htmlFor="photo-date">
                <span className="text-sm font-semibold text-research-ink">
                  Date Picker
                </span>
                <input
                  className="min-h-12 w-full rounded-xl border border-research-line bg-white px-4 text-research-ink outline-none transition focus:border-ocean-500 focus:ring-4 focus:ring-ocean-100"
                  id="photo-date"
                  max={maxPhotoDate}
                  type="date"
                  {...register("date", {
                    required: "Date is required."
                  })}
                />
                {errors.date ? (
                  <span className="text-sm font-medium text-red-700">
                    {errors.date.message}
                  </span>
                ) : null}
              </label>

              <label className="space-y-2" htmlFor="photo-time">
                <span className="text-sm font-semibold text-research-ink">
                  Approximate Time Picker
                </span>
                <input
                  aria-describedby="time-help"
                  className="min-h-12 w-full rounded-xl border border-research-line bg-white px-4 text-research-ink outline-none transition focus:border-ocean-500 focus:ring-4 focus:ring-ocean-100"
                  id="photo-time"
                  type="time"
                  {...register("time", {
                    required: "Time is required."
                  })}
                />
                <span className="block text-sm text-research-muted" id="time-help">
                  Approximate time is acceptable.
                </span>
                {errors.time ? (
                  <span className="text-sm font-medium text-red-700">
                    {errors.time.message}
                  </span>
                ) : null}
              </label>
            </div>
          </Card>
        </div>

        <div className="flex flex-col gap-4 rounded-2xl border border-research-line bg-white/82 p-5 shadow-research sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm leading-6 text-research-muted">
            Image, date, time, and California coast observation site are required before
            submission.
          </p>
          <div className="flex flex-wrap items-center gap-3">
            <label className="text-sm font-medium text-research-ink" htmlFor="drift-hours">
              Drift history (hours)
            </label>
            <select
              className="min-h-11 rounded-xl border border-research-line bg-white px-3 text-research-ink"
              id="drift-hours"
              value={driftHours}
              onChange={(event) => {
                setDriftHours(Number(event.target.value));
                driftMutation.reset();
              }}
            >
              <option value={6}>6</option>
              <option value={12}>12</option>
              <option value={24}>24</option>
              <option value={48}>48</option>
              <option value={72}>72</option>
            </select>
            <Button
              disabled={!selectedDate || !selectedTime || !selectedLocation || driftMutation.isPending}
              isLoading={driftMutation.isPending}
              size="lg"
              type="button"
              onClick={runDrift}
            >
              Estimate Drift
            </Button>
          </div>
          <Button
            disabled={!canAnalyze}
            isLoading={mutation.isPending}
            size="lg"
            type="submit"
          >
            Analyze
          </Button>
        </div>
      </form>

      {driftMutation.error ? (
        <Card className="mt-6 border-red-200 bg-red-50/80 shadow-none">
          <p className="font-semibold text-red-900">Drift request failed</p>
          <p className="mt-2 text-sm text-red-800">{driftMutation.error.message}</p>
        </Card>
      ) : null}

      {driftMutation.data ? (
        <Card className="mt-6">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-ocean-600">
            Backward Drift Estimate
          </p>
          <h2 className="mt-2 text-2xl font-semibold text-research-ink">
            {driftMutation.data.status === "experimental" ? "Experimental trace" : "Marine history unavailable"}
          </h2>
          <p className="mt-3 text-sm text-research-muted">{driftMutation.data.message}</p>
          <p className="mt-2 text-sm text-research-muted">
            Traced {driftMutation.data.hours_traced} of {driftMutation.data.hours_requested} requested hours.
          </p>
          {driftMutation.data.anchor_time ? (
            <p className="mt-2 text-sm text-research-muted">
              Latest current reading: {driftMutation.data.anchor_time} (California local time).
              Offset from observation: {driftMutation.data.observation_offset_minutes ?? "unknown"} minutes.
            </p>
          ) : null}
          <p className="mt-2 text-sm text-research-muted">{driftMutation.data.limitations}</p>
          <p className="mt-2 text-sm font-medium text-research-ink">
            Coastline screening: {driftMutation.data.coastline_status === "potential_land_crossing"
              ? "Potential land crossing detected — route not valid as a marine track."
              : driftMutation.data.coastline_status === "clear_on_reference_map"
                ? "No land crossing on the configured reference map (not a navigation guarantee)."
                : "Not checked — coastline dataset is not configured."}
          </p>
          <DriftPathMap path={driftMutation.data.path} coastlineStatus={driftMutation.data.coastline_status} />
          <pre className="mt-4 max-h-[28rem] overflow-auto rounded-2xl bg-research-ink p-5 text-sm leading-6 text-ocean-50">
            {JSON.stringify(driftMutation.data, null, 2)}
          </pre>
        </Card>
      ) : null}

      {mutation.error ? (
        <Card className="mt-6 border-red-200 bg-red-50/80 shadow-none">
          <p className="font-semibold text-red-900">Request failed</p>
          <p className="mt-2 text-sm leading-6 text-red-800">
            {mutation.error.message}
          </p>
        </Card>
      ) : null}

      {mutation.data ? (
        <Card className="mt-6">
          <div className="mb-4">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-ocean-600">
              API Response
            </p>
            <h2 className="mt-2 text-2xl font-semibold text-research-ink">
              Submission Received
            </h2>
          </div>
          <pre className="max-h-[28rem] overflow-auto rounded-2xl bg-research-ink p-5 text-sm leading-6 text-ocean-50">
            {JSON.stringify(mutation.data, null, 2)}
          </pre>
        </Card>
      ) : null}
    </div>
  );
}
