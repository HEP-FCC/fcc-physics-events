/**
 * Defines the structure of a Dataset object received from the backend API.
 * This interface corresponds to the `DatasetWithDetails` Pydantic model.
 */
export interface Dataset {
    dataset_id: number;
    name: string;
    metadata: Record<string, unknown>;
    created_at: string; // ISO 8601 date string
    last_edited_at?: string; // ISO 8601 date string for when metadata was last edited

    accelerator_id?: number | null;
    stage_id?: number | null;
    campaign_id?: number | null;
    detector_id?: number | null;

    detector_name?: string | null;
    campaign_name?: string | null;
    stage_name?: string | null;
    accelerator_name?: string | null;
}

/**
 * Defines the structure of the paginated response from the /query/ endpoint.
 * Some API versions return 'data' while others return 'items'.
 */
export interface PaginatedResponse {
    total: number;
    items?: Dataset[];
    data?: Dataset[];
}
