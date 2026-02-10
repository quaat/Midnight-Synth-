'use client'

export function Analyzer({ l, r }: { l: number; r: number }) {
  const lp = Math.min(100, l * 160)
  const rp = Math.min(100, r * 160)
  return (
    <div className='panel space-y-3'>
      <div className='text-sm'>Output Meters</div>
      <div className='space-y-2'>
        <div className='h-3 rounded bg-slate-800'><div className='h-full rounded bg-gradient-to-r from-cyan-400 to-fuchsia-500' style={{ width: `${lp}%` }} /></div>
        <div className='h-3 rounded bg-slate-800'><div className='h-full rounded bg-gradient-to-r from-cyan-400 to-fuchsia-500' style={{ width: `${rp}%` }} /></div>
      </div>
    </div>
  )
}
