import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { 
  PanelLeft, 
  FileText, 
  CheckSquare, 
  Folder, 
  Bot, 
  Plus,
  ChevronRight,
  ChevronDown,
  Settings,
  Calendar,
  Inbox,
  Loader2
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { useQuery } from '@tanstack/react-query'
import { agentsApi, settingsApi, type AgentItem } from '@/services/api'

interface SidebarProps {
  collapsed: boolean
  onToggle: () => void
  onAgentClick?: (agent: AgentItem) => void
}

const spaces = [
  { id: 'notes', name: 'Notes', icon: FileText, href: '/' },
  { id: 'tasks', name: 'Tasks', icon: CheckSquare, href: '/tasks' },
  { id: 'files', name: 'Files', icon: Folder, href: '/files' },
  { id: 'agents', name: 'Agents', icon: Bot, href: '/agents' },
]

const quickLinks = [
  { id: 'today', name: 'Today', icon: Calendar, href: '/tasks?filter=today' },
  { id: 'inbox', name: 'Inbox', icon: Inbox, href: '/inbox' },
]

export function Sidebar({ collapsed, onToggle, onAgentClick }: SidebarProps) {
  const location = useLocation()
  const [spacesOpen, setSpacesOpen] = useState(true)
  const [agentsOpen, setAgentsOpen] = useState(true)
  const [foldersOpen, setFoldersOpen] = useState(true)

  // Fetch agents
  const { data: agentsData, isLoading: agentsLoading } = useQuery({
    queryKey: ['agents'],
    queryFn: agentsApi.list,
    refetchInterval: 10000, // Poll every 10 seconds for status updates
  })
  const agents = agentsData?.agents ?? []

  // Fetch watched folders
  const { data: watchedFoldersData, isLoading: foldersLoading } = useQuery({
    queryKey: ['watched-folders'],
    queryFn: settingsApi.getWatchedFolders,
  })
  const watchedFolders = watchedFoldersData?.folders ?? []

  const getStatusColor = (status: AgentItem['status']) => {
    switch (status) {
      case 'active':
      case 'busy':
      case 'working': return 'bg-blue-500 animate-pulse'
      case 'idle': return 'bg-green-500'
      case 'error': return 'bg-red-500'
      case 'offline': return 'bg-gray-400'
      default: return 'bg-gray-400'
    }
  }

  if (collapsed) {
    return (
      <div className="w-14 border-r bg-card flex flex-col items-center py-4">
        <Button variant="ghost" size="icon" onClick={onToggle} className="mb-4">
          <PanelLeft className="h-5 w-5" />
        </Button>
        
        <div className="flex flex-col gap-2">
          {spaces.map((space) => (
            <Link key={space.id} to={space.href}>
              <Button
                variant={location.pathname === space.href ? 'secondary' : 'ghost'}
                size="icon"
                className="relative"
              >
                <space.icon className="h-5 w-5" />
              </Button>
            </Link>
          ))}
        </div>

        {/* Agent indicators */}
        <div className="mt-auto flex flex-col gap-2">
          {agents.slice(0, 3).map((agent: AgentItem) => (
            <Button
              key={agent.id}
              variant="ghost"
              size="icon"
              className="relative"
              onClick={() => onAgentClick?.(agent)}
            >
              <Bot className="h-5 w-5" />
              <span className={cn(
                "absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-card",
                getStatusColor(agent.status)
              )} />
            </Button>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="w-64 border-r bg-card flex flex-col">
      {/* Header */}
      <div className="h-14 border-b flex items-center justify-between px-4">
        <Link to="/" className="font-semibold text-lg">
          Knowledge OS
        </Link>
        <Button variant="ghost" size="icon" onClick={onToggle}>
          <PanelLeft className="h-5 w-5" />
        </Button>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-3 space-y-4">
          {/* Quick Links */}
          <div className="space-y-1">
            {quickLinks.map((link) => (
              <Link key={link.id} to={link.href}>
                <Button
                  variant={location.pathname === link.href ? 'secondary' : 'ghost'}
                  className="w-full justify-start gap-2"
                >
                  <link.icon className="h-4 w-4" />
                  {link.name}
                </Button>
              </Link>
            ))}
          </div>

          {/* Spaces */}
          <Collapsible open={spacesOpen} onOpenChange={setSpacesOpen}>
            <CollapsibleTrigger asChild>
              <Button variant="ghost" className="w-full justify-between">
                <span className="text-sm font-medium text-muted-foreground">Spaces</span>
                {spacesOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <div className="space-y-1 pt-1">
                {spaces.map((space) => (
                  <Link key={space.id} to={space.href}>
                    <Button
                      variant={location.pathname === space.href ? 'secondary' : 'ghost'}
                      className="w-full justify-start gap-2"
                    >
                      <space.icon className="h-4 w-4" />
                      {space.name}
                    </Button>
                  </Link>
                ))}
              </div>
            </CollapsibleContent>
          </Collapsible>

          {/* Agents */}
          <Collapsible open={agentsOpen} onOpenChange={setAgentsOpen}>
            <CollapsibleTrigger asChild>
              <Button variant="ghost" className="w-full justify-between">
                <span className="text-sm font-medium text-muted-foreground">Agents</span>
                <div className="flex items-center gap-2">
                  {agentsLoading && <Loader2 className="h-3 w-3 animate-spin" />}
                  {agentsOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                </div>
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <div className="space-y-1 pt-1">
                {agentsLoading ? (
                  <div className="text-sm text-muted-foreground px-3 py-2">Loading agents...</div>
                ) : agents.length === 0 ? (
                  <div className="text-sm text-muted-foreground px-3 py-2">No agents configured</div>
                ) : (
                  agents.map((agent: AgentItem) => (
                    <Button
                      key={agent.id}
                      variant="ghost"
                      className="w-full justify-start gap-2"
                      onClick={() => onAgentClick?.(agent)}
                    >
                      <div className={cn("h-2 w-2 rounded-full flex-shrink-0", getStatusColor(agent.status))} />
                      <span className="truncate">@{agent.name}</span>
                      {agent.current_task && (
                        <span className="text-xs text-muted-foreground ml-auto truncate max-w-[60px]">
                          {agent.current_task}
                        </span>
                      )}
                    </Button>
                  ))
                )}
              </div>
            </CollapsibleContent>
          </Collapsible>

          {/* Watched Folders */}
          <Collapsible open={foldersOpen} onOpenChange={setFoldersOpen}>
            <CollapsibleTrigger asChild>
              <Button variant="ghost" className="w-full justify-between">
                <span className="text-sm font-medium text-muted-foreground">Watched Folders</span>
                <div className="flex items-center gap-2">
                  {foldersLoading && <Loader2 className="h-3 w-3 animate-spin" />}
                  {foldersOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                </div>
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <div className="space-y-1 pt-1">
                {foldersLoading ? (
                  <div className="text-sm text-muted-foreground px-3 py-2">Loading folders...</div>
                ) : watchedFolders.length === 0 ? (
                  <div className="text-sm text-muted-foreground px-3 py-2">No folders watched</div>
                ) : (
                  watchedFolders.map((folder: { path: string; id: string }) => (
                    <Button
                      key={folder.id}
                      variant="ghost"
                      className="w-full justify-start gap-2 text-sm"
                    >
                      <Folder className="h-4 w-4 flex-shrink-0" />
                      <span className="truncate">{folder.path}</span>
                    </Button>
                  ))
                )}
              </div>
            </CollapsibleContent>
          </Collapsible>
        </div>
      </ScrollArea>

      {/* Footer */}
      <div className="border-t p-3">
        <Link to="/settings">
          <Button
            variant={location.pathname === '/settings' ? 'secondary' : 'ghost'}
            className="w-full justify-start gap-2"
          >
            <Settings className="h-4 w-4" />
            Settings
          </Button>
        </Link>
      </div>
    </div>
  )
}
