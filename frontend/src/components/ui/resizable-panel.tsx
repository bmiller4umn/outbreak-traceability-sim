import { useState, useCallback, useRef, useEffect } from 'react'
import { GripVertical } from 'lucide-react'

interface ResizablePanelProps {
  children: React.ReactNode
  defaultWidth?: number
  minWidth?: number
  maxWidth?: number
  className?: string
}

export function ResizablePanel({
  children,
  defaultWidth = 384,
  minWidth = 300,
  maxWidth = 800,
  className = '',
}: ResizablePanelProps) {
  const [width, setWidth] = useState(defaultWidth)
  const [isResizing, setIsResizing] = useState(false)
  const panelRef = useRef<HTMLDivElement>(null)

  const startResizing = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    setIsResizing(true)
  }, [])

  const stopResizing = useCallback(() => {
    setIsResizing(false)
  }, [])

  const resize = useCallback(
    (e: MouseEvent) => {
      if (!isResizing || !panelRef.current) return

      const panelRect = panelRef.current.getBoundingClientRect()
      // Calculate new width based on mouse position from the right edge
      const newWidth = panelRect.right - e.clientX

      if (newWidth >= minWidth && newWidth <= maxWidth) {
        setWidth(newWidth)
      }
    },
    [isResizing, minWidth, maxWidth]
  )

  useEffect(() => {
    if (isResizing) {
      window.addEventListener('mousemove', resize)
      window.addEventListener('mouseup', stopResizing)
      // Add cursor style to body during resize
      document.body.style.cursor = 'col-resize'
      document.body.style.userSelect = 'none'
    }

    return () => {
      window.removeEventListener('mousemove', resize)
      window.removeEventListener('mouseup', stopResizing)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
  }, [isResizing, resize, stopResizing])

  return (
    <div
      ref={panelRef}
      className={`relative flex ${className}`}
      style={{ width: `${width}px` }}
    >
      {/* Resize Handle */}
      <div
        className={`absolute left-0 top-0 bottom-0 w-2 cursor-col-resize flex items-center justify-center
          hover:bg-primary/10 transition-colors z-10 group
          ${isResizing ? 'bg-primary/20' : ''}`}
        onMouseDown={startResizing}
      >
        <div className={`h-8 flex items-center justify-center rounded
          ${isResizing ? 'bg-primary/30' : 'bg-muted group-hover:bg-primary/20'} transition-colors`}>
          <GripVertical className="h-4 w-4 text-muted-foreground" />
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 pl-3 overflow-y-auto">
        {children}
      </div>
    </div>
  )
}
