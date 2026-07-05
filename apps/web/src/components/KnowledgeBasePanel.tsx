"use client";

import { ChangeEvent, useEffect, useRef, useState } from "react";
import { Activity, Database, RefreshCw, Search, Trash2, Upload, Wand2 } from "lucide-react";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { SafeDrawer } from "@/components/ui/SafeDrawer";
import {
  deleteKnowledgeDocument,
  diagnoseQAKnowledge,
  getKnowledgeDocument,
  reindexKnowledgeDocument,
  testQAEmbedding,
  testQARetrieval,
  uploadKnowledgeDocument,
  type QADiagnoseResult,
  type QAEmbeddingTestResult,
  type QAModelStatus,
  type QARetrievalTestResult,
  type KnowledgeChunkPreview,
  type KnowledgeDocument,
  type KnowledgeStats
} from "@/lib/api";
import { getStoredUser } from "@/lib/auth";
import { useKnowledgeDocuments, useKnowledgeStats, useQAModelStatus } from "@/hooks/useKnowledgeStats";

type Props = {
  open: boolean;
  onClose: () => void;
  onUploaded?: (message: string) => void;
};

export function KnowledgeBasePanel({ open, onClose, onUploaded }: Props) {
  const readOnly = getStoredUser()?.role === "viewer";
  const inputRef = useRef<HTMLInputElement>(null);
  const [stats, setStats] = useState<KnowledgeStats | null>(null);
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [selected, setSelected] = useState<KnowledgeDocument | null>(null);
  const [chunks, setChunks] = useState<KnowledgeChunkPreview[]>([]);
  const [title, setTitle] = useState("");
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [modelStatus, setModelStatus] = useState<QAModelStatus | null>(null);
  const [embeddingText, setEmbeddingText] = useState("测试中文向量生成");
  const [retrievalQuestion, setRetrievalQuestion] = useState("怎么打爆款？");
  const [diagnosticBusy, setDiagnosticBusy] = useState("");
  const [embeddingResult, setEmbeddingResult] = useState<QAEmbeddingTestResult | null>(null);
  const [retrievalResult, setRetrievalResult] = useState<QARetrievalTestResult | null>(null);
  const [diagnoseResult, setDiagnoseResult] = useState<QADiagnoseResult | null>(null);
  const { data: statsData, error: statsError, mutate: mutateStats } = useKnowledgeStats(open);
  const { data: documentData, error: documentError, mutate: mutateDocuments } = useKnowledgeDocuments(open);
  const { data: modelStatusData, error: modelStatusError, mutate: mutateModelStatus } = useQAModelStatus(open);

  const refresh = async () => {
    setLoading(true);
    setError("");
    try {
      const [nextStats, nextDocs, nextModelStatus] = await Promise.all([mutateStats(), mutateDocuments(), mutateModelStatus()]);
      if (nextStats) setStats(nextStats);
      setDocuments(nextDocs?.documents || []);
      if (nextModelStatus) setModelStatus(nextModelStatus);
    } catch (err) {
      setError(err instanceof Error ? err.message : "知识库加载失败。");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { if (open) void refresh(); }, [open]);
  useEffect(() => { if (statsData) setStats(statsData); }, [statsData]);
  useEffect(() => { setDocuments(Array.isArray(documentData?.documents) ? documentData.documents : []); }, [documentData]);
  useEffect(() => { if (modelStatusData) setModelStatus(modelStatusData); }, [modelStatusData]);
  useEffect(() => {
    const loadError = statsError || documentError || modelStatusError;
    if (loadError) setError(loadError instanceof Error ? loadError.message : "知识库加载失败。");
  }, [statsError, documentError, modelStatusError]);

  const selectDocument = async (docId: string) => {
    setLoading(true);
    setError("");
    try {
      const detail = await getKnowledgeDocument(docId);
      setSelected(detail.document);
      setChunks(detail.chunks_preview || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "文档详情加载失败。");
    } finally {
      setLoading(false);
    }
  };

  const upload = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file || readOnly) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const result = await uploadKnowledgeDocument(file, title);
      setNotice(result.message);
      onUploaded?.("文档已入库，后续问答将优先检索该知识库。");
      setTitle("");
      await refresh();
      await selectDocument(result.doc_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "文档入库失败。");
    } finally {
      setBusy(false);
    }
  };

  const remove = async (docId: string) => {
    if (readOnly || !window.confirm("确认删除这个知识库文档吗？对应 chunks 会同步删除。")) return;
    setBusy(true);
    setError("");
    try {
      await deleteKnowledgeDocument(docId);
      setSelected(null);
      setChunks([]);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "文档删除失败。");
    } finally {
      setBusy(false);
    }
  };

  const reindex = async (docId: string) => {
    if (readOnly || !window.confirm("确认重新索引这个文档吗？旧 chunks 会被重建。")) return;
    setBusy(true);
    setError("");
    try {
      const result = await reindexKnowledgeDocument(docId);
      setNotice(result.message);
      await refresh();
      await selectDocument(docId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "重新索引失败。");
    } finally {
      setBusy(false);
    }
  };

  const runEmbeddingTest = async () => {
    if (readOnly) return;
    setDiagnosticBusy("embedding");
    setError("");
    try {
      setEmbeddingResult(await testQAEmbedding({ text: embeddingText.trim() || "测试中文向量生成" }));
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Embedding 测试失败。");
    } finally {
      setDiagnosticBusy("");
    }
  };

  const runRetrievalTest = async () => {
    if (readOnly) return;
    setDiagnosticBusy("retrieval");
    setError("");
    try {
      setRetrievalResult(await testQARetrieval({ question: retrievalQuestion.trim() || "怎么打爆款？", top_k: 5 }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "检索测试失败。");
    } finally {
      setDiagnosticBusy("");
    }
  };

  const runDiagnose = async () => {
    if (readOnly) return;
    setDiagnosticBusy("diagnose");
    setError("");
    try {
      setDiagnoseResult(await diagnoseQAKnowledge({ question: retrievalQuestion.trim() || "怎么打爆款？" }));
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "知识库诊断失败。");
    } finally {
      setDiagnosticBusy("");
    }
  };

  const badge = (ok: boolean, warning = false) => <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${ok ? "bg-emerald-50 text-emerald-700" : warning ? "bg-amber-50 text-amber-700" : "bg-rose-50 text-rose-700"}`}>{ok ? "正常" : warning ? "提醒" : "不可用"}</span>;

  const sidebar = <><div className="shrink-0 p-4"><p className="text-xs font-semibold text-violet-700">meizhaiseek v1.7.2</p><h3 className="mt-1 font-bold">知识库</h3></div><div className="min-h-0 flex-1 overflow-y-auto px-3 pb-4">{documents.map((item) => <button className={`mb-2 w-full rounded-xl p-3 text-left ${selected?.doc_id === item.doc_id ? "bg-violet-100 text-violet-800" : "bg-white text-slate-700"}`} key={item.doc_id} onClick={() => void selectDocument(item.doc_id)} type="button"><span className="block truncate text-sm font-semibold">{item.title}</span><span className="mt-1 block text-xs">{item.status} · {item.chunk_count} chunks</span></button>)}{!documents.length && !loading ? <p className="px-2 text-xs text-slate-400">暂无知识库文档</p> : null}</div></>;

  return <SafeDrawer open={open} title={selected?.title || "AI 对话知识库"} eyebrow="meizhaiseek v1.7.2" onClose={onClose} sidebar={sidebar} maxWidth="max-w-6xl">
    {error ? <div className="mb-4"><ErrorState message={error} onRetry={() => void refresh()} /></div> : null}
    {notice ? <p className="mb-4 rounded-xl bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-700">{notice}</p> : null}
    {modelStatus ? <section className="mb-6 grid gap-3 lg:grid-cols-3">
      <div className="rounded-2xl border border-slate-100 bg-white p-4"><div className="mb-3 flex items-center justify-between"><h3 className="font-bold text-slate-900">bge-small-zh</h3>{badge(modelStatus.embedding_model.exists && !modelStatus.embedding_model.error)}</div><p className="break-all text-xs text-slate-500">{modelStatus.embedding_model.configured_path}</p><p className="mt-2 text-sm text-slate-600">存在：{modelStatus.embedding_model.exists ? "是" : "否"} · 已加载：{modelStatus.embedding_model.loaded ? "是" : "否"}</p>{modelStatus.embedding_model.dimension ? <p className="mt-1 text-sm text-slate-600">维度：{modelStatus.embedding_model.dimension}</p> : null}{modelStatus.embedding_model.error ? <p className="mt-2 text-sm text-rose-600">{modelStatus.embedding_model.error}</p> : null}{!modelStatus.embedding_model.exists ? <p className="mt-2 text-sm text-amber-700">bge-small-zh 模型未安装<br />{modelStatus.embedding_model.setup_hint}</p> : null}</div>
      <div className="rounded-2xl border border-slate-100 bg-white p-4"><div className="mb-3 flex items-center justify-between"><h3 className="font-bold text-slate-900">SQLite RAG</h3>{badge(modelStatus.rag.sqlite_exists, !modelStatus.rag.current_user_chunk_count)}</div><p className="break-all text-xs text-slate-500">{modelStatus.rag.sqlite_path}</p><p className="mt-2 text-sm text-slate-600">文档 {modelStatus.rag.current_user_document_count} · chunk {modelStatus.rag.current_user_chunk_count}</p><p className="mt-1 text-sm text-slate-600">ready {modelStatus.rag.ready_document_count} · failed {modelStatus.rag.failed_document_count}</p></div>
      <div className="rounded-2xl border border-slate-100 bg-white p-4"><div className="mb-3 flex items-center justify-between"><h3 className="font-bold text-slate-900">DeepSeek</h3>{badge(modelStatus.deepseek.configured)}</div><p className="text-sm text-slate-600">模型：{modelStatus.deepseek.model}</p><p className="mt-1 text-sm text-slate-600">Base URL：{modelStatus.deepseek.base_url_configured ? "已配置" : "未配置"}</p>{modelStatus.deepseek.error ? <p className="mt-2 text-sm text-rose-600">{modelStatus.deepseek.error}</p> : null}</div>
    </section> : null}
    <section className="mb-6 rounded-2xl border border-slate-100 bg-slate-50 p-4">
      <div className="mb-3 flex items-center gap-2 font-bold text-slate-900"><Activity className="h-4 w-4 text-violet-600" />RAG 可用性诊断</div>
      {readOnly ? <p className="mb-3 rounded-xl bg-sky-50 px-3 py-2 text-sm text-sky-700">当前账号为只读权限，无法执行诊断测试。</p> : null}
      <div className="grid gap-3 lg:grid-cols-2"><input className="rounded-xl border border-slate-200 px-3 py-2 text-sm" disabled={readOnly || Boolean(diagnosticBusy)} onChange={(event) => setEmbeddingText(event.target.value)} value={embeddingText} /><input className="rounded-xl border border-slate-200 px-3 py-2 text-sm" disabled={readOnly || Boolean(diagnosticBusy)} onChange={(event) => setRetrievalQuestion(event.target.value)} value={retrievalQuestion} /></div>
      <div className="mt-3 flex flex-wrap gap-2"><button className="inline-flex items-center gap-2 rounded-xl bg-violet-600 px-3 py-2 text-sm font-semibold text-white disabled:opacity-50" disabled={readOnly || Boolean(diagnosticBusy)} onClick={() => void runEmbeddingTest()} type="button"><Wand2 className="h-4 w-4" />{diagnosticBusy === "embedding" ? "测试中..." : "测试 Embedding"}</button><button className="inline-flex items-center gap-2 rounded-xl bg-sky-600 px-3 py-2 text-sm font-semibold text-white disabled:opacity-50" disabled={readOnly || Boolean(diagnosticBusy)} onClick={() => void runRetrievalTest()} type="button"><Search className="h-4 w-4" />{diagnosticBusy === "retrieval" ? "测试中..." : "测试检索"}</button><button className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-3 py-2 text-sm font-semibold text-white disabled:opacity-50" disabled={readOnly || Boolean(diagnosticBusy)} onClick={() => void runDiagnose()} type="button"><Activity className="h-4 w-4" />{diagnosticBusy === "diagnose" ? "诊断中..." : "知识库诊断"}</button></div>
      {(embeddingResult || retrievalResult || diagnoseResult) ? <div className="mt-4 max-h-80 space-y-3 overflow-y-auto rounded-xl bg-white p-3 text-sm">
        {embeddingResult ? <div><p className="font-semibold text-slate-900">Embedding：{embeddingResult.status}</p>{embeddingResult.status === "success" ? <p className="mt-1 text-slate-600">dimension {embeddingResult.dimension} · preview [{embeddingResult.preview?.join(", ")}]</p> : <p className="mt-1 text-rose-600">{embeddingResult.error} {embeddingResult.setup_hint}</p>}</div> : null}
        {retrievalResult ? <div><p className="font-semibold text-slate-900">检索：{retrievalResult.status} · sources {retrievalResult.source_count}</p>{retrievalResult.warnings?.length ? <p className="mt-1 text-amber-700">{retrievalResult.warnings.join("；")}</p> : null}{retrievalResult.error ? <p className="mt-1 text-rose-600">{retrievalResult.error}</p> : null}{retrievalResult.sources?.map((source) => <div className="mt-2 rounded-xl bg-slate-50 p-3" key={source.chunk_id}><p className="font-semibold">{source.title} · score {Number(source.score || 0).toFixed(2)}</p><p className="mt-1 text-slate-600">{source.content_preview}</p></div>)}</div> : null}
        {diagnoseResult ? <div><p className="font-semibold text-slate-900">诊断：{diagnoseResult.status}</p><p className="mt-1 text-slate-600">{diagnoseResult.summary}</p>{diagnoseResult.checks.map((check) => <div className="mt-2 rounded-xl bg-slate-50 p-3" key={check.key}><p className="font-semibold">{check.label} · {check.status}</p><p className="mt-1 text-slate-600">{check.message}</p>{check.suggestion ? <p className="mt-1 text-amber-700">{check.suggestion}</p> : null}</div>)}</div> : null}
      </div> : null}
    </section>
    {readOnly ? <p className="mb-4 rounded-xl bg-sky-50 px-4 py-3 text-sm text-sky-700">当前账号为只读权限，无法管理知识库。</p> : <section className="mb-6 rounded-2xl border border-violet-100 bg-violet-50/50 p-4"><h3 className="font-bold text-slate-900">上传文档入库</h3><p className="mt-1 text-xs text-slate-500">支持 txt、md、docx，单文件最大 20MB。</p><div className="mt-3 flex flex-wrap items-end gap-3"><input accept=".txt,.md,.docx" className="hidden" onChange={upload} ref={inputRef} type="file" /><label className="min-w-56 flex-1 text-xs font-semibold text-slate-600">文档标题（可选）<input className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm font-normal" onChange={(event) => setTitle(event.target.value)} value={title} /></label><button className="inline-flex items-center gap-2 rounded-xl bg-violet-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50" disabled={busy} onClick={() => inputRef.current?.click()} type="button"><Upload className="h-4 w-4" />{busy ? "处理中..." : "上传并入库"}</button></div></section>}
    {stats ? <section className="mb-6 grid gap-3 sm:grid-cols-4"><div className="rounded-2xl bg-slate-50 p-4"><p className="text-xs text-slate-500">文档数</p><p className="mt-1 text-2xl font-bold">{stats.document_count}</p></div><div className="rounded-2xl bg-slate-50 p-4"><p className="text-xs text-slate-500">chunk 数</p><p className="mt-1 text-2xl font-bold">{stats.chunk_count}</p></div><div className="rounded-2xl bg-emerald-50 p-4"><p className="text-xs text-emerald-600">ready</p><p className="mt-1 text-2xl font-bold text-emerald-700">{stats.ready_count}</p></div><div className="rounded-2xl bg-rose-50 p-4"><p className="text-xs text-rose-600">failed</p><p className="mt-1 text-2xl font-bold text-rose-700">{stats.failed_count}</p></div></section> : null}
    {loading ? <LoadingState label="正在读取知识库..." /> : selected ? <section className="space-y-5"><div className="rounded-2xl border border-slate-100 bg-white p-4"><div className="flex flex-wrap items-start justify-between gap-3"><div><h3 className="text-lg font-bold text-slate-900">{selected.title}</h3><p className="mt-1 text-sm text-slate-500">{selected.source_type} · {selected.status} · {selected.chunk_count} chunks</p><p className="mt-1 text-xs text-slate-400">{selected.updated_at ? new Date(selected.updated_at).toLocaleString("zh-CN") : ""}</p></div>{!readOnly ? <div className="flex flex-wrap gap-2"><button className="inline-flex items-center gap-2 rounded-xl border border-violet-200 px-3 py-2 text-sm font-semibold text-violet-700 disabled:opacity-50" disabled={busy} onClick={() => void reindex(selected.doc_id)} type="button"><RefreshCw className="h-4 w-4" />重新索引</button><button className="inline-flex items-center gap-2 rounded-xl border border-rose-200 px-3 py-2 text-sm font-semibold text-rose-600 disabled:opacity-50" disabled={busy} onClick={() => void remove(selected.doc_id)} type="button"><Trash2 className="h-4 w-4" />删除</button></div> : null}</div></div><div><h3 className="mb-3 flex items-center gap-2 font-bold text-slate-900"><Database className="h-4 w-4 text-violet-600" />Chunk Preview</h3><div className="max-h-96 space-y-3 overflow-y-auto rounded-2xl border border-slate-100 bg-slate-50 p-3">{chunks.length ? chunks.map((chunk) => <div className="rounded-xl bg-white p-3 text-sm text-slate-700" key={chunk.chunk_id}><p className="mb-2 text-xs font-semibold text-violet-700">#{chunk.chunk_index}</p><p className="whitespace-pre-wrap break-words leading-6">{chunk.content_preview}</p></div>) : <p className="p-3 text-sm text-slate-400">暂无 chunk preview</p>}</div></div></section> : <p className="rounded-2xl bg-slate-50 px-4 py-8 text-center text-sm text-slate-500">从左侧选择文档查看详情。</p>}
  </SafeDrawer>;
}


