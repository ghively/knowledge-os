import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

describe('WebSocket Store', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('initial state', () => {
    it('should have initial state', () => {
      // Import the store after mocking
      const { useWebSocketStore } = require('../websocket')

      const store = useWebSocketStore.getState()

      expect(store.socket).toBeNull()
      expect(store.isConnected).toBe(false)
      expect(store.reconnectAttempts).toBe(0)
      expect(store.lastMessage).toBeNull()
    })
  })

  describe('connect', () => {
    it('should create WebSocket connection', async () => {
      // Mock WebSocket
      const mockWebSocket = {
        readyState: WebSocket.OPEN,
        send: vi.fn(),
        close: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      }

      global.WebSocket = vi.fn(() => mockWebSocket) as any

      const { useWebSocketStore } = require('../websocket')

      useWebSocketStore.getState().connect('ws://localhost:8000/ws')

      // Wait a tick for connection
      await new Promise(resolve => setTimeout(resolve, 0))

      expect(WebSocket).toHaveBeenCalledWith('ws://localhost:8000/ws')
    })

    it('should set isConnected to true on open', async () => {
      const mockWebSocket = {
        readyState: WebSocket.CONNECTING,
        send: vi.fn(),
        close: vi.fn(),
        addEventListener: vi.fn((event, callback) => {
          if (event === 'open') {
            setTimeout(() => callback(), 0)
          }
        }),
        removeEventListener: vi.fn(),
      }

      global.WebSocket = vi.fn(() => mockWebSocket) as any

      const { useWebSocketStore } = require('../websocket')

      useWebSocketStore.getState().connect('ws://localhost:8000/ws')

      // Wait for open event
      await new Promise(resolve => setTimeout(resolve, 10))

      expect(useWebSocketStore.getState().isConnected).toBe(true)
    })

    it('should handle connection errors', async () => {
      const mockWebSocket = {
        readyState: WebSocket.CONNECTING,
        send: vi.fn(),
        close: vi.fn(),
        addEventListener: vi.fn((event, callback) => {
          if (event === 'error') {
            setTimeout(() => callback(new Error('Connection failed')), 0)
          }
        }),
        removeEventListener: vi.fn(),
      }

      global.WebSocket = vi.fn(() => mockWebSocket) as any

      const { useWebSocketStore } = require('../websocket')

      useWebSocketStore.getState().connect('ws://localhost:8000/ws')

      // Wait for error event
      await new Promise(resolve => setTimeout(resolve, 10))

      // Should attempt reconnection
      expect(useWebSocketStore.getState().reconnectAttempts).toBeGreaterThan(0)
    })
  })

  describe('disconnect', () => {
    it('should close WebSocket connection', () => {
      const mockWebSocket = {
        readyState: WebSocket.OPEN,
        send: vi.fn(),
        close: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      }

      global.WebSocket = vi.fn(() => mockWebSocket) as any

      const { useWebSocketStore } = require('../websocket')

      useWebSocketStore.getState().connect('ws://localhost:8000/ws')
      useWebSocketStore.getState().disconnect()

      expect(mockWebSocket.close).toHaveBeenCalled()
      expect(useWebSocketStore.getState().socket).toBeNull()
      expect(useWebSocketStore.getState().isConnected).toBe(false)
    })
  })

  describe('send', () => {
    it('should send message through WebSocket', () => {
      const mockWebSocket = {
        readyState: WebSocket.OPEN,
        send: vi.fn(),
        close: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      }

      global.WebSocket = vi.fn(() => mockWebSocket) as any

      const { useWebSocketStore } = require('../websocket')

      useWebSocketStore.getState().connect('ws://localhost:8000/ws')

      const message = { type: 'test', data: 'hello' }
      useWebSocketStore.getState().send(message)

      expect(mockWebSocket.send).toHaveBeenCalledWith(JSON.stringify(message))
    })

    it('should not send if not connected', () => {
      const mockWebSocket = {
        readyState: WebSocket.CLOSED,
        send: vi.fn(),
        close: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      }

      global.WebSocket = vi.fn(() => mockWebSocket) as any

      const { useWebSocketStore } = require('../websocket')

      useWebSocketStore.getState().connect('ws://localhost:8000/ws')

      const message = { type: 'test', data: 'hello' }
      useWebSocketStore.getState().send(message)

      expect(mockWebSocket.send).not.toHaveBeenCalled()
    })
  })

  describe('message handling', () => {
    it('should handle incoming messages', async () => {
      const mockWebSocket = {
        readyState: WebSocket.OPEN,
        send: vi.fn(),
        close: vi.fn(),
        addEventListener: vi.fn((event, callback) => {
          if (event === 'message') {
            setTimeout(() => {
              callback({ data: JSON.stringify({ type: 'test', data: 'hello' }) })
            }, 0)
          }
        }),
        removeEventListener: vi.fn(),
      }

      global.WebSocket = vi.fn(() => mockWebSocket) as any

      const { useWebSocketStore } = require('../websocket')

      useWebSocketStore.getState().connect('ws://localhost:8000/ws')

      // Wait for message event
      await new Promise(resolve => setTimeout(resolve, 10))

      expect(useWebSocketStore.getState().lastMessage).toEqual({
        type: 'test',
        data: 'hello',
      })
    })

    it('should handle invalid messages', async () => {
      const mockWebSocket = {
        readyState: WebSocket.OPEN,
        send: vi.fn(),
        close: vi.fn(),
        addEventListener: vi.fn((event, callback) => {
          if (event === 'message') {
            setTimeout(() => {
              callback({ data: 'invalid json' })
            }, 0)
          }
        }),
        removeEventListener: vi.fn(),
      }

      global.WebSocket = vi.fn(() => mockWebSocket) as any

      const { useWebSocketStore } = require('../websocket')

      useWebSocketStore.getState().connect('ws://localhost:8000/ws')

      // Wait for message event
      await new Promise(resolve => setTimeout(resolve, 10))

      // Should not crash or set invalid message
      expect(useWebSocketStore.getState().lastMessage).not.toEqual({
        data: 'invalid json',
      })
    })
  })

  describe('reconnection', () => {
    it('should attempt reconnection on disconnect', async () => {
      let connectCount = 0

      const mockWebSocket = {
        readyState: WebSocket.OPEN,
        send: vi.fn(),
        close: vi.fn(),
        addEventListener: vi.fn((event, callback) => {
          if (event === 'close') {
            setTimeout(() => {
              callback({ code: 1006 })
            }, 0)
          }
        }),
        removeEventListener: vi.fn(),
      }

      global.WebSocket = vi.fn(() => {
        connectCount++
        return mockWebSocket
      }) as any

      const { useWebSocketStore } = require('../websocket')

      useWebSocketStore.getState().connect('ws://localhost:8000/ws')

      // Wait for close event and potential reconnection
      await new Promise(resolve => setTimeout(resolve, 100))

      // Should have attempted reconnection
      expect(connectCount).toBeGreaterThan(1)
    })

    it('should limit reconnection attempts', async () => {
      const mockWebSocket = {
        readyState: WebSocket.CONNECTING,
        send: vi.fn(),
        close: vi.fn(),
        addEventListener: vi.fn((event, callback) => {
          if (event === 'close') {
            setTimeout(() => {
              callback({ code: 1006 })
            }, 0)
          }
        }),
        removeEventListener: vi.fn(),
      }

      global.WebSocket = vi.fn(() => mockWebSocket) as any

      const { useWebSocketStore } = require('../websocket')

      // Set max reconnection attempts
      useWebSocketStore.getState().setMaxReconnectAttempts(3)

      useWebSocketStore.getState().connect('ws://localhost:8000/ws')

      // Wait for multiple reconnection attempts
      await new Promise(resolve => setTimeout(resolve, 200))

      // Should respect max attempts
      expect(useWebSocketStore.getState().reconnectAttempts).toBeLessThanOrEqual(3)
    })
  })

  describe('ping/pong', () => {
    it('should send ping messages', async () => {
      vi.useFakeTimers()

      const mockWebSocket = {
        readyState: WebSocket.OPEN,
        send: vi.fn(),
        close: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      }

      global.WebSocket = vi.fn(() => mockWebSocket) as any

      const { useWebSocketStore } = require('../websocket')

      useWebSocketStore.getState().connect('ws://localhost:8000/ws')

      // Advance timer to trigger ping
      vi.advanceTimersByTime(30000)

      expect(mockWebSocket.send).toHaveBeenCalledWith(
        JSON.stringify({ type: 'ping' })
      )

      vi.useRealTimers()
    })
  })

  describe('event handlers', () => {
    it('should call custom onOpen handler', async () => {
      const onOpen = vi.fn()

      const mockWebSocket = {
        readyState: WebSocket.CONNECTING,
        send: vi.fn(),
        close: vi.fn(),
        addEventListener: vi.fn((event, callback) => {
          if (event === 'open') {
            setTimeout(() => callback(), 0)
          }
        }),
        removeEventListener: vi.fn(),
      }

      global.WebSocket = vi.fn(() => mockWebSocket) as any

      const { useWebSocketStore } = require('../websocket')

      useWebSocketStore.getState().connect('ws://localhost:8000/ws', { onOpen })

      // Wait for open event
      await new Promise(resolve => setTimeout(resolve, 10))

      expect(onOpen).toHaveBeenCalled()
    })

    it('should call custom onClose handler', async () => {
      const onClose = vi.fn()

      const mockWebSocket = {
        readyState: WebSocket.OPEN,
        send: vi.fn(),
        close: vi.fn(),
        addEventListener: vi.fn((event, callback) => {
          if (event === 'close') {
            setTimeout(() => callback({ code: 1000 }), 0)
          }
        }),
        removeEventListener: vi.fn(),
      }

      global.WebSocket = vi.fn(() => mockWebSocket) as any

      const { useWebSocketStore } = require('../websocket')

      useWebSocketStore.getState().connect('ws://localhost:8000/ws', { onClose })

      // Wait for close event
      await new Promise(resolve => setTimeout(resolve, 10))

      expect(onClose).toHaveBeenCalled()
    })

    it('should call custom onError handler', async () => {
      const onError = vi.fn()

      const mockWebSocket = {
        readyState: WebSocket.CONNECTING,
        send: vi.fn(),
        close: vi.fn(),
        addEventListener: vi.fn((event, callback) => {
          if (event === 'error') {
            setTimeout(() => callback(new Error('Connection failed')), 0)
          }
        }),
        removeEventListener: vi.fn(),
      }

      global.WebSocket = vi.fn(() => mockWebSocket) as any

      const { useWebSocketStore } = require('../websocket')

      useWebSocketStore.getState().connect('ws://localhost:8000/ws', { onError })

      // Wait for error event
      await new Promise(resolve => setTimeout(resolve, 10))

      expect(onError).toHaveBeenCalled()
    })

    it('should call custom onMessage handler', async () => {
      const onMessage = vi.fn()

      const mockWebSocket = {
        readyState: WebSocket.OPEN,
        send: vi.fn(),
        close: vi.fn(),
        addEventListener: vi.fn((event, callback) => {
          if (event === 'message') {
            setTimeout(() => {
              callback({ data: JSON.stringify({ type: 'test' }) })
            }, 0)
          }
        }),
        removeEventListener: vi.fn(),
      }

      global.WebSocket = vi.fn(() => mockWebSocket) as any

      const { useWebSocketStore } = require('../websocket')

      useWebSocketStore.getState().connect('ws://localhost:8000/ws', { onMessage })

      // Wait for message event
      await new Promise(resolve => setTimeout(resolve, 10))

      expect(onMessage).toHaveBeenCalledWith({ type: 'test' })
    })
  })
})
