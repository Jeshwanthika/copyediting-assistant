"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import {
  deleteDocument,
  getDocumentFile,
  getDocuments,
  replaceDocumentFile,
  updateDocument,
  uploadDocument,
} from "@/lib/api";
import type { DocumentItem } from "@/types";

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(iso: string): string {
  const date = new Date(iso);
  return Number.isNaN(date.getTime())
    ? iso
    : date.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
}

const message = (err: unknown) => (err instanceof Error ? err.message : "Something went wrong.");

export default function ErrorsSolutions() {
  const { isLead } = useAuth();
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [openId, setOpenId] = useState<number | null>(null);
  const [editing, setEditing] = useState<DocumentItem | "new" | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setDocs(await getDocuments());
      setError(null);
    } catch (err) {
      setError(message(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    // Open a document straight away when linked as /errors-solutions?doc=3
    const doc = Number(new URLSearchParams(window.location.search).get("doc"));
    if (doc) setOpenId(doc);
  }, [load]);

  function open(id: number | null) {
    setOpenId(id);
    const url = id ? `/errors-solutions?doc=${id}` : "/errors-solutions";
    window.history.replaceState(null, "", url);
  }

  const openDoc = docs.find((d) => d.id === openId) ?? null;

  if (openId !== null && (openDoc || loading)) {
    return openDoc ? (
      <PdfViewer doc={openDoc} onClose={() => open(null)} />
    ) : (
      <div className="page-wrap"><p className="muted">Loading document…</p></div>
    );
  }

  return (
    <div className="page-wrap">
      <div className="page-header-row">
        <div>
          <div className="page-kicker">Reference library</div>
          <h1 className="page-title">
            Errors <span className="accent-italic">&amp;</span> solutions
          </h1>
          <p className="page-subtitle">
            Common copy-editing errors and how to fix them. Select a guide to read it here.
          </p>
        </div>
        {isLead && (
          <button className="btn-filled" type="button" onClick={() => setEditing("new")}>
            <span className="material-symbols-outlined">upload_file</span>
            Upload PDF
          </button>
        )}
      </div>

      {isLead ? (
        <p className="role-note">
          <span className="material-symbols-outlined">admin_panel_settings</span>
          You can upload, rename, replace and delete guides. Trainees can only read them.
        </p>
      ) : (
        <p className="role-note">
          <span className="material-symbols-outlined">visibility</span>
          Read-only. Ask a lead if a guide is missing or out of date.
        </p>
      )}

      {notice && <p className="success">{notice}</p>}
      {error && <p className="error">{error}</p>}

      {loading ? (
        <div className="doc-grid">
          {[0, 1, 2].map((i) => (
            <div className="doc-card skeleton" key={i} />
          ))}
        </div>
      ) : docs.length === 0 && !error ? (
        <div className="empty-panel">
          <span className="material-symbols-outlined">picture_as_pdf</span>
          <h2>No guides yet</h2>
          <p>
            {isLead
              ? "Upload the errors & solutions PDFs with the button above."
              : "Your lead has not added any errors & solutions guides yet."}
          </p>
        </div>
      ) : (
        <div className="doc-grid">
          {docs.map((doc, index) => (
            <article className="doc-card" key={doc.id}>
              <button className="doc-open" type="button" onClick={() => open(doc.id)}>
                <div className="doc-icon">
                  <span className="material-symbols-outlined">picture_as_pdf</span>
                </div>
                <div className="doc-number">{String(index + 1).padStart(2, "0")}</div>
                <h2 className="doc-title">{doc.title}</h2>
                {doc.description && <p className="doc-description">{doc.description}</p>}
                <div className="doc-meta">
                  {formatSize(doc.size_bytes)} · Updated {formatDate(doc.updated_at)}
                </div>
                <span className="doc-read">
                  Read guide <span className="material-symbols-outlined">arrow_forward</span>
                </span>
              </button>
              {isLead && (
                <div className="doc-admin">
                  <button className="btn-outline" type="button" onClick={() => setEditing(doc)}>
                    <span className="material-symbols-outlined">edit</span>Edit
                  </button>
                </div>
              )}
            </article>
          ))}
        </div>
      )}

      {isLead && editing && (
        <DocumentDialog
          doc={editing === "new" ? null : editing}
          onClose={() => setEditing(null)}
          onDone={async (text) => {
            setEditing(null);
            setNotice(text);
            await load();
          }}
        />
      )}
    </div>
  );
}

/** Shows the PDF in the browser's own viewer (zoom, search, print all work). */
function PdfViewer({ doc, onClose }: { doc: DocumentItem; onClose: () => void }) {
  const [url, setUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let objectUrl: string | null = null;
    let cancelled = false;
    getDocumentFile(doc.id)
      .then((blob) => {
        if (cancelled) return;
        objectUrl = URL.createObjectURL(blob);
        setUrl(objectUrl);
      })
      .catch((err) => !cancelled && setError(message(err)));
    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [doc.id, doc.updated_at]);

  return (
    <div className="viewer-page">
      <div className="viewer-bar">
        <button className="btn-outline" type="button" onClick={onClose}>
          <span className="material-symbols-outlined">arrow_back</span>All guides
        </button>
        <div className="viewer-title">
          <span className="material-symbols-outlined">picture_as_pdf</span>
          <div>
            <strong>{doc.title}</strong>
            <span>{doc.original_filename}</span>
          </div>
        </div>
        <div className="viewer-actions">
          <a
            className={`btn-outline ${url ? "" : "is-disabled"}`}
            href={url ?? undefined}
            target="_blank"
            rel="noopener"
            aria-disabled={!url}
          >
            <span className="material-symbols-outlined">open_in_new</span>New tab
          </a>
          <a
            className={`btn-filled ${url ? "" : "is-disabled"}`}
            href={url ?? undefined}
            download={doc.original_filename}
            aria-disabled={!url}
          >
            <span className="material-symbols-outlined">download</span>Download
          </a>
        </div>
      </div>
      <div className="viewer-frame">
        {error ? (
          <p className="error">{error}</p>
        ) : url ? (
          <iframe src={url} title={doc.title} />
        ) : (
          <p className="muted">Opening {doc.title}…</p>
        )}
      </div>
    </div>
  );
}

/** Upload a new PDF, or (for an existing one) edit details, replace the file or delete it. */
function DocumentDialog({
  doc,
  onClose,
  onDone,
}: {
  doc: DocumentItem | null;
  onClose: () => void;
  onDone: (notice: string) => Promise<void>;
}) {
  const [title, setTitle] = useState(doc?.title ?? "");
  const [description, setDescription] = useState(doc?.description ?? "");
  const [file, setFile] = useState<File | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && !busy && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [busy, onClose]);

  function pickFile(picked: File | null) {
    setError(null);
    if (picked && picked.type && picked.type !== "application/pdf") {
      setError("Please choose a PDF file.");
      return;
    }
    setFile(picked);
    if (picked && !doc && !title.trim()) {
      setTitle(picked.name.replace(/\.pdf$/i, "").replace(/[_-]+/g, " "));
    }
  }

  async function run(action: () => Promise<string>) {
    setBusy(true);
    setError(null);
    try {
      await onDone(await action());
    } catch (err) {
      setError(message(err));
      setBusy(false);
    }
  }

  function save() {
    if (!doc) {
      if (!file) return setError("Choose a PDF to upload.");
      return run(async () => {
        await uploadDocument(file, title.trim(), description.trim());
        return `Uploaded “${title.trim() || file.name}”.`;
      });
    }
    if (!title.trim()) return setError("The title cannot be blank.");
    return run(async () => {
      await updateDocument(doc.id, { title: title.trim(), description: description.trim() });
      if (file) await replaceDocumentFile(doc.id, file);
      return file ? `Saved “${title.trim()}” with the new PDF.` : `Saved “${title.trim()}”.`;
    });
  }

  return (
    <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && !busy && onClose()}>
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby="doc-dialog-title">
        <div className="modal-head">
          <h2 id="doc-dialog-title">{doc ? "Edit guide" : "Upload a guide"}</h2>
          <button className="icon-btn" type="button" onClick={onClose} disabled={busy} aria-label="Close">
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>

        <div className="modal-body">
          <div
            className={`dropzone ${file ? "has-file" : ""}`}
            onClick={() => fileInput.current?.click()}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              pickFile(e.dataTransfer.files?.[0] ?? null);
            }}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && fileInput.current?.click()}
          >
            <span className="material-symbols-outlined">{file ? "task" : "upload_file"}</span>
            {file ? (
              <span>
                <strong>{file.name}</strong> · {formatSize(file.size)}
              </span>
            ) : doc ? (
              <span>
                Current file: <strong>{doc.original_filename}</strong>. Drop a PDF here or click to replace it
                (optional).
              </span>
            ) : (
              <span>Drop a PDF here or click to choose one</span>
            )}
            <input
              ref={fileInput}
              type="file"
              accept="application/pdf,.pdf"
              hidden
              onChange={(e) => pickFile(e.target.files?.[0] ?? null)}
            />
          </div>

          <label className="field">
            <span>Title</span>
            <input type="text" value={title} maxLength={200} onChange={(e) => setTitle(e.target.value)} />
          </label>
          <label className="field">
            <span>Short description (optional)</span>
            <textarea
              rows={3}
              value={description}
              maxLength={2000}
              onChange={(e) => setDescription(e.target.value)}
            />
          </label>

          {error && <p className="error">{error}</p>}
        </div>

        <div className="modal-foot">
          {doc &&
            (confirmDelete ? (
              <div className="confirm-delete">
                <span>Delete this guide for everyone?</span>
                <button
                  className="btn-danger"
                  type="button"
                  disabled={busy}
                  onClick={() =>
                    run(async () => {
                      await deleteDocument(doc.id);
                      return `Deleted “${doc.title}”.`;
                    })
                  }
                >
                  Yes, delete
                </button>
                <button className="btn-outline" type="button" onClick={() => setConfirmDelete(false)}>
                  Keep
                </button>
              </div>
            ) : (
              <button className="btn-text-danger" type="button" onClick={() => setConfirmDelete(true)}>
                <span className="material-symbols-outlined">delete</span>Delete
              </button>
            ))}
          <div className="modal-foot-right">
            <button className="btn-outline" type="button" onClick={onClose} disabled={busy}>
              Cancel
            </button>
            <button className="btn-filled" type="button" onClick={save} disabled={busy}>
              {busy ? "Saving…" : doc ? "Save" : "Upload"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
