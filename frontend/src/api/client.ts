/**
 * MemoryVerse AI — API Client
 *
 * Fetch wrappers for backend endpoints.
 * Frontend never talks to LLM/Qdrant/Neo4j directly — everything
 * goes through the FastAPI backend (per Architecture.md §5).
 */

const API_BASE = 'http://localhost:8000/api';

export class ApiError extends Error {
  status: number;
  detail: string;
  suggestion: string;

  constructor(status: number, error: string, detail: string = '', suggestion: string = '') {
    super(error);
    this.status = status;
    this.detail = detail;
    this.suggestion = suggestion;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorData: any = {};
    try {
      errorData = await response.json();
      if (errorData.detail && typeof errorData.detail === 'object') {
        errorData = errorData.detail;
      }
    } catch {
      // Ignore JSON error
    }
    throw new ApiError(
      response.status,
      errorData.error || `Request failed (${response.status})`,
      errorData.detail || '',
      errorData.suggestion || 'Please try again.',
    );
  }
  return response.json();
}

// ---------------------------------------------------------------------------
// Types (mirror backend Pydantic schemas)
// ---------------------------------------------------------------------------

export interface ExtractedEntity {
  name: string;
  type: 'skill' | 'technology' | 'organization' | 'role';
}

export type DocumentCategory =
  | 'Projects'
  | 'Skills'
  | 'Certifications'
  | 'Internships'
  | 'Achievements'
  | 'Academics';

export interface DocumentResponse {
  id: string;
  filename: string;
  category: DocumentCategory;
  title: string;
  issuer: string | null;
  date: string | null;
  entities: ExtractedEntity[];
  confidence: number;
  summary: string | null;
  uploaded_at: string;
}

export interface UploadResponse {
  message: string;
  document: DocumentResponse;
}

export interface DocumentListResponse {
  documents: DocumentResponse[];
  total: number;
}

export interface GraphNode {
  id: string;
  name: string;
  type: string;
  category?: string;
  color: string;
  val: number;
  source_doc_id?: string;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relationship: string;
  explanation: string;
}

export interface GraphDataResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
  total_nodes: number;
  total_edges: number;
}

export interface TimelineEvent {
  id: string;
  date: string;
  title: string;
  category: DocumentCategory;
  summary?: string;
  issuer?: string;
  document_id: string;
  entities: ExtractedEntity[];
}

export interface TimelineResponse {
  events: TimelineEvent[];
  total: number;
}

export interface SearchHit {
  document_id: string;
  title: string;
  category: DocumentCategory;
  snippet: string;
  score: number;
  file_url: string;
  entities: ExtractedEntity[];
}

export interface SearchResponse {
  query: string;
  hits: SearchHit[];
  total: number;
}

export interface Citation {
  document_id: string;
  title: string;
  category: DocumentCategory;
  snippet: string;
  score: number;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
}

export interface ChatRequest {
  message: string;
  history?: ChatMessage[];
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
  confidence: number;
}

// --- Career Intelligence Types (Phase 4 — Hero Feature) ---

export interface CareerAnalysisRequest {
  job_title: string;
  company?: string;
  job_description: string;
}

export interface SkillMatch {
  skill: string;
  status: 'matched' | 'gap';
  confidence: number;
  evidence_doc_id?: string;
  evidence_title?: string;
  evidence_snippet?: string;
}

export interface CareerAnalysisResponse {
  overall_score: number;
  skills_score: number;
  experience_score: number;
  matched_skills: SkillMatch[];
  missing_gaps: string[];
  tailored_resume: string;
  cover_letter: string;
  citations: Citation[];
}

// ---------------------------------------------------------------------------
// API Functions
// ---------------------------------------------------------------------------

export async function uploadFile(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData,
  });

  return handleResponse<UploadResponse>(response);
}

export async function getDocuments(): Promise<DocumentListResponse> {
  const response = await fetch(`${API_BASE}/documents`);
  return handleResponse<DocumentListResponse>(response);
}

export async function getDocument(id: string): Promise<DocumentResponse> {
  const response = await fetch(`${API_BASE}/documents/${id}`);
  return handleResponse<DocumentResponse>(response);
}

export function getDocumentFileUrl(id: string): string {
  return `${API_BASE}/documents/${id}/file`;
}

export async function getGraphData(): Promise<GraphDataResponse> {
  const response = await fetch(`${API_BASE}/graph`);
  return handleResponse<GraphDataResponse>(response);
}

export async function getTimeline(): Promise<TimelineResponse> {
  const response = await fetch(`${API_BASE}/timeline`);
  return handleResponse<TimelineResponse>(response);
}

export async function searchDocuments(query: string, category?: string): Promise<SearchResponse> {
  const params = new URLSearchParams({ q: query });
  if (category && category !== 'All') {
    params.append('category', category);
  }
  const response = await fetch(`${API_BASE}/search?${params.toString()}`);
  return handleResponse<SearchResponse>(response);
}

export async function chatSearch(request: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  return handleResponse<ChatResponse>(response);
}

/**
 * Perform Career Match JD analysis and document synthesis.
 */
export async function analyzeCareerMatch(request: CareerAnalysisRequest): Promise<CareerAnalysisResponse> {
  const response = await fetch(`${API_BASE}/career/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  return handleResponse<CareerAnalysisResponse>(response);
}

export async function healthCheck(): Promise<{ status: string; phase: string }> {
  const response = await fetch(`${API_BASE}/health`);
  return handleResponse(response);
}
