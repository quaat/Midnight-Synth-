'use client'

import { useRef, useState } from 'react'

type Props = {
  label: string
  value: number
  min: number
  max: number
  onChange: (next: number) => void
}

export function Knob({ label, value, min, max, onChange }: Props) {
  const [dragging, setDragging] = useState(false)
  const startRef = useRef<{ y: number; v: number } | null>(null)
  const pct = (value - min) / (max - min)
  const angle = -140 + pct * 280

  return (
    <div
      className='flex flex-col items-center gap-2 select-none'
      onMouseDown={(e) => {
        setDragging(true)
        startRef.current = { y: e.clientY, v: value }
      }}
      onMouseMove={(e) => {
        if (!dragging || !startRef.current) return
        const delta = (startRef.current.y - e.clientY) * (e.shiftKey ? 0.001 : 0.004)
        const next = Math.max(min, Math.min(max, startRef.current.v + delta * (max - min)))
        onChange(next)
      }}
      onMouseUp={() => setDragging(false)}
      onMouseLeave={() => setDragging(false)}
      onDoubleClick={() => onChange((min + max) / 2)}
    >
      <div className='relative h-16 w-16 rounded-full bg-slate-900 border border-white/10'>
        <div
          className='absolute left-1/2 top-1/2 h-1 w-6 origin-left rounded bg-neon'
          style={{ transform: `translate(-2px,-50%) rotate(${angle}deg)` }}
        />
      </div>
      <div className='text-xs text-slate-300'>{label}</div>
      <div className='font-mono text-[11px] text-neon'>{value.toFixed(2)}</div>
    </div>
  )
}
