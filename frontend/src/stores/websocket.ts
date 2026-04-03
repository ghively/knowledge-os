import { create } from 'zustand'

interface WebSocketState {
  socket: WebSocket | null
  isConnected: boolean
  reconnectAttempts: number
  connect: () => void
  disconnect: () => void
  send: (message: unknown) => void
  lastMessage: unknown | null
}

const MAX_RECONNECT_ATTEMPTS = 5
const RECONNECT_DELAY = 3000

export const useWebSocketStore = create<WebSocketState>((set, get) => ({
  socket: null,
  isConnected: false,
  reconnectAttempts: 0,
  lastMessage: null,

  connect: () => {
    const { socket, reconnectAttempts } = get()
    
    if (socket?.readyState === WebSocket.OPEN) return
    if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
      console.error('Max reconnect attempts reached')
      return
    }

    const ws = new WebSocket('ws://localhost:8000/ws')

    ws.onopen = () => {
      console.log('WebSocket connected')
      set({ 
        socket: ws, 
        isConnected: true,
        reconnectAttempts: 0 
      })
      
      // Send ping to keep connection alive
      const pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }))
        } else {
          clearInterval(pingInterval)
        }
      }, 30000)
    }

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        set({ lastMessage: message })
        
        // Handle different message types
        switch (message.type) {
          case 'pong':
            // Heartbeat response
            break
          case 'object.created':
          case 'object.updated':
          case 'object.deleted':
            // Trigger refetch of objects
            break
          case 'task.assigned':
          case 'task.status_changed':
          case 'task.completed':
            // Trigger refetch of tasks
            break
          case 'chat.message':
            // Handle chat message
            break
          default:
            console.log('WebSocket message:', message)
        }
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e)
      }
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected')
      set({ 
        socket: null, 
        isConnected: false,
        reconnectAttempts: reconnectAttempts + 1
      })
      
      // Attempt reconnect
      setTimeout(() => {
        get().connect()
      }, RECONNECT_DELAY)
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
  },

  disconnect: () => {
    const { socket } = get()
    if (socket) {
      socket.close()
      set({ socket: null, isConnected: false })
    }
  },

  send: (message) => {
    const { socket } = get()
    if (socket?.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket not connected')
    }
  },
}))
