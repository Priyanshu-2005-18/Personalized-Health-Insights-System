import { useEffect, useRef } from 'react'
import { X } from 'lucide-react'
import { cn } from '../../utils'

interface ModalProps {
  open:        boolean
  onClose:     () => void
  title?:      string
  description?: string
  children:    React.ReactNode
  size?:       'sm' | 'md' | 'lg' | 'xl'
  footer?:     React.ReactNode
  closeOnBackdrop?: boolean
}

const sizeMap = {
  sm:  'max-w-sm',
  md:  'max-w-md',
  lg:  'max-w-lg',
  xl:  'max-w-2xl',
}

export function Modal({
  open,
  onClose,
  title,
  description,
  children,
  size = 'md',
  footer,
  closeOnBackdrop = true,
}: ModalProps) {
  const dialogRef = useRef<HTMLDivElement>(null)

  // Close on Escape
  useEffect(() => {
    if (!open) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [open, onClose])

  // Lock body scroll while open
  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => { document.body.style.overflow = '' }
  }, [open])

  // Focus first focusable element on open
  useEffect(() => {
    if (open && dialogRef.current) {
      const focusable = dialogRef.current.querySelector<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      )
      focusable?.focus()
    }
  }, [open])

  if (!open) return null

  return (
    /* Backdrop */
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      aria-modal="true"
      role="dialog"
      aria-labelledby={title ? 'modal-title' : undefined}
    >
      {/* Dim layer */}
      <div
        className="absolute inset-0 bg-health-slate/40 backdrop-blur-sm"
        onClick={closeOnBackdrop ? onClose : undefined}
      />

      {/* Panel */}
      <div
        ref={dialogRef}
        className={cn(
          'relative w-full bg-white rounded-2xl shadow-2xl animate-fade-up',
          'flex flex-col max-h-[90vh]',
          sizeMap[size]
        )}
      >
        {/* Header */}
        {(title || description) && (
          <div className="flex items-start justify-between gap-4 px-6 pt-6 pb-4 border-b border-health-border shrink-0">
            <div>
              {title && (
                <h2
                  id="modal-title"
                  className="text-base font-semibold text-health-slate"
                >
                  {title}
                </h2>
              )}
              {description && (
                <p className="text-sm text-health-muted mt-0.5">{description}</p>
              )}
            </div>
            <button
              onClick={onClose}
              className="shrink-0 p-1.5 rounded-lg text-health-muted hover:text-health-slate hover:bg-health-surface transition-all"
              aria-label="Close modal"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-5">
          {children}
        </div>

        {/* Footer */}
        {footer && (
          <div className="px-6 py-4 border-t border-health-border shrink-0 flex items-center justify-end gap-3">
            {footer}
          </div>
        )}
      </div>
    </div>
  )
}
