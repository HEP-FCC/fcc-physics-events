/**
 * Defines the structure of a Process/Sample object received from the backend API.
 * This interface corresponds to the `ProcessWithDetails` Pydantic model.
 */
export interface Event {
  process_id: number;
  name: string;
  metadata: Record<string, any>;
  created_at: string; // ISO 8601 date string

  accelerator_id?: number | null;
  framework_id?: number | null;
  campaign_id?: number | null;
  detector_id?: number | null;

  detector_name?: string | null;
  campaign_name?: string | null;
  framework_name?: string | null;
  accelerator_name?: string | null;
}

/**
 * Defines the structure of the paginated response from the /query/ endpoint.
 */
export interface PaginatedResponse {
  total: number;
  items: Event[];
}
