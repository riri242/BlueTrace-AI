import { useId, useRef, useState } from "react";

import { Button } from "@/components/ui/Button";

interface FileUploadProps {
  error?: string;
  file: File | null;
  onFileSelect: (file: File) => void;
  previewUrl: string | null;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024 * 1024) {
    return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function FileUpload({
  error,
  file,
  onFileSelect,
  previewUrl
}: FileUploadProps) {
  const inputId = useId();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const selectFirstImage = (files: FileList | null) => {
    const selectedFile = files?.item(0);

    if (selectedFile && selectedFile.type.startsWith("image/")) {
      onFileSelect(selectedFile);
    }
  };

  return (
    <div className="space-y-4">
      <div
        aria-describedby={error ? `${inputId}-error` : undefined}
        className={[
          "flex min-h-64 flex-col items-center justify-center rounded-2xl border border-dashed p-6 text-center transition",
          isDragging
            ? "border-ocean-500 bg-ocean-50"
            : "border-research-line bg-white"
        ].join(" ")}
        onDragEnter={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={(event) => {
          event.preventDefault();
          setIsDragging(false);
        }}
        onDragOver={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDrop={(event) => {
          event.preventDefault();
          setIsDragging(false);
          selectFirstImage(event.dataTransfer.files);
        }}
      >
        {previewUrl ? (
          <img
            alt="Uploaded marine debris preview"
            className="h-56 w-full rounded-xl object-cover"
            src={previewUrl}
          />
        ) : (
          <div className="max-w-sm space-y-3">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-ocean-600">
              Image Upload
            </p>
            <h2 className="text-2xl font-semibold text-research-ink">
              Drag and Drop
            </h2>
            <p className="text-sm leading-6 text-research-muted">
              or choose a clear beach observation image for this Milestone 1
              submission.
            </p>
          </div>
        )}
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <input
          accept="image/jpeg,image/png,image/webp"
          className="sr-only"
          id={inputId}
          onChange={(event) => selectFirstImage(event.target.files)}
          ref={inputRef}
          type="file"
        />
        <Button
          onClick={() => inputRef.current?.click()}
          type="button"
          variant="secondary"
        >
          Choose File
        </Button>
        {file ? (
          <p className="text-sm text-research-muted">
            {file.name} · {formatFileSize(file.size)}
          </p>
        ) : null}
      </div>

      {error ? (
        <p className="text-sm font-medium text-red-700" id={`${inputId}-error`}>
          {error}
        </p>
      ) : null}
    </div>
  );
}

