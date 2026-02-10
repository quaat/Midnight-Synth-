'use client'

import { useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { Analyzer } from '@/components/Analyzer'
import { Knob } from '@/components/Knob'
import { LedDisplay } from '@/components/LedDisplay'
import { Piano } from '@/components/Piano'
import { SliderGauge } from '@/components/SliderGauge'
import { useSynthSocket } from '@/lib/useSynthSocket'

const API_BASE = process.env.NEXT_PUBLIC_SYNTH_URL || 'http://localhost:8000'
const WS_URL = API_BASE.replace('http', 'ws') + '/ws'

export default function Home() {
  const { connected, state, send } = useSynthSocket(WS_URL)
  const [cutoff, setCutoff] = useState(2200)
  const [res, setRes] = useState(0.2)
  const [attack, setAttack] = useState(0.01)

  const runtime = useMemo(() => state ?? { meters: { l: 0, r: 0 }, notes: [], voices_active: 0 }, [state])

  const setParam = (path: string, value: number, localSetter: (n: number) => void) => {
    localSetter(value)
    send({ type: 'param.set', path, value })
  }

  return (
    <main className='min-h-screen p-6'>
      <header className='mb-4 panel flex flex-wrap items-center justify-between gap-3'>
        <h1 className='text-xl font-semibold'>Midnight Synth</h1>
        <div className='flex items-center gap-3'>
          <LedDisplay label='Link' value={connected ? 'CONNECTED' : 'OFFLINE'} />
          <LedDisplay label='Voices' value={runtime.voices_active} />
          <LedDisplay label='Cutoff' value={Math.round(cutoff)} unit='Hz' />
        </div>
      </header>

      <section className='grid gap-4 md:grid-cols-3'>
        <motion.div className='panel flex gap-5' initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <Knob label='Cutoff' value={cutoff} min={20} max={18000} onChange={(v) => setParam('filter.cutoff', v, setCutoff)} />
          <Knob label='Resonance' value={res} min={0} max={1} onChange={(v) => setParam('filter.resonance', v, setRes)} />
          <Knob label='Attack' value={attack} min={0} max={2} onChange={(v) => setParam('amp_env.attack', v, setAttack)} />
        </motion.div>

        <div className='panel'>
          <SliderGauge label='Noise' value={0} min={0} max={1} onChange={(v) => send({ type: 'param.set', path: 'noise_level', value: v })} modAmount={0.1} />
          <SliderGauge label='Master Gain' value={0.8} min={0} max={1.4} onChange={(v) => send({ type: 'param.set', path: 'master_gain', value: v })} />
        </div>

        <Analyzer l={runtime.meters.l} r={runtime.meters.r} />
      </section>

      <section className='mt-4'>
        <Piano
          active={runtime.notes}
          onNoteOn={(note, vel) => send({ type: 'midi.note_on', note, vel, channel: 0 })}
          onNoteOff={(note) => send({ type: 'midi.note_off', note, vel: 0, channel: 0 })}
        />
      </section>

      <footer className='mt-4 text-xs text-slate-400'>
        Backend endpoint: {API_BASE}. MIDI learn: right-click any control in future panel extension and map CC via websocket `midi.learn`.
      </footer>
    </main>
  )
}
