import React from 'react'
import { cn } from '../../utils'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  padding?: boolean
}

export function Card({ children, className, padding = true, ...props }: CardProps) {
  return (
    <div className={cn('card', padding && 'p-6', className)} {...props}>
      {children}
    </div>
  )
}

export function CardHeader({ children, className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('flex items-center justify-between mb-5', className)} {...props}>
      {children}
    </div>
  )
}

export function CardTitle({ children, className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h2 className={cn('text-base font-semibold text-health-slate', className)} {...props}>
      {children}
    </h2>
  )
}
