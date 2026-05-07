import { create } from 'zustand';
import type { UploadResponse, PipelineResult, ImageMetadata } from '../types/api';

interface SessionState {
  sessionId: string | null;
  originalImage: string | null;
  metadata: ImageMetadata | null;
  pipelineResult: PipelineResult | null;
  isUploading: boolean;
  isProcessing: boolean;
  error: string | null;
  phase: 'upload' | 'configure' | 'results';
}

interface SessionActions {
  setSession: (resp: UploadResponse) => void;
  setResult: (result: PipelineResult) => void;
  setUploading: (v: boolean) => void;
  setProcessing: (v: boolean) => void;
  setError: (msg: string | null) => void;
  setPhase: (phase: SessionState['phase']) => void;
  reset: () => void;
}

const initialState: SessionState = {
  sessionId: null,
  originalImage: null,
  metadata: null,
  pipelineResult: null,
  isUploading: false,
  isProcessing: false,
  error: null,
  phase: 'upload',
};

export const useSessionStore = create<SessionState & SessionActions>((set) => ({
  ...initialState,

  setSession: (resp) =>
    set({
      sessionId: resp.session_id,
      originalImage: resp.image_base64,
      metadata: resp.metadata,
      pipelineResult: null,
      error: null,
      phase: 'configure',
    }),

  setResult: (result) =>
    set({ pipelineResult: result, isProcessing: false, phase: 'results' }),

  setUploading: (v) => set({ isUploading: v }),
  setProcessing: (v) => set({ isProcessing: v }),
  setError: (msg) => set({ error: msg, isUploading: false, isProcessing: false }),
  setPhase: (phase) => set({ phase }),
  reset: () => set(initialState),
}));
