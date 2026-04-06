export interface VideoUploadResponse {
  session_id: string;
  filename: string;
  size: number;
  duration: number;
  status: string;
}

export interface SessionStatus {
  session_id: string;
  status: "uploaded" | "processing" | "completed" | "failed";
  created_at: string;
  start_time?: string;
  end_time?: string;
  error?: string;
}

export interface PredictionResult {
  session_id: string;
  timestamp: string;
  video_filename: string;
  emotion_class: string;
  confidence_scores: { [key: string]: number };
  processing_metadata: any;
}
