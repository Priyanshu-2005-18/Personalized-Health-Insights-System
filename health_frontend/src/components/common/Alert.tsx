import React from 'react'
import { AlertCircle, CheckCircle2, Info, XCircle } from 'lucide-react'
import { cn } from '../../utils'

type AlertVariant = 'success' | 'error' | 'warning' | 'info'

interface AlertProps {
  variant: AlertVariant
  title?: string
  message: string
  className?: string
  onDismiss?: () => void
}

const config: Record<AlertVariant, { icon: React.ReactNode; classes: string }> = {
  success: {
    icon:    <CheckCircle2 className="h-4 w-4 text-teal-600" />,
    classes: 'bg-teal-50 border-teal-200 text-teal-800',
  },
  error: {
    icon:    <XCircle className="h-4 w-4 text-red-600" />,
    classes: 'bg-red-50 border-red-200 text-red-800',
  },
  warning: {
    icon:    <AlertCircle className="h-4 w-4 text-yellow-600" />,
    classes: 'bg-yellow-50 border-yellow-200 text-yellow-800',
  },
  info: {
    icon:    <Info className="h-4 w-4 text-blue-600" />,
    classes: 'bg-blue-50 border-blue-200 text-blue-800',
  },
}

export function Alert({ variant, title, message, className, onDismiss }: AlertProps) {
  const { icon, classes } = config[variant]
  return (
    <div className={cn('flex gap-3 items-start p-4 rounded-xl border text-sm', classes, className)}>
      <span className="shrink-0 mt-0.5">{icon}</span>
      <div className="flex-1 min-w-0">
        {title && <p className="font-semibold mb-0.5">{title}</p>}
        <p className="leading-relaxed">{message}</p>
      </div>
      {onDismiss && (
        <button onClick={onDismiss} className="shrink-0 opacity-60 hover:opacity-100">
          <XCircle className="h-4 w-4" />
        </button>
      )}
    </div>
  )
}
