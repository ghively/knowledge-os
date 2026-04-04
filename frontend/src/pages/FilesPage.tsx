import { useState } from 'react'
import { Folder, File, Search, Plus, RefreshCw, Loader2, FileText, Image, Code } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { filesApi, settingsApi } from '@/services/api'
import { cn } from '@/lib/utils'

interface FileItem {
  id: string
  name: string
  type: 'file' | 'folder'
  path: string
  size?: number
  modified: string
  content_type?: string
  indexed?: boolean
  indexed_at?: string
}

const fileTypeIcons: Record<string, React.ElementType> = {
  'text/plain': FileText,
  'text/markdown': FileText,
  'application/pdf': FileText,
  'image/png': Image,
  'image/jpeg': Image,
  'text/x-python': Code,
  'text/javascript': Code,
  'text/typescript': Code,
  'default': File,
}

const fileTypeColors: Record<string, string> = {
  'text/plain': 'text-blue-500',
  'text/markdown': 'text-blue-500',
  'application/pdf': 'text-red-500',
  'image/png': 'text-purple-500',
  'image/jpeg': 'text-purple-500',
  'text/x-python': 'text-green-500',
  'text/javascript': 'text-yellow-500',
  'text/typescript': 'text-blue-500',
  'default': 'text-gray-500',
}

function formatFileSize(bytes?: number): string {
  if (!bytes) return ''
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`
}

function getFileIcon(contentType?: string) {
  return fileTypeIcons[contentType || 'default'] || fileTypeIcons.default
}

function getFileColor(contentType?: string) {
  return fileTypeColors[contentType || 'default'] || fileTypeColors.default
}

export function FilesPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [addFolderOpen, setAddFolderOpen] = useState(false)
  const [newFolderPath, setNewFolderPath] = useState('')
  const [selectedFile, setSelectedFile] = useState<FileItem | null>(null)
  const queryClient = useQueryClient()

  // Fetch files
  const { data: filesData, isLoading, error } = useQuery({
    queryKey: ['files'],
    queryFn: filesApi.list,
    refetchInterval: 30000, // Poll every 30 seconds
  })
  const files = (filesData?.files ?? []) as FileItem[]

  // Add folder mutation
  const addFolderMutation = useMutation({
    mutationFn: (path: string) => settingsApi.addWatchedFolder(path),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watched-folders'] })
      queryClient.invalidateQueries({ queryKey: ['files'] })
      setAddFolderOpen(false)
      setNewFolderPath('')
    },
  })

  // Reindex file mutation
  const reindexMutation = useMutation({
    mutationFn: (fileId: string) => filesApi.reindex(fileId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['files'] })
    },
  })

  const filteredFiles = files.filter((file: FileItem) =>
    file.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    file.path.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const handleAddFolder = () => {
    if (newFolderPath.trim()) {
      addFolderMutation.mutate(newFolderPath.trim())
    }
  }

  const handleReindex = (fileId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    reindexMutation.mutate(fileId)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-red-500">
        <p>Error loading files</p>
        <Button variant="outline" onClick={() => queryClient.invalidateQueries({ queryKey: ['files'] })} className="mt-4">
          <RefreshCw className="h-4 w-4 mr-2" />
          Retry
        </Button>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="border-b p-4 bg-card">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Folder className="h-6 w-6" />
              Files
            </h1>
            <p className="text-muted-foreground mt-1">
              {files.length} item{files.length !== 1 ? 's' : ''} indexed
            </p>
          </div>
          <Button onClick={() => setAddFolderOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Add Folder
          </Button>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search files..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {/* File List */}
      <ScrollArea className="flex-1">
        <div className="p-4">
          {filteredFiles.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <Folder className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium">No files found</p>
              <p className="text-sm">Add folders to watch in settings</p>
            </div>
          ) : (
            <div className="space-y-1">
              {filteredFiles.map((file: FileItem) => {
                const Icon = getFileIcon(file.content_type)
                return (
                  <div
                    key={file.id}
                    className="flex items-center gap-3 p-3 hover:bg-muted rounded-lg cursor-pointer group"
                    onClick={() => setSelectedFile(file)}
                  >
                    <Icon className={cn("h-5 w-5", getFileColor(file.content_type))} />
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate">{file.name}</div>
                      <div className="text-sm text-muted-foreground truncate">{file.path}</div>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      {file.size !== undefined && (
                        <span className="hidden sm:inline">{formatFileSize(file.size)}</span>
                      )}
                      <span className="hidden md:inline">
                        {new Date(file.modified).toLocaleDateString()}
                      </span>
                      {file.indexed && (
                        <span className="text-xs px-2 py-0.5 bg-green-500/10 text-green-600 rounded-full">
                          Indexed
                        </span>
                      )}
                      <Button
                        variant="ghost"
                        size="icon"
                        className="opacity-0 group-hover:opacity-100 transition-opacity"
                        onClick={(e) => handleReindex(file.id, e)}
                        disabled={reindexMutation.isPending}
                      >
                        <RefreshCw className={cn("h-4 w-4", reindexMutation.isPending && "animate-spin")} />
                      </Button>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Add Folder Dialog */}
      <Dialog open={addFolderOpen} onOpenChange={setAddFolderOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Watched Folder</DialogTitle>
            <DialogDescription>
              Enter the path to a folder you want to watch for changes.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Input
              placeholder="~/Documents or /home/user/Documents"
              value={newFolderPath}
              onChange={(e) => setNewFolderPath(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAddFolder()}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAddFolderOpen(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleAddFolder}
              disabled={!newFolderPath.trim() || addFolderMutation.isPending}
            >
              {addFolderMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : (
                <Plus className="h-4 w-4 mr-2" />
              )}
              Add Folder
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* File Details Dialog */}
      <Dialog open={!!selectedFile} onOpenChange={() => setSelectedFile(null)}>
        <DialogContent className="max-w-2xl">
          {selectedFile && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  {(() => {
                    const Icon = getFileIcon(selectedFile.content_type)
                    return <Icon className={cn("h-5 w-5", getFileColor(selectedFile.content_type))} />
                  })()}
                  {selectedFile.name}
                </DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Path:</span>
                    <p className="font-mono mt-1">{selectedFile.path}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Type:</span>
                    <p className="mt-1 capitalize">{selectedFile.type}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Size:</span>
                    <p className="mt-1">{formatFileSize(selectedFile.size)}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Modified:</span>
                    <p className="mt-1">{new Date(selectedFile.modified).toLocaleString()}</p>
                  </div>
                  {selectedFile.content_type && (
                    <div>
                      <span className="text-muted-foreground">Content Type:</span>
                      <p className="mt-1">{selectedFile.content_type}</p>
                    </div>
                  )}
                  {selectedFile.indexed_at && (
                    <div>
                      <span className="text-muted-foreground">Indexed:</span>
                      <p className="mt-1">{new Date(selectedFile.indexed_at).toLocaleString()}</p>
                    </div>
                  )}
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setSelectedFile(null)}>
                  Close
                </Button>
                <Button 
                  onClick={() => selectedFile && reindexMutation.mutate(selectedFile.id)}
                  disabled={reindexMutation.isPending}
                >
                  {reindexMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  ) : (
                    <RefreshCw className="h-4 w-4 mr-2" />
                  )}
                  Reindex
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
