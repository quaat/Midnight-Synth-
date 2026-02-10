'use client'

export function LedDisplay({ label, value, unit = '' }: { label: string; value: string | number; unit?: string }) {
  return (
    <div className='rounded-md border border-cyan-300/30 bg-black/70 p-2'>
      <div className='text-[10px] uppercase tracking-wide text-slate-400'>{label}</div>
      <div className='font-mono text-lg text-cyan-300'>
        {value}
        <span className='ml-1 text-xs text-slate-400'>{unit}</span>
      </div>
    </div>
  )
}
