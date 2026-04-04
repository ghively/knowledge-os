import { useCallback, useMemo, useState } from 'react'
import { createEditor, Descendant, Transforms, Editor, Element as SlateElement, BaseEditor } from 'slate'
import { Slate, Editable, withReact, ReactEditor } from 'slate-react'
import { withHistory } from 'slate-history'
import { 
  Plus, 
  CheckSquare, 
  Type, 
  Heading1, 
  List,
  Quote,
  Code
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'

// Types
type BlockType = 'paragraph' | 'heading' | 'todo' | 'bullet' | 'numbered' | 'quote' | 'code'

export interface BlockElement {
  id: string
  type: BlockType
  level?: number
  checked?: boolean
  content?: string
  children: { text: string }[]
}

interface OutlinerEditorProps {
  objectId: string
  initialBlocks?: BlockElement[]
  onChange?: (blocks: BlockElement[]) => void
  readOnly?: boolean
}

// Custom Element type
type CustomElement = {
  id: string
  type: BlockType
  level?: number
  checked?: boolean
  children: CustomText[]
}

type CustomText = {
  text: string
  bold?: boolean
  italic?: boolean
  code?: boolean
}

declare module 'slate' {
  interface CustomTypes {
    Editor: BaseEditor & ReactEditor
    Element: CustomElement
    Text: CustomText
  }
}

// Empty block factory
const createEmptyBlock = (type: BlockType = 'paragraph', level: number = 0): BlockElement => ({
  id: Math.random().toString(36).substr(2, 9),
  type,
  level,
  children: [{ text: '' }],
})

// Render element based on type
const renderElement = (props: { attributes: any; children: any; element: CustomElement }) => {
  const { attributes, children, element } = props
  const { type, level = 0, checked } = element

  const baseClasses = cn(
    'py-1 px-2 -mx-2 rounded hover:bg-muted/30 transition-colors',
    level > 0 && 'ml-4'
  )

  switch (type) {
    case 'heading':
      return (
        <h2 
          {...attributes} 
          className={cn(baseClasses, 'text-xl font-semibold mt-2')}
        >
          {children}
        </h2>
      )
    case 'todo':
      return (
        <div {...attributes} className={cn(baseClasses, 'flex items-start gap-2')}>
          <input 
            type="checkbox" 
            checked={checked}
            className="mt-1.5 h-4 w-4 rounded border-gray-300"
            readOnly
          />
          <span className={cn(checked && 'line-through text-muted-foreground')}>
            {children}
          </span>
        </div>
      )
    case 'bullet':
      return (
        <ul {...attributes} className={cn(baseClasses, 'list-disc ml-6')}>
          <li>{children}</li>
        </ul>
      )
    case 'numbered':
      return (
        <ol {...attributes} className={cn(baseClasses, 'list-decimal ml-6')}>
          <li>{children}</li>
        </ol>
      )
    case 'quote':
      return (
        <blockquote 
          {...attributes} 
          className={cn(baseClasses, 'border-l-4 border-muted-foreground/30 pl-4 italic')}
        >
          {children}
        </blockquote>
      )
    case 'code':
      return (
        <pre {...attributes} className={cn(baseClasses, 'bg-muted p-2 rounded font-mono text-sm')}>
          <code>{children}</code>
        </pre>
      )
    default:
      return (
        <p {...attributes} className={baseClasses}>
          {children}
        </p>
      )
  }
}

// Render leaf (text formatting)
const renderLeaf = (props: { attributes: any; children: any; leaf: CustomText }) => {
  let { children } = props
  
  if (props.leaf.bold) {
    children = <strong>{children}</strong>
  }
  if (props.leaf.italic) {
    children = <em>{children}</em>
  }
  if (props.leaf.code) {
    children = <code className="bg-muted px-1 rounded">{children}</code>
  }
  
  return <span {...props.attributes}>{children}</span>
}

// Toolbar component
const Toolbar = ({ editor }: { editor: Editor }) => {
  const toggleBlock = (type: BlockType) => {
    const isActive = isBlockActive(editor, type)
    
    Transforms.setNodes(
      editor,
      { type: isActive ? 'paragraph' : type },
      { match: (n) => SlateElement.isElement(n) && Editor.isBlock(editor, n) }
    )
  }

  const isBlockActive = (editor: Editor, type: string) => {
    const [match] = Editor.nodes(editor, {
      match: (n) => SlateElement.isElement(n) && n.type === type,
    })
    return !!match
  }

  return (
    <div className="flex items-center gap-1 p-2 border-b bg-muted/50">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => toggleBlock('paragraph')}
        className={cn(isBlockActive(editor, 'paragraph') && 'bg-muted')}
      >
        <Type className="h-4 w-4" />
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => toggleBlock('heading')}
        className={cn(isBlockActive(editor, 'heading') && 'bg-muted')}
      >
        <Heading1 className="h-4 w-4" />
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => toggleBlock('todo')}
        className={cn(isBlockActive(editor, 'todo') && 'bg-muted')}
      >
        <CheckSquare className="h-4 w-4" />
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => toggleBlock('bullet')}
        className={cn(isBlockActive(editor, 'bullet') && 'bg-muted')}
      >
        <List className="h-4 w-4" />
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => toggleBlock('quote')}
        className={cn(isBlockActive(editor, 'quote') && 'bg-muted')}
      >
        <Quote className="h-4 w-4" />
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => toggleBlock('code')}
        className={cn(isBlockActive(editor, 'code') && 'bg-muted')}
      >
        <Code className="h-4 w-4" />
      </Button>
    </div>
  )
}

// Main Editor Component
export function OutlinerEditor({ 
  objectId, 
  initialBlocks = [], 
  onChange,
  readOnly = false 
}: OutlinerEditorProps) {
  const editor = useMemo(() => withHistory(withReact(createEditor())), [])
  
  // Convert initial blocks to Slate format
  const [value, setValue] = useState<Descendant[]>(() => {
    if (initialBlocks.length === 0) {
      return [createEmptyBlock()]
    }
    return initialBlocks.map(b => ({
      id: b.id,
      type: b.type,
      level: b.level || 0,
      checked: b.checked,
      children: b.children,
    }))
  })

  // Handle key commands
  const onKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (readOnly) return

    // Enter creates new block
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      
      const [match] = Editor.nodes(editor, {
        match: (n) => SlateElement.isElement(n) && Editor.isBlock(editor, n),
        mode: 'lowest',
      })
      
      if (match) {
        const [node, path] = match
        const currentType = (node as CustomElement).type
        const currentLevel = (node as CustomElement).level || 0
        
        // Insert new block after current
        Transforms.insertNodes(
          editor,
          createEmptyBlock(currentType === 'heading' ? 'paragraph' : currentType, currentLevel),
          { at: Editor.after(editor, path) }
        )
      }
    }

    // Tab increases indent
    if (event.key === 'Tab' && !event.shiftKey) {
      event.preventDefault()
      const [match] = Editor.nodes(editor, {
        match: (n) => SlateElement.isElement(n) && Editor.isBlock(editor, n),
      })
      if (match) {
        const [node, path] = match
        const currentLevel = (node as CustomElement).level || 0
        Transforms.setNodes(editor, { level: Math.min(currentLevel + 1, 6) }, { at: path })
      }
    }

    // Shift+Tab decreases indent
    if (event.key === 'Tab' && event.shiftKey) {
      event.preventDefault()
      const [match] = Editor.nodes(editor, {
        match: (n) => SlateElement.isElement(n) && Editor.isBlock(editor, n),
      })
      if (match) {
        const [node, path] = match
        const currentLevel = (node as CustomElement).level || 0
        Transforms.setNodes(editor, { level: Math.max(currentLevel - 1, 0) }, { at: path })
      }
    }

    // Backspace on empty block removes it
    if (event.key === 'Backspace') {
      const { selection } = editor
      if (selection && Editor.isStart(editor, selection.anchor, selection.anchor.path)) {
        const [match] = Editor.nodes(editor, {
          match: (n) => SlateElement.isElement(n) && Editor.isBlock(editor, n),
        })
        if (match) {
          const [node] = match
          const text = Editor.string(editor, match[1])
          if (text === '' && value.length > 1) {
            event.preventDefault()
            Transforms.removeNodes(editor, { at: match[1] })
          }
        }
      }
    }
  }, [editor, readOnly, value.length])

  // Handle changes
  const handleChange = useCallback((newValue: Descendant[]) => {
    setValue(newValue)
    
    // Convert back to BlockElement format
    const blocks = newValue.map((node) => ({
      id: (node as CustomElement).id || Math.random().toString(36).substr(2, 9),
      type: (node as CustomElement).type,
      level: (node as CustomElement).level || 0,
      checked: (node as CustomElement).checked,
      content: (node as CustomElement).children.map((child) => child.text).join(''),
      children: (node as CustomElement).children,
    })) as BlockElement[]
    
    onChange?.(blocks)
  }, [onChange])

  // Add new block at end
  const addBlock = useCallback(() => {
    if (readOnly) return
    void objectId
    
    const lastBlock = value[value.length - 1] as CustomElement
    const newBlock = createEmptyBlock('paragraph', lastBlock?.level || 0)
    
    Transforms.insertNodes(editor, newBlock as Descendant, {
      at: [value.length],
    })
  }, [editor, readOnly, value.length])

  return (
    <div className="outliner-editor">
      {!readOnly && <Toolbar editor={editor} />}
      
      <div className="py-4">
        <Slate editor={editor} initialValue={value} onChange={handleChange}>
          <Editable
            renderElement={renderElement}
            renderLeaf={renderLeaf}
            onKeyDown={onKeyDown}
            placeholder="Type something..."
            readOnly={readOnly}
            className="outline-none min-h-[200px]"
          />
        </Slate>
        
        {!readOnly && (
          <Button
            variant="ghost"
            className="w-full justify-start gap-2 text-muted-foreground mt-2"
            onClick={addBlock}
          >
            <Plus className="h-4 w-4" />
            Add a block
          </Button>
        )}
      </div>
    </div>
  )
}

export default OutlinerEditor
