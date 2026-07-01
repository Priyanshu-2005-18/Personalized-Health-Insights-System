import { useState, useRef, useEffect } from 'react'
import { cn } from '../../utils'

interface TooltipProps {
  content:   React.ReactNode
  children:  React.ReactElement
  placement?: 'top' | 'bottom' | 'left' | 'right'
  delay?:    number
  className?: string
}

const placementClasses = {
  top:    'bottom-full left-1/2 -translate-x-1/2 mb-2',
  bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
  left:   'right-full top-1/2 -translate-y-1/2 mr-2',
  right:  'left-full top-1/2 -translate-y-1/2 ml-2',
}

const arrowClasses = {
  top:    'top-full left-1/2 -translate-x-1/2 border-t-health-slate border-l-transparent border-r-transparent border-b-transparent',
  bottom: 'bottom-full left-1/2 -translate-x-1/2 border-b-health-slate border-l-transparent border-r-transparent border-t-transparent',
  left:   'left-full top-1/2 -translate-y-1/2 border-l-health-slate border-t-transparent border-b-transparent border-r-transparent',
  right:  'right-full top-1/2 -translate-y-1/2 border-r-health-slate border-t-transparent border-b-transparent border-l-transparent',
}

export function Tooltip({
  content,
  children,
  placement = 'top',
  delay = 300,
  className,
}: TooltipProps) {
  const [visible, setVisible] = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const show = () => {
    timerRef.current = setTimeout(() => setVisible(true), delay)
  }
  const hide = () => {
    if (timerRef.current) clearTimeout(timerRef.current)
    setVisible(false)
  }

  useEffect(() => () => { if (timerRef.current) clearTimeout(timerRef.current) }, [])

  return (
    <span
      className="relative inline-flex"
      onMouseEnter={show}
      onMouseLeave={hide}
      onFocus={show}
      onBlur={hide}
    >
      {children}
      {visible && (
        <span
          role="tooltip"
          className={cn(
            'absolute z-50 pointer-events-none',
            placementClasses[placement]
          )}
        >
          <span
            className={cn(
              'block whitespace-nowrap bg-health-slate text-white text-xs',
              'font-medium px-2.5 py-1.5 rounded-lg shadow-lg',
              className
            )}
          >
            {content}
          </span>
          {/* Arrow */}
          <span
            className={cn(
              'absolute w-0 h-0 border-4',
              arrowClasses[placement]
            )}
          />
        </span>
      )}
    </span>
  )
}
