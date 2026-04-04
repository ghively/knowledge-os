import { useCallback, useEffect, useMemo, useState } from 'react'
import { createEditor, Descendant, Transforms, Editor, Element as SlateElement, BaseEditor, Text, Range, NodeEntry, Node } from 'slate'
import { Slate, Editable, withReact, ReactEditor, RenderLeafProps } from 'slate-react'
import { withHistory } from 'slate-history'
import {
  Plus,
  CheckSquare,
  Type,
  Heading1,
  List,
  Quote,
  Code,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'

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
  linkType?: 'wiki' | 'block'
  linkValue?: string
}

type DecoratedRange = Range & {
  linkType?: 'wiki' | 'block'
  linkValue?: string
}

declare module 'slate' {
  interface CustomTypes {
    Editor: BaseEditor & ReactEditor
    Element: CustomElement
    Text: CustomText
  }
}

const SLASH_COMMANDS: Record<string, BlockType> = {
  text: 'paragraph',
  p: 'paragraph',
  heading: 'heading',
  h1: 'heading',
  todo: 'todo',
  task: 'todo',
  bullet: 'bullet',
  list: 'bullet',
  numbered: 'numbered',
  quote: 'quote',
  code: 'code',
}

const createBlockId = () => {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  return `block-${Math.random().toString(36).slice(2, 11)}`
}

const createEmptyBlock = (type: BlockType = 'paragraph', level: number = 0): BlockElement => ({
  id: createBlockId(),
  type,
  level,
  children: [{ text: '' }],
})

const renderElement = (props: { attributes: React.HTMLAttributes<HTMLElement>; children: React.ReactNode; element: CustomElement }) => {
  const { attributes, children, element } = props
  const { type, level = 0, checked } = element

  const baseClasses = cn(
    'py-1 px-2 -mx-2 rounded hover:bg-muted/30 transition-colors',
    level > 0 && 'ml-4'
  )

  switch (type) {
    case 'heading':
      return <h2 {...attributes} className={cn(baseClasses, 'mt-2 text-xl font-semibold')}>{children}</h2>
    case 'todo':
      return (
        <div {...attributes} className={cn(baseClasses, 'flex items-start gap-2')}>
          <input type="checkbox" checked={checked} className="mt-1.5 h-4 w-4 rounded border-gray-300" readOnly />
          <span className={cn(checked && 'line-through text-muted-foreground')}>{children}</span>
        </div>
      )
    case 'bullet':
      return <ul {...attributes} className={cn(baseClasses, 'ml-6 list-disc')}><li>{children}</li></ul>
    case 'numbered':
      return <ol {...attributes} className={cn(baseClasses, 'ml-6 list-decimal')}><li>{children}</li></ol>
    case 'quote':
      return <blockquote {...attributes} className={cn(baseClasses, 'border-l-4 border-muted-foreground/30 pl-4 italic')}>{children}</blockquote>
    case 'code':
      return <pre {...attributes} className={cn(baseClasses, 'rounded bg-muted p-2 font-mono text-sm')}><code>{children}</code></pre>
    default:
      return <p {...attributes} className={baseClasses}>{children}</p>
  }
}

const renderLeaf = (
  props: RenderLeafProps & { leaf: CustomText },
  onLinkClick?: (type: 'wiki' | 'block', value: string) => void
) => {
  let { children } = props

  if (props.leaf.bold) children = <strong>{children}</strong>
  if (props.leaf.italic) children = <em>{children}</em>
  if (props.leaf.code) children = <code className="rounded bg-muted px-1">{children}</code>
  if (props.leaf.linkType && props.leaf.linkValue) {
    children = (
      <button
        type="button"
        className={cn(
          'rounded px-1 underline decoration-dotted underline-offset-4',
          props.leaf.linkType === 'wiki' ? 'bg-sky-100 text-sky-800' : 'bg-amber-100 text-amber-800'
        )}
        contentEditable={false}
        onMouseDown={(event) => {
          event.preventDefault()
          onLinkClick?.(props.leaf.linkType!, props.leaf.linkValue!)
        }}
      >
        {children}
      </button>
    )
  }

  return <span {...props.attributes}>{children}</span>
}

const Toolbar = ({ editor }: { editor: Editor }) => {
  const toggleBlock = (type: BlockType) => {
    const isActive = isBlockActive(editor, type)
    Transforms.setNodes(
      editor,
      { type: isActive ? 'paragraph' : type },
      { match: (node) => SlateElement.isElement(node) && Editor.isBlock(editor, node) }
    )
  }

  const isBlockActive = (currentEditor: Editor, type: string) => {
    const [match] = Editor.nodes(currentEditor, {
      match: (node) => SlateElement.isElement(node) && node.type === type,
    })
    return !!match
  }

  return (
    <div className="flex items-center gap-1 border-b bg-muted/50 p-2">
      <Button variant="ghost" size="sm" onClick={() => toggleBlock('paragraph')} className={cn(isBlockActive(editor, 'paragraph') && 'bg-muted')}>
        <Type className="h-4 w-4" />
      </Button>
      <Button variant="ghost" size="sm" onClick={() => toggleBlock('heading')} className={cn(isBlockActive(editor, 'heading') && 'bg-muted')}>
        <Heading1 className="h-4 w-4" />
      </Button>
      <Button variant="ghost" size="sm" onClick={() => toggleBlock('todo')} className={cn(isBlockActive(editor, 'todo') && 'bg-muted')}>
        <CheckSquare className="h-4 w-4" />
      </Button>
      <Button variant="ghost" size="sm" onClick={() => toggleBlock('bullet')} className={cn(isBlockActive(editor, 'bullet') && 'bg-muted')}>
        <List className="h-4 w-4" />
      </Button>
      <Button variant="ghost" size="sm" onClick={() => toggleBlock('quote')} className={cn(isBlockActive(editor, 'quote') && 'bg-muted')}>
        <Quote className="h-4 w-4" />
      </Button>
      <Button variant="ghost" size="sm" onClick={() => toggleBlock('code')} className={cn(isBlockActive(editor, 'code') && 'bg-muted')}>
        <Code className="h-4 w-4" />
      </Button>
    </div>
  )
}

export function OutlinerEditor({
  objectId,
  initialBlocks = [],
  onChange,
  readOnly = false,
}: OutlinerEditorProps) {
  const navigate = useNavigate()
  const editor = useMemo(() => withHistory(withReact(createEditor())), [])
  const initialSignature = useMemo(() => JSON.stringify(initialBlocks), [initialBlocks])
  const [value, setValue] = useState<Descendant[]>(() => {
    if (initialBlocks.length === 0) {
      return [createEmptyBlock()]
    }
    return initialBlocks.map((block) => ({
      id: block.id,
      type: block.type,
      level: block.level || 0,
      checked: block.checked,
      children: block.children,
    }))
  })

  useEffect(() => {
    if (initialBlocks.length === 0) {
      setValue([createEmptyBlock()])
      return
    }
    setValue(initialBlocks.map((block) => ({
      id: block.id,
      type: block.type,
      level: block.level || 0,
      checked: block.checked,
      children: block.children,
    })))
  }, [initialBlocks, initialSignature])

  const handleLinkClick = useCallback((type: 'wiki' | 'block', linkValue: string) => {
    if (type === 'block') {
      navigate(`/object/${objectId}?block=${encodeURIComponent(linkValue)}`)
      return
    }
    navigate(`/search?q=${encodeURIComponent(linkValue)}`)
  }, [navigate, objectId])

  const decorate = useCallback(([node, path]: NodeEntry<Node>) => {
    const ranges: DecoratedRange[] = []
    if (!Text.isText(node)) {
      return ranges
    }

    const patterns: Array<{ regex: RegExp; type: 'wiki' | 'block' }> = [
      { regex: /\[\[([^[\]]+)\]\]/g, type: 'wiki' },
      { regex: /\(\(([a-zA-Z0-9-]+)\)\)/g, type: 'block' },
    ]

    for (const pattern of patterns) {
      for (const match of node.text.matchAll(pattern.regex)) {
        if (match.index === undefined) {
          continue
        }
        ranges.push({
          anchor: { path, offset: match.index },
          focus: { path, offset: match.index + match[0].length },
          linkType: pattern.type,
          linkValue: match[1],
        })
      }
    }

    return ranges
  }, [])

  const onKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (readOnly) return

    if (event.key === ' ') {
      const [match] = Editor.nodes(editor, {
        match: (node) => SlateElement.isElement(node) && Editor.isBlock(editor, node),
        mode: 'lowest',
      })
      if (match) {
        const [, path] = match
        const text = Editor.string(editor, path).trim()
        const nextType = text.startsWith('/') ? SLASH_COMMANDS[text.slice(1).toLowerCase()] : undefined
        if (nextType) {
          event.preventDefault()
          Transforms.setNodes(editor, { type: nextType }, { at: path })
          Transforms.delete(editor, {
            at: {
              anchor: { path: path.concat(0), offset: 0 },
              focus: { path: path.concat(0), offset: text.length },
            },
          })
          return
        }
      }
    }

    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      const [match] = Editor.nodes(editor, {
        match: (node) => SlateElement.isElement(node) && Editor.isBlock(editor, node),
        mode: 'lowest',
      })
      if (match) {
        const [node, path] = match
        const currentType = (node as CustomElement).type
        const currentLevel = (node as CustomElement).level || 0
        Transforms.insertNodes(
          editor,
          createEmptyBlock(currentType === 'heading' ? 'paragraph' : currentType, currentLevel),
          { at: Editor.after(editor, path) }
        )
      }
    }

    if (event.key === 'Tab' && !event.shiftKey) {
      event.preventDefault()
      const [match] = Editor.nodes(editor, {
        match: (node) => SlateElement.isElement(node) && Editor.isBlock(editor, node),
      })
      if (match) {
        const [node, path] = match
        const currentLevel = (node as CustomElement).level || 0
        Transforms.setNodes(editor, { level: Math.min(currentLevel + 1, 6) }, { at: path })
      }
    }

    if (event.key === 'Tab' && event.shiftKey) {
      event.preventDefault()
      const [match] = Editor.nodes(editor, {
        match: (node) => SlateElement.isElement(node) && Editor.isBlock(editor, node),
      })
      if (match) {
        const [node, path] = match
        const currentLevel = (node as CustomElement).level || 0
        Transforms.setNodes(editor, { level: Math.max(currentLevel - 1, 0) }, { at: path })
      }
    }

    if (event.key === 'Backspace') {
      const { selection } = editor
      if (selection && Editor.isStart(editor, selection.anchor, selection.anchor.path)) {
        const [match] = Editor.nodes(editor, {
          match: (node) => SlateElement.isElement(node) && Editor.isBlock(editor, node),
        })
        if (match) {
          const text = Editor.string(editor, match[1])
          if (text === '' && value.length > 1) {
            event.preventDefault()
            Transforms.removeNodes(editor, { at: match[1] })
          }
        }
      }
    }
  }, [editor, readOnly, value.length])

  const handleChange = useCallback((newValue: Descendant[]) => {
    setValue(newValue)

    const blocks = newValue.map((node) => ({
      id: (node as CustomElement).id || createBlockId(),
      type: (node as CustomElement).type,
      level: (node as CustomElement).level || 0,
      checked: (node as CustomElement).checked,
      content: (node as CustomElement).children.map((child) => child.text).join(''),
      children: (node as CustomElement).children,
    })) as BlockElement[]

    onChange?.(blocks)
  }, [onChange])

  const addBlock = useCallback(() => {
    if (readOnly) return
    void objectId

    const lastBlock = value[value.length - 1] as CustomElement
    const newBlock = createEmptyBlock('paragraph', lastBlock?.level || 0)
    Transforms.insertNodes(editor, newBlock as Descendant, { at: [value.length] })
  }, [editor, objectId, readOnly, value.length])

  return (
    <div className="outliner-editor">
      {!readOnly && <Toolbar editor={editor} />}
      <div className="py-4">
        <Slate editor={editor} initialValue={value} onChange={handleChange}>
          <Editable
            renderElement={renderElement}
            renderLeaf={(props) => renderLeaf(props, handleLinkClick)}
            decorate={decorate}
            onKeyDown={onKeyDown}
            placeholder="Type something... Use /todo, /heading, [[Wiki Links]], or ((block-id))"
            readOnly={readOnly}
            className="min-h-[200px] outline-none"
          />
        </Slate>

        {!readOnly && (
          <Button variant="ghost" className="mt-2 w-full justify-start gap-2 text-muted-foreground" onClick={addBlock}>
            <Plus className="h-4 w-4" />
            Add a block
          </Button>
        )}
      </div>
    </div>
  )
}

export default OutlinerEditor
