import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Objects API
export const objectsApi = {
  list: (params?: { type?: string; limit?: number; offset?: number }) =>
    api.get('/objects', { params }).then((r) => r.data),
  
  get: (id: string) => api.get(`/objects/${id}`).then((r) => r.data),
  
  create: (data: {
    type: string
    title: string
    icon?: string
    content?: string
    properties?: Record<string, unknown>
    layout?: string
  }) => api.post('/objects', data).then((r) => r.data),
  
  update: (id: string, data: Partial<{
    title: string
    icon: string
    content: string
    properties: Record<string, unknown>
    layout: string
  }>) => api.put(`/objects/${id}`, data).then((r) => r.data),
  
  delete: (id: string) => api.delete(`/objects/${id}`).then((r) => r.data),
  
  getRelations: (id: string) => api.get(`/objects/${id}/relations`).then((r) => r.data),
}

// Blocks API
export const blocksApi = {
  getForObject: (objectId: string) =>
    api.get(`/blocks/object/${objectId}`).then((r) => r.data.blocks),
  
  create: (objectId: string, data: {
    content: string
    type?: string
    level?: number
    properties?: Record<string, unknown>
    parent_id?: string | null
  }) => api.post(`/blocks?object_id=${objectId}`, data).then((r) => r.data),
  
  update: (id: string, data: Partial<{
    content: string
    type: string
    level: number
    properties: Record<string, unknown>
    order: number
  }>) => api.put(`/blocks/${id}`, data).then((r) => r.data),
  
  batchUpdate: (blocks: { id: string; order: number; parent_id?: string | null }[]) =>
    api.post('/blocks/batch-update', { blocks }).then((r) => r.data),
  
  delete: (id: string) => api.delete(`/blocks/${id}`).then((r) => r.data),
}

// Tasks API
export const tasksApi = {
  list: (params?: { status?: string; priority?: string; assigned_to?: string }) =>
    api.get('/tasks', { params }).then((r) => r.data),
  
  get: (id: string) => api.get(`/tasks/${id}`).then((r) => r.data),
  
  assign: (taskId: string, data: {
    agent_name: string
    priority: string
    include_context?: boolean
    additional_context?: string[]
  }) => api.post(`/tasks/${taskId}/assign`, data).then((r) => r.data),
  
  updateStatus: (taskId: string, data: {
    agent_name: string
    status: string
    current_action?: string
    notes?: string
  }) => api.post(`/tasks/${taskId}/status`, data).then((r) => r.data),
  
  getContext: (taskId: string) => api.get(`/tasks/${taskId}/context`).then((r) => r.data),
}

// Agents API
export const agentsApi = {
  list: () => api.get('/agents').then((r) => r.data.agents),
  
  get: (name: string) => api.get(`/agents/${name}`).then((r) => r.data),
  
  getTasks: (name: string, params?: { status?: string }) =>
    api.get(`/agents/${name}/tasks`, { params }).then((r) => r.data.tasks),
  
  chat: (name: string, content: string, sessionId?: string) =>
    api.post(`/agents/${name}/chat`, { content, session_id: sessionId }).then((r) => r.data),
  
  getChatHistory: (name: string, sessionId?: string) =>
    api.get(`/agents/${name}/chat`, { params: { session_id: sessionId } }).then((r) => r.data.messages),
  
  getMemories: (name: string, query?: string) =>
    api.get(`/agents/${name}/memories`, { params: { query } }).then((r) => r.data.memories),
}

// Search API
export const searchApi = {
  search: (query: string, type: 'semantic' | 'exact' = 'semantic', params?: { collection?: string; limit?: number }) =>
    api.get('/search', { params: { q: query, type, ...params } }).then((r) => r.data.results),
  
  findSimilar: (objectId: string, params?: { collection?: string; limit?: number }) =>
    api.get(`/search/similar/${objectId}`, { params }).then((r) => r.data),
}

// Files API
export const filesApi = {
  list: () => api.get('/files').then((r) => r.data.files),
  
  get: (id: string) => api.get(`/files/${id}`).then((r) => r.data),
  
  reindex: (id: string) => api.post(`/files/${id}/reindex`).then((r) => r.data),
}

// Settings API
export const settingsApi = {
  get: () => api.get('/settings').then((r) => r.data),
  
  update: (data: {
    openclaw_url?: string
    openclaw_token?: string
    backup_snapshots?: boolean
    backup_markdown?: boolean
    backup_git?: boolean
    git_repo_url?: string
    auto_index?: boolean
  }) => api.put('/settings', data).then((r) => r.data),
  
  getWatchedFolders: () => api.get('/settings/watched-folders').then((r) => r.data.folders),
  
  addWatchedFolder: (path: string, recursive: boolean = true, includePatterns?: string[], excludePatterns?: string[]) =>
    api.post('/settings/watched-folders', {
      path,
      recursive,
      include_patterns: includePatterns,
      exclude_patterns: excludePatterns,
    }).then((r) => r.data),
  
  removeWatchedFolder: (id: string) =>
    api.delete(`/settings/watched-folders/${id}`).then((r) => r.data),
  
  triggerBackup: (type: 'snapshot' | 'markdown' | 'git') =>
    api.post('/settings/backup', { type }).then((r) => r.data),
}

// Relations API
export const relationsApi = {
  create: (data: {
    source_id: string
    target_id: string
    relation_type: string
    metadata?: Record<string, unknown>
  }) => api.post('/relations', data).then((r) => r.data),
  
  delete: (id: string) => api.delete(`/relations/${id}`).then((r) => r.data),
  
  getForObject: (objectId: string) =>
    api.get(`/relations/object/${objectId}`).then((r) => r.data.relations),
}

// WebSocket API (for reference - actual WebSocket handled by useWebSocket hook)
export const websocketApi = {
  getUrl: (endpoint: string) => `${API_BASE_URL.replace('http', 'ws')}/ws/${endpoint}`,
}
