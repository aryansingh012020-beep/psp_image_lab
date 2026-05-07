/* TypeScript interfaces matching all backend Pydantic schemas exactly */

export interface ImageMetadata {
  width: number;
  height: number;
  channels: number;
  format: string;
  file_size_kb: number;
}

export interface UploadResponse {
  session_id: string;
  image_base64: string;
  metadata: ImageMetadata;
}

export interface StepParams {
  gaussian_sigma: number;
  median_kernel_size: number;
  bilateral_d: number;
  bilateral_sigma_color: number;
  bilateral_sigma_space: number;
  mrf_iterations: number;
  mrf_beta: number;
  bayesian_noise_var?: number;
}

export type StepId =
  | 'noise_analysis'
  | 'statistical_analysis'
  | 'gaussian_filter'
  | 'median_filter'
  | 'bilateral_filter'
  | 'histogram_equalization'
  | 'bayesian_map'
  | 'mrf_prior';

export interface ProcessRequest {
  steps: StepId[];
  params: StepParams;
}

export interface StepChartsData {
  histogram_data?: Array<Record<string, any>>;
  snr_data?: Array<Record<string, any>>;
  convergence_data?: Array<Record<string, any>>;
}

export interface StepCharts {
  histogram?: string;
  correlation_map?: string;
  snr_bar?: string;
  convergence_plot?: string;
  wiener_gain_map?: string;
  data?: StepChartsData;
}

export interface StepResult {
  step_id: StepId;
  label: string;
  image_base64: string;
  stats: Record<string, unknown>;
  charts: StepCharts;
  error: string | null;
}

export interface SummaryReport {
  snr_original: number;
  snr_final: number;
  snr_improvement_db: number;
  variance_original: number;
  variance_final: number;
  dominant_noise_type: string;
  processing_time_ms: number;
}

export interface PipelineResult {
  session_id: string;
  steps: StepResult[];
  summary: SummaryReport;
}

export interface ApiError {
  detail: string;
}
