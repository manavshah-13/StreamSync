import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, AreaChart, Area, ReferenceLine
} from 'recharts'
import { Activity, Zap, TrendingUp, AlertTriangle, Clock, RefreshCw, Database, Cpu } from 'lucide-react'
import { fetchMetrics, fetchDemandVelocity, fetchRepricingEvents, fetchMLInsights } from '../services/api'
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

// ─── Premium Dark Theme Palette ──────────────────────────────────────────────
const BG_BASE      = '#0B1020'
const CARD_BG      = '#111827'
const BORDER       = 'rgba(255, 255, 255, 0.1)'
const PRIMARY      = '#6D5DFC' // primary accent
const PRIMARY_DIM  = 'rgba(109, 93, 252, 0.1)'
const SECONDARY    = '#22D3EE' // secondary accent
const SUCCESS      = '#10B981'
const WARNING      = '#F59E0B'
const DANGER       = '#EF4444'

// ─── p99 Latency Gauge ────────────────────────────────────────────────────────
function LatencyGauge({ value = 145 }) {
  const max   = 300
  const angle = (value / max) * 180 - 90
  const color = value < 150 ? SUCCESS : value < 200 ? WARNING : DANGER

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative w-48 h-28 overflow-hidden">
        <svg viewBox="0 0 200 110" className="w-full h-full">
          {/* Track */}
          <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="14" strokeLinecap="round" />
          {/* Fill */}
          {[0, 25, 50, 75].map((pct, i) => {
            const filled = (value / max) > pct / 100
            const c      = filled ? color : 'rgba(255,255,255,0.03)'
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
          <text x="18"  y="115" fill="#9CA3AF" fontSize="9" fontWeight="bold">0</text>
          <text x="100" y="18"  fill="#9CA3AF" fontSize="9" fontWeight="bold" textAnchor="middle">150</text>
          <text x="186" y="115" fill="#9CA3AF" fontSize="9" fontWeight="bold" textAnchor="end">300</text>
        </svg>
      </div>
      <div className="text-center">
        <p className="text-3xl font-extrabold font-mono" style={{ color }}>
          {value}<span className="text-base font-normal text-[#9CA3AF]">ms</span>
        </p>
        <p className="text-xs mt-0.5 text-[#9CA3AF]">p99 Latency</p>
      </div>
    </div>
  )
}

// ─── Custom Tooltip ───────────────────────────────────────────────────────────
function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-xl px-4 py-3 shadow-xl text-xs space-y-1 bg-[#111827] border border-white/10">
      <p className="font-mono text-[#9CA3AF] font-bold">{label}</p>
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
  const [mlInsights, setMlInsights] = useState(null)
  const [loading, setLoading]       = useState(false)
  const [lastUpdate, setLastUpdate] = useState(new Date())
  const timerRef = useRef(null)

  const loadAll = () => {
    setLoading(true)
    Promise.allSettled([
      fetchMetrics().then(d => setMetrics(m => ({ ...m, ...d }))),
      fetchDemandVelocity().then(d => setDemand(d.history ?? genDemandHistory())),
      fetchRepricingEvents().then(d => setEvents(d.events ?? genRepricingEvents())),
      fetchMLInsights().then(setMlInsights),
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
    { label: 'Active SKUs',     value: metrics.activeSkus,                          icon: Database, accent: PRIMARY  },
    { label: 'Repricing Rate',  value: metrics.repricingRate,                        icon: Zap,      accent: SECONDARY },
    { label: 'Active Sessions', value: metrics.activeSessions?.toLocaleString(),     icon: Activity, accent: SUCCESS  },
    { label: 'Cache Hit Rate',  value: `${metrics.cacheHitRate}%`,                   icon: Cpu,      accent: WARNING  },
    { label: 'Stream Lag',      value: metrics.streamLag,                            icon: Clock,    accent: DANGER   },
  ]

  const panel = {
    background: 'rgba(17, 24, 39, 0.7)',
    border: `1px solid ${BORDER}`,
    backdropFilter: 'blur(20px)',
    WebkitBackdropFilter: 'blur(20px)',
    borderRadius: '1rem',
  }

  return (
    <div style={{ background: BG_BASE }} className="min-h-screen text-[#F9FAFB] pt-28 pb-24 px-6 md:px-12 lg:px-24">
      <div className="max-w-7xl mx-auto space-y-8">

        {/* ── Header ─────────────────────────────────────────────────────────── */}
        <div className="flex items-start justify-between flex-wrap gap-4 text-left">
          <div>
            {/* Eyebrow */}
            <div className="flex items-center gap-2.5 mb-2">
              <motion.span animate={{ opacity: [1, 0.25, 1] }} transition={{ duration: 2, repeat: Infinity }}
                className="w-2.5 h-2.5 rounded-full" style={{ background: SUCCESS }} />
              <span className="text-xs font-black uppercase tracking-[0.2em]" style={{ color: SUCCESS }}>
                System Health Strip
              </span>
              <span className="text-xs text-white/20">—</span>
              <span className="text-xs font-medium text-[#9CA3AF]">Telemetry Dashboard</span>
            </div>
            <h1 className="text-4xl font-extrabold tracking-tight flex items-center gap-3 bg-gradient-to-r from-primary-accent to-[#22D3EE] bg-clip-text text-transparent">
              Live Dashboard
              <span className="inline-flex items-center gap-1.5 text-xs font-bold px-3 py-1 rounded-full bg-[#10B981]/10 border border-[#10B981]/30 text-[#10B981]">
                <motion.span animate={{ scale: [1, 1.5, 1], opacity: [1, 0.4, 1] }} transition={{ duration: 2, repeat: Infinity }}
                  className="w-1.5 h-1.5 rounded-full" style={{ background: SUCCESS }} />
                LIVE
              </span>
            </h1>
            <p className="text-sm mt-1 text-[#9CA3AF]">
              Real-time engine metrics &amp; repricing intelligence
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-[11px] font-mono text-[#9CA3AF]">
              Updated {lastUpdate.toLocaleTimeString()}
            </span>
            <button onClick={loadAll} disabled={loading}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all disabled:opacity-50 bg-[#111827]/70 border border-white/10 hover:bg-white/5"
            >
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
              <Clock size={15} style={{ color: PRIMARY }} />
              <span className="text-sm font-semibold text-[#F9FAFB]">Response Latency</span>
            </div>
            <LatencyGauge value={metrics.p99Latency ?? 145} />
            <div className="grid grid-cols-2 gap-3 w-full text-center text-xs">
              {[['p50', '62ms', PRIMARY], ['p95', '118ms', PRIMARY]].map(([k, v, c]) => (
                <div key={k} className="rounded-xl py-2" style={{ background: PRIMARY_DIM, border: `1px solid ${PRIMARY}22` }}>
                  <p className="text-[#9CA3AF]">{k}</p>
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
                className="p-5 flex flex-col gap-3 text-left"
              >
                <div className="w-9 h-9 rounded-xl flex items-center justify-center"
                  style={{ background: `${accent}18`, border: `1px solid ${accent}30` }}>
                  <Icon size={17} style={{ color: accent }} />
                </div>
                <div className="text-2xl font-extrabold font-mono" style={{ color: accent }}>{value}</div>
                <div className="text-[11px] text-[#9CA3AF] font-bold uppercase tracking-wider">{label}</div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* ── AI Engine Health & Ethics ─────────────────────────────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {/* Revenue Uplift & Model Status */}
          <motion.div
            initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
            style={panel}
            className="p-6 space-y-5 text-left"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Cpu size={16} style={{ color: PRIMARY }} />
                <h2 className="font-bold text-base text-[#F9FAFB]">ML Engine Status</h2>
              </div>
              <span className="text-[10px] font-mono text-slate-400">REAL-TIME WARM-UP</span>
            </div>

            {/* Model Pills */}
            <div className="flex flex-wrap gap-2">
              {Object.entries(mlInsights?.model_status || {}).map(([name, status]) => (
                <div key={name} className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-[10px] font-bold border transition-all"
                  style={{
                    background: status === 'warm' ? `${PRIMARY}10` : 'rgba(255,255,255,0.03)',
                    borderColor: status === 'warm' ? `${PRIMARY}30` : 'rgba(255,255,255,0.08)',
                    color: status === 'warm' ? PRIMARY : '#9CA3AF'
                  }}>
                  <div className={`w-1.5 h-1.5 rounded-full ${status === 'warm' ? 'animate-pulse' : ''}`}
                    style={{ background: status === 'warm' ? PRIMARY : '#9CA3AF' }} />
                  {name.replace(/_/g, ' ').toUpperCase()}
                </div>
              ))}
            </div>

            {/* Top Uplift Products */}
            <div className="pt-2 space-y-3">
              <h3 className="text-xs font-black uppercase tracking-wider text-[#9CA3AF]">Top Revenue Gainers (AI Priced)</h3>
              <div className="space-y-2">
                {(mlInsights?.revenue_uplift?.top_products || []).slice(0, 3).map((p, i) => (
                  <div key={p.product_id} className="flex items-center justify-between p-3 rounded-xl bg-[#111827]/40 border border-white/5">
                    <div className="flex items-center gap-3">
                      <span className="text-[10px] font-bold text-[#9CA3AF]">#{i+1}</span>
                      <span className="text-xs font-semibold text-[#F9FAFB]">{p.product_id}</span>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className="text-[10px] text-[#9CA3AF]">Uplift</p>
                        <p className="text-xs font-bold text-green-400">${p.total_uplift.toFixed(0)}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-[10px] text-[#9CA3AF]">Events</p>
                        <p className="text-xs font-bold text-[#9CA3AF]">{p.event_count}</p>
                      </div>
                    </div>
                  </div>
                ))}
                {(!mlInsights?.revenue_uplift?.top_products?.length) && (
                  <div className="text-center py-4 text-[11px] text-[#9CA3AF] border border-dashed border-white/10 rounded-xl">
                    Waiting for repricing events to compute uplift...
                  </div>
                )}
              </div>
            </div>
          </motion.div>

          {/* Fairness & Ethics Audit */}
          <motion.div
            initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}
            style={panel}
            className="p-6 space-y-5 text-left"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertTriangle size={16} style={{ color: SECONDARY }} />
                <h2 className="font-bold text-base text-[#F9FAFB]">Ethical Guardrails</h2>
              </div>
              <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-[#22D3EE]/10 border border-[#22D3EE]/30 text-[10px] font-black text-[#22D3EE]">
                AUDIT SCORE: {mlInsights?.fairness_audit?.health_score || 100}%
              </div>
            </div>

            <div className="space-y-3">
              <h3 className="text-xs font-black uppercase tracking-wider text-[#9CA3AF]">Recent Price Disparity Alerts</h3>
              <div className="space-y-2 overflow-y-auto max-h-[180px] custom-scrollbar">
                {(mlInsights?.fairness_audit?.recent_alerts || []).map((alert, i) => (
                  <div key={i} className="flex items-center gap-3 p-3 rounded-xl bg-[#111827]/40 border border-white/5">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                      alert.severity === 'HIGH' ? 'bg-red-500/10 text-red-500' : 'bg-amber-500/10 text-amber-500'
                    }`}>
                      <AlertTriangle size={14} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-xs font-bold text-[#F9FAFB] truncate">{alert.product_id}</p>
                        <span className={`text-[9px] font-black px-1.5 py-0.5 rounded-full ${
                          alert.severity === 'HIGH' ? 'bg-red-500/20 text-red-400' : 'bg-amber-500/20 text-amber-400'
                        }`}>{alert.severity}</span>
                      </div>
                      <p className="text-[10px] text-[#9CA3AF] truncate">{alert.type}: Price ratio {alert.ratio.toFixed(2)}x</p>
                    </div>
                  </div>
                ))}
                {(!mlInsights?.fairness_audit?.recent_alerts?.length) && (
                  <div className="text-center py-8 text-[11px] text-[#9CA3AF] border border-dashed border-white/10 rounded-xl">
                    <Activity size={24} className="mx-auto mb-2 opacity-20 text-[#9CA3AF]" />
                    No active fairness violations detected.
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        </div>

        {/* ── Demand Velocity Chart ──────────────────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
          style={panel}
          className="p-6 space-y-4 text-left"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TrendingUp size={16} style={{ color: PRIMARY }} />
              <h2 className="font-bold text-base text-[#F9FAFB]">SKU Demand Velocity</h2>
            </div>
            <span className="text-[10px] font-mono text-[#9CA3AF]">Auto-refreshes every 5s</span>
          </div>

          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={demandData} margin={{ top: 4, right: 4, left: -24, bottom: 0 }}>
              <defs>
                <linearGradient id="velGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor={PRIMARY}  stopOpacity={0.22} />
                  <stop offset="95%" stopColor={PRIMARY}  stopOpacity={0}    />
                </linearGradient>
                <linearGradient id="repGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor={SECONDARY} stopOpacity={0.2}  />
                  <stop offset="95%" stopColor={SECONDARY} stopOpacity={0}    />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#1F2937" strokeDasharray="3 3" />
              <XAxis dataKey="t" tick={{ fill: '#9CA3AF', fontSize: 10 }} tickLine={false} axisLine={false} />
              <YAxis                tick={{ fill: '#9CA3AF', fontSize: 10 }} tickLine={false} axisLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine y={75} stroke={DANGER} strokeDasharray="4 2"
                label={{ value: 'Spike threshold', fill: DANGER, fontSize: 9 }} />
              <Area type="monotone" dataKey="velocity"  name="Demand %"     stroke={PRIMARY}  strokeWidth={2} fill="url(#velGrad)" dot={false} activeDot={{ r: 4, fill: PRIMARY  }} />
              <Area type="monotone" dataKey="reprices"  name="Reprices/min" stroke={SECONDARY} strokeWidth={2} fill="url(#repGrad)" dot={false} activeDot={{ r: 4, fill: SECONDARY }} />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>

        {/* ── Repricing Events Log ───────────────────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
          style={panel}
          className="p-6 space-y-4 text-left"
        >
          <div className="flex items-center gap-2">
            <AlertTriangle size={16} style={{ color: SECONDARY }} />
            <h2 className="font-bold text-base text-[#F9FAFB]">Recent Repricing Events</h2>
            <span className="ml-auto inline-flex items-center gap-1.5 text-xs font-bold px-3 py-1 rounded-full bg-[#22D3EE]/15 border border-[#22D3EE]/40 text-[#22D3EE]">
              {events.length} events
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-[10px] uppercase tracking-wider text-[#9CA3AF]">
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
                      className="transition-colors hover:bg-white/5"
                      style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}
                    >
                      <td className="py-3 px-3 font-mono font-semibold text-[#F9FAFB]">{ev.sku}</td>
                      <td className="px-3 text-right font-mono text-[#9CA3AF]">${ev.oldPrice.toFixed(2)}</td>
                      <td className="px-3 text-right font-mono font-bold text-[#F9FAFB]">${ev.newPrice.toFixed(2)}</td>
                      <td className="px-3 text-right font-mono font-bold" style={{ color: isUp ? DANGER : SUCCESS }}>
                        {isUp ? '+' : ''}{delta.toFixed(2)}
                      </td>
                      <td className="px-3 hidden sm:table-cell text-[#9CA3AF]">{ev.reason}</td>
                      <td className="px-3 text-right font-mono text-[#9CA3AF]">{ev.ts}</td>
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
