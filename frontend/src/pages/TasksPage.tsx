import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { CheckSquare, Plus, Filter, MoreHorizontal, User } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { TaskAssignmentDialog } from '@/components/tasks/TaskAssignmentDialog'
import { tasksApi, objectsApi } from '@/services/api'
import { cn } from '@/lib/utils'
import { useNavigate } from 'react-router-dom'

interface Task {
  id: string
  title: string
  type: string
  properties: {
    status: 'todo' | 'in-progress' | 'blocked' | 'review' | 'done'
    priority: 'low' | 'medium' | 'high' | 'urgent'
    assigned_to?: string
    due_date?: string
    current_action?: string
  }
}

const priorityColors = {
  urgent: 'border-l-red-500 bg-red-50/50',
  high: 'border-l-orange-500 bg-orange-50/50',
  medium: 'border-l-yellow-500 bg-yellow-50/50',
  low: 'border-l-green-500 bg-green-50/50',
}

const priorityBadges = {
  urgent: 'bg-red-100 text-red-700',
  high: 'bg-orange-100 text-orange-700',
  medium: 'bg-yellow-100 text-yellow-700',
  low: 'bg-green-100 text-green-700',
}

const statusLabels: Record<string, string> = {
  todo: 'To Do',
  'in-progress': 'In Progress',
  blocked: 'Blocked',
  review: 'In Review',
  done: 'Done',
}

const statusColors: Record<string, string> = {
  todo: 'text-gray-500',
  'in-progress': 'text-blue-500',
  blocked: 'text-red-500',
  review: 'text-yellow-500',
  done: 'text-green-500',
}

export function TasksPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [filter, setFilter] = useState<'all' | 'todo' | 'in-progress' | 'done'>('all')
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)
  const [assignmentDialogOpen, setAssignmentDialogOpen] = useState(false)

  // Fetch tasks (objects with type='task')
  const { data: tasksData, isLoading } = useQuery({
    queryKey: ['tasks', { filter }],
    queryFn: () => tasksApi.list({ status: filter === 'all' ? undefined : filter }),
  })

  const tasks: Task[] = tasksData?.tasks || []

  // Create task mutation
  const createTaskMutation = useMutation({
    mutationFn: objectsApi.create,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
      navigate(`/object/${data.id}`)
    },
  })

  const handleCreateTask = () => {
    createTaskMutation.mutate({
      type: 'task',
      title: 'New Task',
      content: '',
      properties: {
        status: 'todo',
        priority: 'medium',
      },
    })
  }

  const handleAssignClick = (task: Task) => {
    setSelectedTask(task)
    setAssignmentDialogOpen(true)
  }

  const filteredTasks = tasks

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto py-8 px-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-muted rounded w-1/4" />
          <div className="h-4 bg-muted rounded w-1/2" />
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-20 bg-muted rounded" />
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto py-8 px-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <CheckSquare className="h-6 w-6" />
            Tasks
          </h1>
          <p className="text-muted-foreground mt-1">
            {tasks.length} tasks • {tasks.filter((t) => t.properties?.status === 'done').length} completed
          </p>
        </div>
        <Button onClick={handleCreateTask} disabled={createTaskMutation.isPending}>
          <Plus className="h-4 w-4 mr-2" />
          {createTaskMutation.isPending ? 'Creating...' : 'New Task'}
        </Button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2 mb-6">
        <Button
          variant={filter === 'all' ? 'secondary' : 'ghost'}
          size="sm"
          onClick={() => setFilter('all')}
        >
          All
        </Button>
        <Button
          variant={filter === 'todo' ? 'secondary' : 'ghost'}
          size="sm"
          onClick={() => setFilter('todo')}
        >
          To Do
        </Button>
        <Button
          variant={filter === 'in-progress' ? 'secondary' : 'ghost'}
          size="sm"
          onClick={() => setFilter('in-progress')}
        >
          In Progress
        </Button>
        <Button
          variant={filter === 'done' ? 'secondary' : 'ghost'}
          size="sm"
          onClick={() => setFilter('done')}
        >
          Done
        </Button>
      </div>

      {/* Task List */}
      <div className="space-y-2">
        {filteredTasks.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            <CheckSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No tasks found</p>
            <p className="text-sm">Create your first task to get started</p>
          </div>
        ) : (
          filteredTasks.map((task) => (
            <div
              key={task.id}
              className={cn(
                'p-4 bg-card border rounded-lg border-l-4 hover:shadow-sm transition-shadow cursor-pointer',
                priorityColors[task.properties?.priority || 'medium']
              )}
              onClick={() => navigate(`/object/${task.id}`)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-medium">{task.title}</h3>
                    <span
                      className={cn(
                        'text-xs px-2 py-0.5 rounded-full font-medium',
                        priorityBadges[task.properties?.priority || 'medium']
                      )}
                    >
                      {task.properties?.priority}
                    </span>
                  </div>
                  
                  <div className="flex items-center gap-4 text-sm">
                    <span className={cn('font-medium', statusColors[task.properties?.status || 'todo'])}>
                      {statusLabels[task.properties?.status || 'todo']}
                    </span>
                    
                    {task.properties?.assigned_to && (
                      <span className="flex items-center gap-1 text-muted-foreground">
                        <User className="h-3 w-3" />
                        @{task.properties.assigned_to}
                      </span>
                    )}
                    
                    {task.properties?.current_action && (
                      <span className="text-blue-600">
                        ⏳ {task.properties.current_action}
                      </span>
                    )}
                    
                    {task.properties?.due_date && (
                      <span className="text-muted-foreground">
                        Due {new Date(task.properties.due_date).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </div>
                
                <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                  {!task.properties?.assigned_to && task.properties?.status !== 'done' && (
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={() => handleAssignClick(task)}
                    >
                      Assign
                    </Button>
                  )}
                  <Button variant="ghost" size="icon">
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Assignment Dialog */}
      {selectedTask && (
        <TaskAssignmentDialog
          taskId={selectedTask.id}
          taskTitle={selectedTask.title}
          open={assignmentDialogOpen}
          onOpenChange={(open) => {
            setAssignmentDialogOpen(open)
            if (!open) setSelectedTask(null)
          }}
        />
      )}
    </div>
  )
}
