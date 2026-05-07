import React, { useCallback, useState, useRef } from 'react';
import { uploadImage } from '../api/client';
import { useSessionStore } from '../store/sessionStore';

const ACCEPTED = ['image/jpeg', 'image/png', 'image/tiff', 'image/bmp', 'image/webp'];
const MAX_MB = 10;

export const UploadZone: React.FC = () => {
  const [dragging, setDragging] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string>('');
  const inputRef = useRef<HTMLInputElement>(null);

  const { isUploading, error, setSession, setUploading, setError } = useSessionStore();

  const handleFile = useCallback(async (file: File) => {
    if (!ACCEPTED.includes(file.type)) {
      setError(`Unsupported format: ${file.type}. Accepted: JPEG, PNG, TIFF, BMP, WEBP`);
      return;
    }
    if (file.size > MAX_MB * 1024 * 1024) {
      setError(`File too large (${(file.size / 1048576).toFixed(1)} MB). Max 10 MB.`);
      return;
    }
    setError(null);
    setFileName(file.name);
    // Local preview
    const url = URL.createObjectURL(file);
    setPreview(url);
    setUploading(true);
    try {
      const resp = await uploadImage(file);
      setSession(resp);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Upload failed');
      setPreview(null);
    } finally {
      setUploading(false);
    }
  }, [setError, setSession, setUploading]);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, [handleFile]);

  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  return (
    <div style={{ width: '100%', maxWidth: 680, margin: '0 auto' }}>
      {/* Zone */}
      <div
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
        onDragEnter={(e) => { e.preventDefault(); setDragging(true); }}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        style={{
          border: `2px dashed ${dragging ? 'var(--color-accent)' : 'var(--color-border)'}`,
          borderRadius: 'var(--radius-lg)',
          padding: '56px 40px',
          textAlign: 'center',
          cursor: 'pointer',
          background: dragging ? 'var(--color-accent-dim)' : 'var(--color-surface)',
          transition: 'border-color var(--transition-med), background var(--transition-med)',
          outline: 'none',
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED.join(',')}
          style={{ display: 'none' }}
          onChange={onInputChange}
        />

        {preview ? (
          <div className="fade-up">
            <img
              src={preview}
              alt="Preview"
              style={{ maxHeight: 240, maxWidth: '100%', margin: '0 auto 16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}
            />
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--color-text-muted)' }}>
              {fileName}
            </p>
          </div>
        ) : (
          <>
            {/* Upload Icon */}
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent)" strokeWidth="1.5" style={{ margin: '0 auto 20px', opacity: dragging ? 1 : 0.6 }}>
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            <p style={{ fontSize: 16, fontWeight: 600, color: 'var(--color-text)', marginBottom: 8 }}>
              Drop image here or <span style={{ color: 'var(--color-accent)' }}>click to browse</span>
            </p>
            <p style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 20 }}>
              Maximum file size: 10 MB
            </p>
            <div style={{ display: 'flex', gap: 6, justifyContent: 'center', flexWrap: 'wrap' }}>
              {['JPEG', 'PNG', 'TIFF', 'BMP', 'WEBP'].map(f => (
                <span key={f} className="badge badge-muted">{f}</span>
              ))}
            </div>
          </>
        )}
      </div>

      {/* Uploading indicator */}
      {isUploading && (
        <div style={{ marginTop: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
            <div className="spinner" />
            <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>Uploading and processing image…</span>
          </div>
          <div className="progress-bar-track progress-bar-indeterminate">
            <div className="progress-bar-fill" />
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="error-box fade-up" style={{ marginTop: 14 }}>
          ⚠ {error}
        </div>
      )}
    </div>
  );
};
