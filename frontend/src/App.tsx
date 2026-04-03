import { useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import { useWebSocketStore } from './stores/websocket'
import { MainLayout } from './components/layout/MainLayout'
import { OutlinerPage } from './pages/OutlinerPage'
import { TasksPage } from './pages/TasksPage'
import { FilesPage } from './pages/FilesPage'
import { AgentsPage } from './pages/AgentsPage'
import { SettingsPage } from './pages/SettingsPage'
import { SearchPage } from './pages/SearchPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      refetchOnWindowFocus: false,
    },
  },
})

function App() {
  const { connect } = useWebSocketStore()

  useEffect(() => {
    // Connect to WebSocket on mount
    connect()
  }, [connect])

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <MainLayout>
          <Routes>
            <Route path="/" element={<OutlinerPage />} />
            <Route path="/object/:id" element={<OutlinerPage />} />
            <Route path="/tasks" element={<TasksPage />} />
            <Route path="/files" element={<FilesPage />} />
            <Route path="/agents" element={<AgentsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/search" element={<SearchPage />} />
          </Routes>
        </MainLayout>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
