'use client'

type Props = {
  label: string
  value: number
  min: number
  max: number
  onChange: (v: number) => void
  modAmount?: number
}

export function SliderGauge({ label, value, min, max, onChange, modAmount = 0 }: Props) {
  const pct = ((value - min) / (max - min)) * 100
  return (
    <div className='space-y-2'>
      <div className='text-xs text-slate-300'>{label}</div>
      <div className='h-2 rounded bg-slate-800 overflow-hidden'>
        <div className='h-full bg-neon/90' style={{ width: `${pct}%` }} />
        <div className='h-full bg-fuchsia-400/60 -mt-2' style={{ width: `${Math.min(100, pct + modAmount * 100)}%` }} />
      </div>
      <input
        className='w-full accent-cyan-300'
        type='range'
        min={min}
        max={max}
        step={(max - min) / 300}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </div>
  )
}
