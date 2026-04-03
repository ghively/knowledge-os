import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Search, FileText, CheckSquare, Folder, Bot, Image, Code, Loader2 } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { searchApi } from '@/services/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { cn } from '@/lib/utils'

interface SearchResult {
  id: string
  type: 'object' | 'block' | 'file' | 'image' | 'code'
  title: string
  content: string
  score: number
  metadata: {
    object_type?: string
    block_type?: string
    file_path?: string
    agent_name?: string
    tags?: string[]
  }
}

const typeIcons = {
  object: FileText,
  block: FileText,
  file: Folder,
  image: Image,
  code: Code,
}

const typeColors = {
  object: 'text-blue-500',
  block: 'text-gray-500',
  file: 'text-yellow-500',
  image: 'text-purple-500',
  code: 'text-green-500',
}

export function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const initialQuery = searchParams.get('q') || ''
  const [query, setQuery] = useState(initialQuery)
  const [activeQuery, setActiveQuery] = useState(initialQuery)
  const [searchType, setSearchType] = useState<'semantic' | 'exact'>('semantic')

  const { data: results = [], isLoading, error } = useQuery({
    queryKey: ['search', activeQuery, searchType],
    queryFn: () => activeQuery ? searchApi.search(activeQuery, searchType) : Promise.resolve([]),
    enabled: !!activeQuery,
  })

  useEffect(() => {
    if (initialQuery) {
      setQuery(initialQuery)
      setActiveQuery(initialQuery)
    }
  }, [initialQuery])

  const handleSearch = () => {
    if (query.trim()) {
      setActiveQuery(query)
      setSearchParams({ q: query })
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  const handleResultClick = (result: SearchResult) => {
    // Navigate based on result type
    switch (result.type) {
      case 'object':
      case 'block':
        window.location.href = `/object/${result.id}`
        break
      case 'file':
        window.location.href = `/files?file=${result.id}`
        break
      default:
        break
    }
  }

  return (
    <div className="h-full flex flex-col">
      {/* Search Header */}
      <div className="border-b p-4 bg-card">
        <div className="max-w-3xl mx-auto">
          <h1 className="text-2xl font-bold mb-4">Search</h1>
          
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Search across all your knowledge..."
                className="pl-10"
              />
            </div>
            <Button 
              onClick={handleSearch}
              disabled={isLoading || !query.trim()}
            >
              {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Search'}
            </Button>
          </div>

          {/* Search Type Toggle */}
          <div className="flex gap-2 mt-3">
            <Button
              variant={searchType === 'semantic' ? 'secondary' : 'ghost'}
              size="sm"
              onClick={() => setSearchType('semantic')}
            >
              Semantic Search
            </Button>
            <Button
              variant={searchType === 'exact' ? 'secondary' : 'ghost'}
              size="sm"
              onClick={() => setSearchType('exact')}
            >
              Exact Match
            </Button>
          </div>
        </div>
      </div>

      {/* Results */}
      <ScrollArea className="flex-1">
        <div className="max-w-3xl mx-auto p-4">
          {!activeQuery ? (
            <div className="text-center py-12 text-muted-foreground">
              <Search className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium">Start searching</p>
              <p className="text-sm">Type a query above to search across your knowledge base</p>
            </div>
          ) : isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : error ? (
            <div className="text-center py-12 text-red-500">
              <p>Error searching. Please try again.</p>
            </div>
          ) : results.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <p className="text-lg font-medium">No results found</p>
              <p className="text-sm">Try a different search term or check your spelling</p>
            </div>
          ) : (
            <div className="space-y-3">
              <p className="text-sm text-muted-foreground mb-4">
                Found {results.length} result{results.length !== 1 ? 's' : ''}
              </p>
              
              {results.map((result: SearchResult) => {
                const Icon = typeIcons[result.type] || FileText
                return (
                  <div
                    key={result.id}
                    onClick={() => handleResultClick(result)}
                    className="p-4 border rounded-lg hover:bg-muted cursor-pointer transition-colors"
                  >
                    <div className="flex items-start gap-3">
                      <Icon className={cn("h-5 w-5 mt-0.5 flex-shrink-0", typeColors[result.type])} />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <h3 className="font-medium truncate">{result.title}</h3>
                          <span className="text-xs text-muted-foreground">
                            {Math.round(result.score * 100)}% match
                          </span>
                        </div>
                        <p className="text-sm text-muted-foreground line-clamp-2 mt-1">
                          {result.content}
                        </p>
                        <div className="flex items-center gap-2 mt-2">
                          <span className="text-xs px-2 py-0.5 bg-muted rounded-full capitalize">
                            {result.type}
                          </span>
                          {result.metadata.object_type && (
                            <span className="text-xs px-2 py-0.5 bg-muted rounded-full">
                              {result.metadata.object_type}
                            </span>
                          )}
                          {result.metadata.tags?.map((tag) => (
                            <span key={tag} className="text-xs px-2 py-0.5 bg-primary/10 text-primary rounded-full">
                              #{tag}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  )
}
