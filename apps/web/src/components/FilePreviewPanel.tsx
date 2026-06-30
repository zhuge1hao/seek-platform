"use client";

import { useEffect, useState } from "react";
import { ChevronDown, Download, Trash2 } from "lucide-react";
import { downloadArtifact, getArtifactBlobUrl, getFilePreview, type FilePreviewResponse, type GenericUploadResponse } from "@/lib/api";

type FilePreviewPanelProps = {
  file: GenericUploadResponse;
  onRemove: (fileId: string) => void;
};

export function FilePreviewPanel({ file, onRemove }: FilePreviewPanelProps) {
  const [preview, setPreview] = useState<FilePreviewResponse | null>(null);
  const [isOpen, setIsOpen] = useState(true);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError("");
    getFilePreview(file.file_id)
      .then((data) => {
        if (!cancelled) setPreview(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "文件预览失败。");
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [file.file_id]);

  const downloadUrl = preview?.download_url;
  const previewData = preview?.preview || {};

  return (
    <div className="rounded-2xl border border-violet-100 bg-violet-50/50 p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <button className="flex min-w-0 items-center gap-2 text-left" onClick={() => setIsOpen((value) => !value)} type="button">
          <ChevronDown className={["h-4 w-4 text-violet-600 transition", isOpen ? "rotate-180" : ""].join(" ")} />
          <span className="truncate text-sm font-semibold text-slate-900">{file.filename}</span>
          <span className="rounded-full bg-white px-2 py-0.5 text-xs text-slate-500">{file.file_type}</span>
        </button>
        <div className="flex shrink-0 gap-2">
          {downloadUrl ? (
            <button className="rounded-full bg-white p-2 text-violet-700 transition hover:bg-violet-100" onClick={() => downloadArtifact(downloadUrl, file.filename)} type="button">
              <Download className="h-4 w-4" />
            </button>
          ) : null}
          <button className="rounded-full bg-white p-2 text-rose-600 transition hover:bg-rose-50" onClick={() => onRemove(file.file_id)} type="button">
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      {isOpen ? (
        <div className="mt-3">
          {isLoading ? <p className="text-sm text-slate-500">正在解析文件预览...</p> : null}
          {error ? <p className="rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-600">{error}</p> : null}
          {!isLoading && !error && preview ? <PreviewContent preview={preview} /> : null}
        </div>
      ) : null}
    </div>
  );
}

function PreviewContent({ preview }: { preview: FilePreviewResponse }) {
  const data = preview.preview as Record<string, any>;
  if (preview.file_type === "excel") {
    const columns = (data.columns || []) as string[];
    const rows = (data.rows || []) as Record<string, string>[];
    return (
      <div className="overflow-x-auto rounded-xl bg-white">
        <table className="min-w-full text-xs">
          <thead>
            <tr className="border-b border-slate-100">
              {columns.map((column) => (
                <th key={column} className="px-3 py-2 text-left font-semibold text-slate-600">{column}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, rowIndex) => (
              <tr key={rowIndex} className="border-b border-slate-50">
                {columns.map((column) => (
                  <td key={column} className="max-w-[220px] truncate px-3 py-2 text-slate-600">{row[column]}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        <p className="px-3 py-2 text-xs text-slate-400">共 {String(data.row_count || 0)} 行，预览 {String(data.preview_count || rows.length)} 行</p>
      </div>
    );
  }
  if (preview.file_type === "text" || preview.file_type === "json") {
    return <pre className="max-h-64 overflow-auto rounded-xl bg-white p-3 text-xs leading-5 text-slate-700">{String(data.text || "")}</pre>;
  }
  if (preview.file_type === "image" && preview.download_url) {
    return <AuthenticatedImage alt={preview.filename} downloadUrl={preview.download_url} />;
  }
  return <p className="break-all rounded-xl bg-white p-3 text-xs text-slate-600">{preview.saved_path}</p>;
}

function AuthenticatedImage({ alt, downloadUrl }: { alt: string; downloadUrl: string }) {
  const [source, setSource] = useState("");
  useEffect(() => {
    let active = true;
    let objectUrl = "";
    getArtifactBlobUrl(downloadUrl)
      .then((url) => {
        objectUrl = url;
        if (active) setSource(url);
      })
      .catch(() => undefined);
    return () => {
      active = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [downloadUrl]);
  return source ? <img alt={alt} className="max-h-56 rounded-xl object-contain" src={source} /> : <p className="text-sm text-slate-500">正在加载图片...</p>;
}
