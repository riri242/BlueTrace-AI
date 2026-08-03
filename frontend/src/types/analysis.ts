export interface Coordinates {
  latitude: number;
  longitude: number;
}

export interface AnalysisRequest {
  image: File;
  date: string;
  time: string;
  latitude: number;
  longitude: number;
}

export interface ImageMetadata {
  filename: string;
  content_type: string;
  size_bytes: number;
}

export interface AnalysisResponse {
  status: "success";
  message: string;
  received: {
    date: string;
    time: string;
    latitude: number;
    longitude: number;
    image: ImageMetadata;
  };
}

