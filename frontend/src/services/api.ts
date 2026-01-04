import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosResponse } from 'axios';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

// Create axios instance with default config
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// Request interceptor for adding auth tokens or logging
apiClient.interceptors.request.use(
  (config) => {
    // Add any auth token here if needed
    // const token = localStorage.getItem('token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with error status
      console.error('API Error:', error.response.status, error.response.data);
    } else if (error.request) {
      // Request was made but no response received
      console.error('Network Error:', error.message);
    } else {
      // Error in request setup
      console.error('Request Error:', error.message);
    }
    return Promise.reject(error);
  }
);

// Generic API methods
export const api = {
  get: <T>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => 
    apiClient.get<T>(url, config),
  
  post: <T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => 
    apiClient.post<T>(url, data, config),
  
  put: <T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => 
    apiClient.put<T>(url, data, config),
  
  patch: <T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => 
    apiClient.patch<T>(url, data, config),
  
  delete: <T>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => 
    apiClient.delete<T>(url, config),
};

// Artwork-specific API endpoints
export const artworkApi = {
  // Get all artworks with optional pagination
  getAll: (params?: { page?: number; limit?: number; search?: string }) => 
    api.get<ArtworkListResponse>('/artworks', { params }),
  
  // Get single artwork by ID
  getById: (id: string) => 
    api.get<Artwork>(`/artworks/${id}`),
  
  // Get artwork provenance history
  getProvenance: (id: string) => 
    api.get<ProvenanceRecord[]>(`/artworks/${id}/provenance`),
  
  // Create new artwork
  create: (data: CreateArtworkRequest) => 
    api.post<Artwork>('/artworks', data),
  
  // Get QR code for artwork
  getQRCode: (id: string) => 
    api.get<Blob>(`/artworks/${id}/qr`, { responseType: 'blob' }),
};

// SPARQL API endpoints
export const sparqlApi = {
  // Execute a SPARQL query
  query: (sparqlQuery: string) => 
    api.post<SPARQLResponse>('/sparql', { query: sparqlQuery }),
};

// Search API endpoints
export const searchApi = {
  // Search artworks
  search: (query: string, filters?: SearchFilters) => 
    api.get<SearchResponse>('/search', { params: { q: query, ...filters } }),
  
  // Get recommendations for an artwork
  getRecommendations: (artworkId: string) => 
    api.get<Artwork[]>(`/artworks/${artworkId}/recommendations`),
};

// Type definitions (to be expanded based on backend schema)
export interface Artwork {
  id: string;
  title: string;
  artist?: string;
  artistUri?: string;
  dateCreated?: string;
  medium?: string;
  dimensions?: string;
  description?: string;
  imageUrl?: string;
  currentLocation?: string;
  provenance?: ProvenanceRecord[];
  externalLinks?: {
    dbpedia?: string;
    wikidata?: string;
    getty?: string;
  };
}

export interface ProvenanceRecord {
  id: string;
  date: string;
  event: string;
  owner?: string;
  location?: string;
  description?: string;
  sourceUri?: string;
}

export interface ArtworkListResponse {
  items: Artwork[];
  total: number;
  page: number;
  limit: number;
  hasMore: boolean;
}

export interface CreateArtworkRequest {
  title: string;
  artist?: string;
  dateCreated?: string;
  medium?: string;
  description?: string;
}

export interface SPARQLResponse {
  head: { vars: string[] };
  results: {
    bindings: Record<string, { type: string; value: string }>[];
  };
}

export interface SearchFilters {
  artist?: string;
  period?: string;
  medium?: string;
  location?: string;
}

export interface SearchResponse {
  results: Artwork[];
  total: number;
  facets?: {
    artists: { name: string; count: number }[];
    periods: { name: string; count: number }[];
    media: { name: string; count: number }[];
  };
}

export default apiClient;

