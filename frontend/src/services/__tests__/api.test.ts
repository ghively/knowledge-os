import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'
import {
  objectsApi,
  blocksApi,
  tasksApi,
  agentsApi,
  searchApi,
  filesApi,
  settingsApi,
  relationsApi,
  APIError,
} from '../api'

// Mock axios
vi.mock('axios')

describe('API Module', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })
})

describe('Objects API', () => {
  describe('list', () => {
    it('should list objects successfully', async () => {
      const mockResponse = {
        data: {
          objects: [
            { id: 'obj-1', title: 'Object 1' },
            { id: 'obj-2', title: 'Object 2' },
          ],
          total: 2,
        },
      }

      vi.mocked(axios.get).mockResolvedValue(mockResponse)

      const result = await objectsApi.list({ limit: 10 })

      expect(axios.get).toHaveBeenCalledWith('/api/objects', {
        params: { limit: 10 },
      })
      expect(result.objects).toHaveLength(2)
    })

    it('should handle API errors', async () => {
      vi.mocked(axios.get).mockRejectedValue({
        response: { status: 500, data: { detail: 'Server error' } },
      })

      await expect(objectsApi.list()).rejects.toThrow()
    })

    it('should apply filters correctly', async () => {
      vi.mocked(axios.get).mockResolvedValue({ data: { objects: [], total: 0 } })

      await objectsApi.list({
        object_type: 'note',
        tag: 'test',
        status: 'active',
      })

      expect(axios.get).toHaveBeenCalledWith('/api/objects', {
        params: {
          object_type: 'note',
          tag: 'test',
          status: 'active',
        },
      })
    })
  })

  describe('get', () => {
    it('should get a single object', async () => {
      const mockObject = { id: 'obj-1', title: 'Test Object' }
      vi.mocked(axios.get).mockResolvedValue({ data: mockObject })

      const result = await objectsApi.get('obj-1')

      expect(axios.get).toHaveBeenCalledWith('/api/objects/obj-1')
      expect(result.id).toBe('obj-1')
    })

    it('should handle 404 errors', async () => {
      vi.mocked(axios.get).mockRejectedValue({
        response: { status: 404, data: { detail: 'Not found' } },
      })

      await expect(objectsApi.get('nonexistent')).rejects.toThrow()
    })
  })

  describe('create', () => {
    it('should create a new object', async () => {
      const newObject = { title: 'New Object', content: 'Content' }
      const mockResponse = { id: 'obj-1', ...newObject }

      vi.mocked(axios.post).mockResolvedValue({ data: mockResponse })

      const result = await objectsApi.create(newObject)

      expect(axios.post).toHaveBeenCalledWith('/api/objects', newObject)
      expect(result.id).toBe('obj-1')
    })

    it('should handle validation errors', async () => {
      vi.mocked(axios.post).mockRejectedValue({
        response: { status: 422, data: { detail: 'Validation error' } },
      })

      await expect(objectsApi.create({})).rejects.toThrow()
    })
  })

  describe('update', () => {
    it('should update an object', async () => {
      const updates = { title: 'Updated Title' }
      const mockResponse = { id: 'obj-1', ...updates }

      vi.mocked(axios.put).mockResolvedValue({ data: mockResponse })

      const result = await objectsApi.update('obj-1', updates)

      expect(axios.put).toHaveBeenCalledWith('/api/objects/obj-1', updates)
      expect(result.title).toBe('Updated Title')
    })
  })

  describe('delete', () => {
    it('should delete an object', async () => {
      vi.mocked(axios.delete).mockResolvedValue({
        data: { message: 'Object deleted' },
      })

      await objectsApi.delete('obj-1')

      expect(axios.delete).toHaveBeenCalledWith('/api/objects/obj-1')
    })
  })

  describe('getRelations', () => {
    it('should get object relations', async () => {
      const mockRelations = {
        relations: [
          { id: 'rel-1', relation_type: 'references' },
        ],
        total: 1,
      }

      vi.mocked(axios.get).mockResolvedValue({ data: mockRelations })

      const result = await objectsApi.getRelations('obj-1')

      expect(axios.get).toHaveBeenCalledWith('/api/objects/obj-1/relations')
      expect(result.relations).toHaveLength(1)
    })
  })
})

describe('Blocks API', () => {
  describe('getForObject', () => {
    it('should get blocks for an object', async () => {
      const mockBlocks = {
        blocks: [
          { id: 'block-1', content: 'Block 1' },
          { id: 'block-2', content: 'Block 2' },
        ],
        total: 2,
      }

      vi.mocked(axios.get).mockResolvedValue({ data: mockBlocks })

      const result = await blocksApi.getForObject('obj-1')

      expect(axios.get).toHaveBeenCalledWith('/api/blocks/object/obj-1')
      expect(result.blocks).toHaveLength(2)
    })
  })

  describe('create', () => {
    it('should create a new block', async () => {
      const newBlock = {
        object_id: 'obj-1',
        content: 'New block',
        block_type: 'text',
      }

      const mockResponse = { id: 'block-1', ...newBlock }

      vi.mocked(axios.post).mockResolvedValue({ data: mockResponse })

      const result = await blocksApi.create('obj-1', newBlock)

      expect(axios.post).toHaveBeenCalledWith('/api/blocks', newBlock)
      expect(result.id).toBe('block-1')
    })
  })

  describe('update', () => {
    it('should update a block', async () => {
      const updates = { content: 'Updated content' }
      const mockResponse = { id: 'block-1', ...updates }

      vi.mocked(axios.put).mockResolvedValue({ data: mockResponse })

      const result = await blocksApi.update('block-1', updates)

      expect(axios.put).toHaveBeenCalledWith('/api/blocks/block-1', updates)
      expect(result.content).toBe('Updated content')
    })
  })

  describe('batchUpdate', () => {
    it('should batch update blocks', async () => {
      const blocks = [
        { id: 'block-1', content: 'Updated 1' },
        { id: 'block-2', content: 'Updated 2' },
      ]

      vi.mocked(axios.post).mockResolvedValue({
        data: { message: 'Blocks updated' },
      })

      await blocksApi.batchUpdate(blocks)

      expect(axios.post).toHaveBeenCalledWith('/api/blocks/batch-update', {
        blocks,
      })
    })
  })

  describe('syncForObject', () => {
    it('should sync blocks for an object', async () => {
      const blocks = [
        { id: 'block-1', content: 'Synced 1', block_type: 'text', order: 0 },
      ]

      vi.mocked(axios.put).mockResolvedValue({
        data: { message: 'Blocks synced' },
      })

      await blocksApi.syncForObject('obj-1', blocks)

      expect(axios.put).toHaveBeenCalledWith('/api/blocks/object/obj-1/sync', {
        blocks,
      })
    })
  })

  describe('delete', () => {
    it('should delete a block', async () => {
      vi.mocked(axios.delete).mockResolvedValue({
        data: { message: 'Block deleted' },
      })

      await blocksApi.delete('block-1')

      expect(axios.delete).toHaveBeenCalledWith('/api/blocks/block-1')
    })
  })
})

describe('Tasks API', () => {
  describe('list', () => {
    it('should list tasks with filters', async () => {
      const mockTasks = {
        tasks: [{ id: 'task-1', title: 'Task 1' }],
        total: 1,
        counts: { by_status: {}, by_priority: {} },
      }

      vi.mocked(axios.get).mockResolvedValue({ data: mockTasks })

      const result = await tasksApi.list({ status: 'todo', priority: 'high' })

      expect(axios.get).toHaveBeenCalledWith('/api/tasks', {
        params: { status: 'todo', priority: 'high' },
      })
      expect(result.tasks).toHaveLength(1)
    })
  })

  describe('get', () => {
    it('should get a single task', async () => {
      const mockTask = { id: 'task-1', title: 'Test Task' }
      vi.mocked(axios.get).mockResolvedValue({ data: mockTask })

      const result = await tasksApi.get('task-1')

      expect(result.id).toBe('task-1')
    })
  })

  describe('assign', () => {
    it('should assign task to agent', async () => {
      vi.mocked(axios.post).mockResolvedValue({
        data: { agent: 'test-agent', task_id: 'task-1' },
      })

      await tasksApi.assign('task-1', { agent_name: 'test-agent' })

      expect(axios.post).toHaveBeenCalledWith('/api/tasks/task-1/assign', {
        agent_name: 'test-agent',
      })
    })
  })

  describe('updateStatus', () => {
    it('should update task status', async () => {
      vi.mocked(axios.post).mockResolvedValue({
        data: { status: 'in-progress' },
      })

      await tasksApi.updateStatus('task-1', { status: 'in-progress' })

      expect(axios.post).toHaveBeenCalledWith('/api/tasks/task-1/status', {
        status: 'in-progress',
      })
    })
  })

  describe('getContext', () => {
    it('should get task context', async () => {
      const mockContext = {
        context: {
          entities: [],
          relations: [],
        },
      }

      vi.mocked(axios.get).mockResolvedValue({ data: mockContext })

      const result = await tasksApi.getContext('task-1')

      expect(result.context).toBeDefined()
    })
  })
})

describe('Agents API', () => {
  describe('list', () => {
    it('should list all agents', async () => {
      const mockAgents = {
        agents: [
          { name: 'agent-1', status: 'idle' },
          { name: 'agent-2', status: 'working' },
        ],
      }

      vi.mocked(axios.get).mockResolvedValue({ data: mockAgents })

      const result = await agentsApi.list()

      expect(result.agents).toHaveLength(2)
    })
  })

  describe('get', () => {
    it('should get a single agent', async () => {
      const mockAgent = { name: 'agent-1', status: 'idle' }
      vi.mocked(axios.get).mockResolvedValue({ data: mockAgent })

      const result = await agentsApi.get('agent-1')

      expect(result.name).toBe('agent-1')
    })
  })

  describe('chat', () => {
    it('should send chat message', async () => {
      const mockResponse = {
        response: 'Agent response',
        session_id: 'session-1',
      }

      vi.mocked(axios.post).mockResolvedValue({ data: mockResponse })

      const result = await agentsApi.chat('agent-1', 'Hello')

      expect(axios.post).toHaveBeenCalledWith('/api/agents/agent-1/chat', {
        content: 'Hello',
      })
      expect(result.response).toBe('Agent response')
    })
  })

  describe('getChatHistory', () => {
    it('should get chat history', async () => {
      const mockHistory = {
        messages: [
          { role: 'user', content: 'Hello' },
          { role: 'assistant', content: 'Hi there!' },
        ],
      }

      vi.mocked(axios.get).mockResolvedValue({ data: mockHistory })

      const result = await agentsApi.getChatHistory('agent-1', 'session-1')

      expect(result.messages).toHaveLength(2)
    })
  })
})

describe('Search API', () => {
  describe('search', () => {
    it('should perform search', async () => {
      const mockResults = {
        results: [
          { id: 'obj-1', score: 0.95, title: 'Result 1' },
        ],
        total: 1,
      }

      vi.mocked(axios.get).mockResolvedValue({ data: mockResults })

      const result = await searchApi.search('test query', 'object')

      expect(axios.get).toHaveBeenCalledWith('/api/search', {
        params: { query: 'test query', type: 'object' },
      })
      expect(result.results).toHaveLength(1)
    })
  })

  describe('findSimilar', () => {
    it('should find similar content', async () => {
      const mockResults = {
        results: [
          { id: 'obj-2', score: 0.88 },
        ],
        total: 1,
      }

      vi.mocked(axios.get).mockResolvedValue({ data: mockResults })

      const result = await searchApi.findSimilar('obj-1')

      expect(result.results).toBeDefined()
    })
  })
})

describe('Files API', () => {
  describe('list', () => {
    it('should list files', async () => {
      const mockFiles = {
        files: [
          { id: 'file-1', filename: 'test.pdf' },
        ],
      }

      vi.mocked(axios.get).mockResolvedValue({ data: mockFiles })

      const result = await filesApi.list()

      expect(result.files).toBeDefined()
    })
  })

  describe('reindex', () => {
    it('should reindex a file', async () => {
      vi.mocked(axios.post).mockResolvedValue({
        data: { message: 'File reindexed' },
      })

      await filesApi.reindex('file-1')

      expect(axios.post).toHaveBeenCalledWith('/api/files/file-1/reindex')
    })
  })
})

describe('Settings API', () => {
  describe('get', () => {
    it('should get settings', async () => {
      const mockSettings = { theme: 'dark', language: 'en' }
      vi.mocked(axios.get).mockResolvedValue({ data: mockSettings })

      const result = await settingsApi.get()

      expect(result.theme).toBe('dark')
    })
  })

  describe('update', () => {
    it('should update settings', async () => {
      const updates = { theme: 'light' }
      vi.mocked(axios.put).mockResolvedValue({ data: updates })

      await settingsApi.update(updates)

      expect(axios.put).toHaveBeenCalledWith('/api/settings', updates)
    })
  })

  describe('getWatchedFolders', () => {
    it('should get watched folders', async () => {
      const mockFolders = {
        folders: [
          { id: 'folder-1', path: '/path/to/folder' },
        ],
      }

      vi.mocked(axios.get).mockResolvedValue({ data: mockFolders })

      const result = await settingsApi.getWatchedFolders()

      expect(result.folders).toBeDefined()
    })
  })

  describe('triggerBackup', () => {
    it('should trigger backup', async () => {
      vi.mocked(axios.post).mockResolvedValue({
        data: { message: 'Backup complete' },
      })

      await settingsApi.triggerBackup('qdrant')

      expect(axios.post).toHaveBeenCalledWith('/api/settings/backup', {
        type: 'qdrant',
      })
    })
  })
})

describe('Relations API', () => {
  describe('create', () => {
    it('should create a relation', async () => {
      const relation = {
        source_type: 'object',
        source_id: 'obj-1',
        target_type: 'object',
        target_id: 'obj-2',
        relation_type: 'references',
      }

      const mockResponse = { id: 'rel-1', ...relation }

      vi.mocked(axios.post).mockResolvedValue({ data: mockResponse })

      const result = await relationsApi.create(relation)

      expect(axios.post).toHaveBeenCalledWith('/api/relations', relation)
      expect(result.id).toBe('rel-1')
    })
  })

  describe('getForObject', () => {
    it('should get relations for object', async () => {
      const mockRelations = {
        relations: [
          { id: 'rel-1', relation_type: 'references' },
        ],
        total: 1,
      }

      vi.mocked(axios.get).mockResolvedValue({ data: mockRelations })

      const result = await relationsApi.getForObject('obj-1')

      expect(result.relations).toHaveLength(1)
    })
  })

  describe('delete', () => {
    it('should delete a relation', async () => {
      vi.mocked(axios.delete).mockResolvedValue({
        data: { message: 'Relation deleted' },
      })

      await relationsApi.delete('rel-1')

      expect(axios.delete).toHaveBeenCalledWith('/api/relations/rel-1')
    })
  })
})

describe('APIError', () => {
  it('should create error with status code', () => {
    const error = new APIError('Not found', 404)

    expect(error.message).toBe('Not found')
    expect(error.status).toBe(404)
  })

  it('should create error without status code', () => {
    const error = new APIError('Network error')

    expect(error.message).toBe('Network error')
    expect(error.status).toBeUndefined()
  })
})
