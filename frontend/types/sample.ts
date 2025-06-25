export interface Sample {
  id: number;
  name: string;
  detector: string;
  framework: string;
  campaign: string;
  accelerator_type: string;
  // Add other fields as needed
  metadata?: Record<string, any>;
}

export interface SearchResponse {
  samples: Sample[];
  total: number;
}
