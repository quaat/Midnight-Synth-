'use client'

const whiteNotes = [0, 2, 4, 5, 7, 9, 11]

export function Piano({ active, onNoteOn, onNoteOff }: {
  active: { note: number; vel: number }[]
  onNoteOn: (n: number, v: number) => void
  onNoteOff: (n: number) => void
}) {
  const activeSet = new Map(active.map((n) => [n.note, n.vel]))

  return (
    <div className='panel overflow-x-auto'>
      <div className='flex min-w-[900px]'>
        {Array.from({ length: 24 }).map((_, i) => {
          const note = 48 + i
          const pitch = note % 12
          const isWhite = whiteNotes.includes(pitch)
          const vel = activeSet.get(note) || 0
          return (
            <button
              key={note}
              onMouseDown={() => onNoteOn(note, 100)}
              onMouseUp={() => onNoteOff(note)}
              onTouchStart={() => onNoteOn(note, 100)}
              onTouchEnd={() => onNoteOff(note)}
              className={`relative h-28 border ${isWhite ? 'w-10 bg-slate-50 text-black' : 'w-7 bg-slate-900 text-white -mx-3 z-10'} ${vel ? 'ring-2 ring-cyan-400' : ''}`}
              style={{ opacity: vel ? 0.55 + vel / 260 : 1 }}
            />
          )
        })}
      </div>
    </div>
  )
}
