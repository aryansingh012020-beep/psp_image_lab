import type { UploadResponse, ProcessRequest, PipelineResult, ApiError } from '../types/api';

const BASE = '/api';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try {
      const err: ApiError = await res.json();
      msg = err.detail ?? msg;
    } catch {
      // ignore parse errors
    }
    throw new Error(msg);
  }
  return res.json() as Promise<T>;
}

export async function uploadImage(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append('image', file);
  const res = await fetch(`${BASE}/upload`, { method: 'POST', body: form });
  return handleResponse<UploadResponse>(res);
}

export async function processImage(
  sessionId: string,
  req: ProcessRequest,
): Promise<PipelineResult> {
  const res = await fetch(`${BASE}/process/${sessionId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  return handleResponse<PipelineResult>(res);
}

export interface NoiseResponse {
  image_base64: string;
  sigma_used: number;
  noise_type: string;
}

export async function addNoise(
  sessionId: string,
  sigma: number,
  noiseType: 'gaussian' | 'salt_pepper' | 'both',
  spDensity: number,
): Promise<NoiseResponse> {
  const res = await fetch(`${BASE}/noise/${sessionId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sigma, noise_type: noiseType, sp_density: spDensity }),
  });
  return handleResponse<NoiseResponse>(res);
}

