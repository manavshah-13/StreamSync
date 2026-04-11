import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, AreaChart, Area, ReferenceLine
} from 'recharts'
import { Activity, Zap, TrendingUp, AlertTriangle, Clock, RefreshCw, Database, Cpu } from 'lucide-react'
import { fetchMetrics, fetchDemandVelocity, fetchRepricingEvents } from '../services/api'
import { Spinner } from '../components/Loader'

// ─── Mock data generators ─────────────────────────────────────────────────────
const genDemandHistory = () =>
  Array.from({ length: 20 }, (_, i) => ({
    t: `${i * 30}s`,
    velocity: Math.floor(30 + Math.random() * 60),
    reprices: Math.floor(Math.random() * 400 + 100),
  }))

const genRepricingEvents = () => [
  { id: 1, sku: 'SKU-88241', oldPrice: 49.99,  newPrice: 54.99,  reason: 'Demand spike +82%', ts: '21:59:01' },
  { id: 2, sku: 'SKU-10453', oldPrice: 129.00, newPrice: 119.00, reason: 'Competitor drop',    ts: '21:58:47' },
  { id: 3, sku: 'SKU-33891', oldPrice: 19.99,  newPrice: 24.99,  reason: 'Low inventory',      ts: '21:58:22' },
  { id: 4, sku: 'SKU-72810', oldPrice: 89.99,  newPrice: 84.99,  reason: 'Session decay',      ts: '21:57:55' },
  { id: 5, sku: 'SKU-55623', oldPrice: 34.99,  newPrice: 39.99,  reason: 'Demand spike +91%', ts: '21:57:31' },
]

const MOCK_METRICS = {
  p99Latency: 145,
  activeSkus: '10.4M',
  repricingRate: '42,100/s',
  activeSessions: 18340,
  cacheHitRate: 98.7,
  streamLag: '12ms',
}

// ─── Palette (matches Home light theme) ──────────────────────────────────────
const SAND      = '#F2EBE3'        // page bg
const SAND_2    = '#EDE6DC'        // section bg
const SAND_3    = '#E8E0D4'        // ticker / header bg
const BORDER    = 'rgba(0,0,0,0.08)'
const MINT      = '#16A34A'        // primary accent (forest mint)
const MINT_DIM  = 'rgba(22,163,74,0.1)'
const AMBER     = '#C97A2A'        // amber accent
const DANGER    = '#C0392B'        // price-down / error

// ─── p99 Latency Gauge ────────────────────────────────────────────────────────
function LatencyGauge({ value = 145 }) {
  const max   = 300
  const angle = (value / max) * 180 - 90
  const color = value < 150 ? MINT : value < 200 ? AMBER : DANGER

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative w-48 h-28 overflow-hidden">
        <svg viewBox="0 0 200 110" className="w-full h-full">
          {/* Track */}
          <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="rgba(0,0,0,0.08)" strokeWidth="14" strokeLinecap="round" />
          {/* Fill */}
          {[0, 25, 50, 75].map((pct, i) => {
            const filled = (value / max) > pct / 100
            const c      = filled ? color : 'rgba(0,0,0,0.06)'
            const sa     = (((pct / 100) * 180) - 180) * Math.PI / 180
            const ea     = ((((pct + 25) / 100) * 180) - 180) * Math.PI / 180
            const x1 = 100 + 80 * Math.cos(sa), y1 = 100 + 80 * Math.sin(sa)
            const x2 = 100 + 80 * Math.cos(ea), y2 = 100 + 80 * Math.sin(ea)
            return (
              <path key={i}
                d={`M ${x1} ${y1} A 80 80 0 0 1 ${x2} ${y2}`}
                fill="none" stroke={c} strokeWidth="14" strokeLinecap="round"
              />
            )
          })}
          {/* Needle */}
          <motion.line
            x1="100" y1="100" x2="100" y2="30"
            stroke={color} strokeWidth="3" strokeLinecap="round"
            style={{ transformOrigin: '100px 100px' }}
            animate={{ rotate: angle }}
            transition={{ type: 'spring', stiffness: 60, damping: 15 }}
          />
          <circle cx="100" cy="100" r="6" fill={color} />
          <text x="18"  y="115" fill="rgba(0,0,0,0.35)" fontSize="9">0</text>
          <text x="100" y="18"  fill="rgba(0,0,0,0.35)" fontSize="9" textAnchor="middle">150</text>
          <text x="186" y="115" fill="rgba(0,0,0,0.35)" fontSize="9" textAnchor="end">300</text>
        </svg>
      </div>
      <div className="text-center">
        <p className="text-3xl font-extrabold font-mono" style={{ color }}>
          {value}<span className="text-base font-normal" style={{ color: 'rgba(0,0,0,0.4)' }}>ms</span>
        </p>
        <p className="text-xs mt-0.5" style={{ color: 'rgba(0,0,0,0.4)' }}>p99 Latency</p>
      </div>
    </div>
  )
}

// ─── Custom Tooltip ───────────────────────────────────────────────────────────
function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-xl px-4 py-3 shadow-xl text-xs space-y-1"
      style={{ background: 'rgba(255,255,255,0.9)', border: `1px solid ${BORDER}`, backdropFilter: 'blur(12px)' }}>
      <p className="font-mono" style={{ color: 'rgba(0,0,0,0.5)' }}>{label}</p>
      {payload.map(p => (
        <p key={p.dataKey} style={{ color: p.color }} className="font-semibold">
          {p.name}: {p.value}
        </p>
      ))}
    </div>
  )
}

// ─── Dashboard ────────────────────────────────────────────────────────────────
export default function Dashboard() {
  const [metrics, setMetrics]       = useState(MOCK_METRICS)
  const [demandData, setDemand]     = useState(genDemandHistory)
  const [events, setEvents]         = useState(genRepricingEvents)
  const [loading, setLoading]       = useState(false)
  const [lastUpdate, setLastUpdate] = useState(new Date())
  const timerRef = useRef(null)

  const loadAll = () => {
    setLoading(true)
    Promise.allSettled([
      fetchMetrics().then(d => setMetrics(m => ({ ...m, ...d }))),
      fetchDemandVelocity().then(d => setDemand(d.history ?? genDemandHistory())),
      fetchRepricingEvents().then(d => setEvents(d.events ?? genRepricingEvents())),
    ]).finally(() => { setLoading(false); setLastUpdate(new Date()) })
  }

  useEffect(() => {
    loadAll()
    timerRef.current = setInterval(() => {
      setDemand(prev => [
        ...prev.slice(1),
        {
          t: new Date().toLocaleTimeString('en', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }),
          velocity: Math.floor(30 + Math.random() * 60),
          reprices: Math.floor(Math.random() * 400 + 100),
        },
      ])
      setLastUpdate(new Date())
    }, 5000)
    return () => clearInterval(timerRef.current)
  }, [])

  const statCards = [
    { label: 'Active SKUs',     value: metrics.activeSkus,                          icon: Database, accent: MINT  },
    { label: 'Repricing Rate',  value: metrics.repricingRate,                        icon: Zap,      accent: AMBER },
    { label: 'Active Sessions', value: metrics.activeSessions?.toLocaleString(),     icon: Activity, accent: MINT  },
    { label: 'Cache Hit Rate',  value: `${metrics.cacheHitRate}%`,                   icon: Cpu,      accent: MINT  },
    { label: 'Stream Lag',      value: metrics.streamLag,                            icon: Clock,    accent: MINT  },
  ]

  const panel = {
    background: 'rgba(255,255,255,0.7)',
    border: `1px solid ${BORDER}`,
    backdropFilter: 'blur(20px)',
    WebkitBackdropFilter: 'blur(20px)',
    boxShadow: '0 4px 24px rgba(0,0,0,0.06)',
    borderRadius: '1rem',
  }

  return (
    <div style={{ background: SAND }} className="min-h-screen pt-28 pb-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">

        {/* ── Header ─────────────────────────────────────────────────────────── */}
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            {/* Eyebrow */}
            <div className="flex items-center gap-2.5 mb-2">
              <motion.span animate={{ opacity: [1, 0.25, 1] }} transition={{ duration: 2, repeat: Infinity }}
                className="w-2 h-2 rounded-full" style={{ background: MINT }} />
              <span className="text-xs font-black uppercase tracking-[0.2em]" style={{ color: MINT }}>
                System Health Strip
              </span>
              <span className="text-xs" style={{ color: 'rgba(0,0,0,0.2)' }}>—</span>
              <span className="text-xs font-medium" style={{ color: 'rgba(0,0,0,0.35)' }}>Judge's View</span>
            </div>
            <h1 className="text-3xl font-black tracking-tight flex items-center gap-3" style={{ color: '#1A1A1A' }}>
              Live Dashboard
              <span className="inline-flex items-center gap-1.5 text-xs font-bold px-3 py-1 rounded-full"
                style={{ background: MINT_DIM, border: `1px solid ${MINT}44`, color: MINT }}>
                <motion.span animate={{ scale: [1, 1.5, 1], opacity: [1, 0.4, 1] }} transition={{ duration: 2, repeat: Infinity }}
                  className="w-1.5 h-1.5 rounded-full" style={{ background: MINT }} />
                LIVE
              </span>
            </h1>
            <p className="text-sm mt-1" style={{ color: 'rgba(0,0,0,0.45)' }}>
              Real-time engine metrics &amp; repricing intelligence
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-[11px] font-mono" style={{ color: 'rgba(0,0,0,0.35)' }}>
              Updated {lastUpdate.toLocaleTimeString()}
            </span>
            <button onClick={loadAll} disabled={loading}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all disabled:opacity-50"
              style={{ background: 'rgba(255,255,255,0.8)', border: `1px solid ${BORDER}`, color: '#1A1A1A', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
              {loading ? <Spinner size={14} /> : <RefreshCw size={14} />}
              Refresh
            </button>
          </div>
        </div>

        {/* ── Gauge + Stat tiles ─────────────────────────────────────────────── */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {/* p99 Gauge */}
          <motion.div
            initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }}
            style={panel}
            className="flex flex-col items-center justify-center gap-4 p-6"
          >
            <div className="flex items-center gap-2 self-start">
              <Clock size={15} style={{ color: MINT }} />
              <span className="text-sm font-semibold" style={{ color: '#1A1A1A' }}>Response Latency</span>
            </div>
            <LatencyGauge value={metrics.p99Latency ?? 145} />
            <div className="grid grid-cols-2 gap-3 w-full text-center text-xs">
              {[['p50', '62ms', MINT], ['p95', '118ms', MINT]].map(([k, v, c]) => (
                <div key={k} className="rounded-xl py-2" style={{ background: MINT_DIM, border: `1px solid ${MINT}22` }}>
                  <p style={{ color: 'rgba(0,0,0,0.4)' }}>{k}</p>
                  <p className="font-bold font-mono" style={{ color: c }}>{v}</p>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Stat tiles */}
          <div className="lg:col-span-2 grid grid-cols-2 sm:grid-cols-3 gap-4">
            {statCards.map(({ label, value, icon: Icon, accent }, i) => (
              <motion.div
                key={label}
                initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.07 }}
                style={panel}
                className="p-5 flex flex-col gap-3"
              >
                <div className="w-9 h-9 rounded-xl flex items-center justify-center"
                  style={{ background: `${accent}18`, border: `1px solid ${accent}30` }}>
                  <Icon size={17} style={{ color: accent }} />
                </div>
                <div className="text-2xl font-extrabold font-mono" style={{ color: accent }}>{value}</div>
                <div className="text-[11px]" style={{ color: 'rgba(0,0,0,0.4)' }}>{label}</div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* ── Demand Velocity Chart ──────────────────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
          style={panel}
          className="p-6 space-y-4"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TrendingUp size={16} style={{ color: MINT }} />
              <h2 className="font-bold text-base" style={{ color: '#1A1A1A' }}>SKU Demand Velocity</h2>
            </div>
            <span className="text-[10px] font-mono" style={{ color: 'rgba(0,0,0,0.35)' }}>Auto-refreshes every 5s</span>
          </div>

          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={demandData} margin={{ top: 4, right: 4, left: -24, bottom: 0 }}>
              <defs>
                <linearGradient id="velGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor={MINT}  stopOpacity={0.22} />
                  <stop offset="95%" stopColor={MINT}  stopOpacity={0}    />
                </linearGradient>
                <linearGradient id="repGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor={AMBER} stopOpacity={0.2}  />
                  <stop offset="95%" stopColor={AMBER} stopOpacity={0}    />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="rgba(0,0,0,0.06)" strokeDasharray="3 3" />
              <XAxis dataKey="t" tick={{ fill: 'rgba(0,0,0,0.35)', fontSize: 10 }} tickLine={false} axisLine={false} />
              <YAxis                tick={{ fill: 'rgba(0,0,0,0.35)', fontSize: 10 }} tickLine={false} axisLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine y={75} stroke={DANGER} strokeDasharray="4 2"
                label={{ value: 'Spike threshold', fill: DANGER, fontSize: 9 }} />
              <Area type="monotone" dataKey="velocity"  name="Demand %"     stroke={MINT}  strokeWidth={2} fill="url(#velGrad)" dot={false} activeDot={{ r: 4, fill: MINT  }} />
              <Area type="monotone" dataKey="reprices"  name="Reprices/min" stroke={AMBER} strokeWidth={2} fill="url(#repGrad)" dot={false} activeDot={{ r: 4, fill: AMBER }} />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>

        {/* ── Repricing Events Log ───────────────────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
          style={panel}
          className="p-6 space-y-4"
        >
          <div className="flex items-center gap-2">
            <AlertTriangle size={16} style={{ color: AMBER }} />
            <h2 className="font-bold text-base" style={{ color: '#1A1A1A' }}>Recent Repricing Events</h2>
            <span className="ml-auto inline-flex items-center gap-1.5 text-xs font-bold px-3 py-1 rounded-full"
              style={{ background: `${AMBER}15`, border: `1px solid ${AMBER}40`, color: AMBER }}>
              {events.length} events
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-[10px] uppercase tracking-wider" style={{ color: 'rgba(0,0,0,0.35)' }}>
                  <th className="text-left py-2 px-3">SKU</th>
                  <th className="text-right px-3">Old Price</th>
                  <th className="text-right px-3">New Price</th>
                  <th className="text-right px-3">Δ</th>
                  <th className="text-left px-3 hidden sm:table-cell">Trigger</th>
                  <th className="text-right px-3">Time</th>
                </tr>
              </thead>
              <tbody>
                {events.map((ev, i) => {
                  const delta = ev.newPrice - ev.oldPrice
                  const isUp  = delta > 0
                  return (
                    <motion.tr
                      key={ev.id}
                      initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }}
                      className="transition-colors"
                      style={{ borderTop: '1px solid rgba(0,0,0,0.05)' }}
                      onMouseEnter={e => e.currentTarget.style.background = 'rgba(0,0,0,0.02)'}
                      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                    >
                      <td className="py-3 px-3 font-mono font-semibold" style={{ color: '#1A1A1A' }}>{ev.sku}</td>
                      <td className="px-3 text-right font-mono"       style={{ color: 'rgba(0,0,0,0.45)' }}>${ev.oldPrice.toFixed(2)}</td>
                      <td className="px-3 text-right font-mono font-bold" style={{ color: '#1A1A1A' }}>${ev.newPrice.toFixed(2)}</td>
                      <td className="px-3 text-right font-mono font-bold" style={{ color: isUp ? DANGER : MINT }}>
                        {isUp ? '+' : ''}{delta.toFixed(2)}
                      </td>
                      <td className="px-3 hidden sm:table-cell" style={{ color: 'rgba(0,0,0,0.4)' }}>{ev.reason}</td>
                      <td className="px-3 text-right font-mono"       style={{ color: 'rgba(0,0,0,0.35)' }}>{ev.ts}</td>
                    </motion.tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </motion.div>

      </div>
    </div>
  )
}
