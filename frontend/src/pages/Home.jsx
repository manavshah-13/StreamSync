import React, { useEffect, useState, useRef } from 'react'
import { Link } from 'react-router-dom'
import { motion, useScroll, useTransform, AnimatePresence } from 'framer-motion'
import {
  ArrowRight, TrendingUp, Activity,
  Headphones, Monitor, Laptop, Coffee,
  ChevronRight, ShoppingBag
} from 'lucide-react'
import { fetchProducts, fetchRecommendations, captureView } from '../services/api'
import { getSessionId } from '../utils/session'

// ─── Static product data ──────────────────────────────────────────────────────
const PRODUCTS = [
  { id: 'prod-1',  name: 'Surface Pro AI Edition', price: 106500, cat: 'Computing',  tag: 'BESTSELLER',  icon: Laptop,     image: '/images/surface_pro.png', demand: 91 },
  { id: 'prod-2',  name: 'StreamBuds Pro ANC',     price: 14750,  cat: 'Audio',       tag: 'DEMAND SPIKE', icon: Headphones, image: '/images/stream_buds.png', demand: 87 },
  { id: 'prod-3',  name: 'Creator Laptop X1',      price: 151600, cat: 'Computing',  tag: 'TRENDING',    icon: Monitor,    image: '/images/creator_laptop.png', demand: 78 },
  { id: 'prod-4',  name: 'Artisan Desk Collection', price: 28700, cat: 'Lifestyle',   tag: 'NEW',         icon: Coffee,     image: '/images/artisan_desk.png', demand: 55 },
]

// ─── Sub-components ───────────────────────────────────────────────────────────

/** Warm-sand product card with amber rim */
function LuxProductCard({ product, index }) {
  const Icon = product.icon
  const isSpike = product.demand > 80
  return (
    <motion.div
      initial={{ opacity: 0, y: 28 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay: index * 0.1, duration: 0.5 }}
      whileHover={{ y: -6, transition: { duration: 0.25 } }}
      className="group cursor-pointer relative"
    >
      <Link to={`/products/${product.id}`}>
        {/* Amber rim outer glow */}
        <div className="absolute -inset-px rounded-[28px] opacity-0 group-hover:opacity-100 transition-opacity duration-500"
          style={{ background: 'linear-gradient(135deg, rgba(201,122,42,0.4), transparent 60%)', filter: 'blur(1px)' }} />

        <div
          className="relative rounded-[28px] overflow-hidden flex flex-col"
          style={{
            background: '#F8FAF7',
            boxShadow: '0 2px 0 rgba(201,122,42,0.15), 0 24px 64px rgba(0,0,0,0.5)',
          }}
        >
          {/* Tag */}
          {product.tag && (
            <div className="absolute top-4 left-4 z-10">
              <span className={`text-2xs font-black tracking-[0.15em] px-2.5 py-1 rounded-full border ${
                isSpike
                  ? 'bg-[#0D0D0D] text-mint border-mint/30'
                  : 'bg-[#0D0D0D]/80 text-white/70 border-white/10'
              }`}>
                {isSpike && <span className="inline-block w-1 h-1 rounded-full bg-mint mr-1.5 animate-mintPulse align-middle" />}
                {product.tag}
              </span>
            </div>
          )}

          {/* Product image area */}
          <div className="h-52 flex items-center justify-center relative overflow-hidden"
            style={{ background: 'linear-gradient(145deg, #FAF6F2 0%, #EDE3D8 100%)' }}>
            {/* Ambient amber light */}
            <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-40 h-16 rounded-full opacity-30 blur-2xl z-0"
              style={{ background: 'radial-gradient(ellipse, #C97A2A 0%, transparent 70%)' }} />
            
            {product.image ? (
              <img src={product.image} alt={product.name} className="w-full h-full object-cover relative z-10 opacity-95 group-hover:scale-[1.03] transition-transform duration-500" />
            ) : (
              <Icon size={64} className="text-[#8B7355] group-hover:text-[#6B5335] transition-colors duration-300 relative z-10" />
            )}
          </div>

          {/* Info */}
          <div className="p-5 space-y-3" style={{ background: '#F8FAF7' }}>
            <div>
              <p className="text-[10px] font-bold text-[#8B7355] uppercase tracking-[0.15em]">{product.cat}</p>
              <h3 className="font-bold text-[#1A1A1A] text-sm mt-0.5 leading-snug group-hover:text-[#0D0D0D] transition-colors">{product.name}</h3>
            </div>

            {/* Demand bar */}
            <div className="space-y-1">
              <div className="flex justify-between text-[10px]">
                <span className="text-[#8B7355]">Demand</span>
                <span className={`font-bold font-mono ${isSpike ? 'text-[#E05C00]' : 'text-[#4A7C59]'}`}>{product.demand}%</span>
              </div>
              <div className="h-0.5 bg-[#DDD3C7] rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  whileInView={{ width: `${product.demand}%` }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.9, ease: 'easeOut', delay: index * 0.08 }}
                  className="h-full rounded-full"
                  style={{ background: isSpike ? '#E05C00' : '#16A34A' }}
                />
              </div>
            </div>

            <div className="flex items-center justify-between pt-1">
              <span className="text-xl font-black font-mono text-[#1A1A1A]">₹{product.price.toLocaleString('en-IN')}</span>
              <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full"
                style={{ background: '#0D0D0D', border: '1px solid rgba(22,163,74,0.25)' }}>
                <motion.span
                  animate={{ scale: [1, 1.6, 1], opacity: [1, 0.3, 1] }}
                  transition={{ duration: 2, repeat: Infinity }}
                  className="w-1.5 h-1.5 rounded-full bg-mint inline-block" />
                <span className="text-2xs font-bold text-mint tracking-widest">STREAMSYNC</span>
              </div>
            </div>
          </div>
        </div>
      </Link>
    </motion.div>
  )
}

// ─── HOME PAGE ────────────────────────────────────────────────────────────────
export default function Home() {
  const heroRef = useRef(null)
  const { scrollYProgress } = useScroll({ target: heroRef, offset: ['start start', 'end start'] })
  const heroY      = useTransform(scrollYProgress, [0, 1], ['0%', '20%'])
  const heroOpacity= useTransform(scrollYProgress, [0, 0.7], [1, 0])
  
  const [trending, setTrending] = useState(PRODUCTS)
  const [recs, setRecs] = useState([])
  const sessionId = getSessionId()

  useEffect(() => {
    // Fetch all products to find highest demand for "Trending"
    fetchProducts().then(res => {
      const sorted = (res.products || []).sort((a,b) => b.demandVelocity - a.demandVelocity)
      if (sorted.length > 0) setTrending(sorted.slice(0, 4))
    })

    // Fetch personalised recommendations for landing page (defaults to prod-1 context)
    fetchRecommendations('prod-1', sessionId, 4).then(res => {
      setRecs(res.products || [])
    })

    // Capture landing page hit
    captureView('landing', sessionId).catch(() => {})
  }, [sessionId])

  return (
    <div style={{ background: '#F2EBE3' }} className="text-[#1A1A1A] overflow-x-hidden">

      {/* ══════════════════════════════════════════════════════════════════
          HERO
      ══════════════════════════════════════════════════════════════════ */}
      <section ref={heroRef} className="relative min-h-screen flex items-center justify-center overflow-hidden">
        <motion.div style={{ y: heroY, opacity: heroOpacity }} className="absolute inset-0 pointer-events-none">
          {/* Warm radial bloom */}
          <div className="absolute inset-0" style={{ background: 'radial-gradient(ellipse 110% 60% at 50% 0%, rgba(22,163,74,0.09) 0%, transparent 55%)' }} />
          {/* Subtle warm grid */}
          <div className="absolute inset-0 opacity-[0.06]"
            style={{ backgroundImage: 'linear-gradient(rgba(0,0,0,0.08) 1px,transparent 1px),linear-gradient(90deg,rgba(0,0,0,0.08) 1px,transparent 1px)', backgroundSize: '80px 80px' }} />
          {/* Amber bottom rim */}
          <div className="absolute bottom-0 right-0 w-[600px] h-[600px] opacity-[0.12]"
            style={{ background: 'radial-gradient(ellipse at 100% 100%, #C97A2A, transparent 60%)' }} />
          {/* Left cream fade */}
          <div className="absolute top-0 left-0 w-[400px] h-[400px] opacity-[0.5]"
            style={{ background: 'radial-gradient(ellipse at 0% 0%, #FAF6F2, transparent 70%)' }} />
        </motion.div>

        <div className="relative z-10 max-w-6xl mx-auto px-6 sm:px-8 pt-32 pb-20 text-center space-y-10">


          {/* Headline — fashion editorial scale */}
          <motion.div initial={{ opacity: 0, y: 36 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.1 }}>
            <h1 className="font-black tracking-[-0.03em] leading-[0.95]"
              style={{ fontSize: 'clamp(3.5rem, 10vw, 8.5rem)', letterSpacing: '-0.03em', color: '#0D0D0D' }}>
              Smart Prices<br />
              <span style={{
                background: 'linear-gradient(135deg, #16A34A 0%, #16A34A 50%, #16A34A 100%)',
                WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text',
              }}>
                with AI.
              </span>
            </h1>
          </motion.div>

          {/* Sub */}
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.45 }}
            className="text-lg sm:text-xl max-w-xl mx-auto leading-relaxed font-light" style={{ color: '#5C5048' }}>
            StreamSync: Markets Move Fast.{' '}
            <span style={{ color: '#2A2018' }} className="font-semibold">We Move Faster.</span>
          </motion.p>

          {/* CTAs */}
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }}
            className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/products">
              <motion.button whileHover={{ scale: 1.04, boxShadow: '0 0 32px rgba(22,163,74,0.35)' }} whileTap={{ scale: 0.97 }}
                className="inline-flex items-center gap-2.5 px-9 py-4 rounded-2xl font-bold text-base"
                style={{ background: '#16A34A', color: '#0D0D0D', boxShadow: '0 0 24px rgba(22,163,74,0.2)' }}>
                <TrendingUp size={17} /> Explore Trends
              </motion.button>
            </Link>
            <Link to="/dashboard">
              <motion.button whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
                className="inline-flex items-center gap-2.5 px-9 py-4 rounded-2xl font-bold text-base transition-all"
                style={{ border: '1px solid rgba(0,0,0,0.15)', background: 'rgba(255,255,255,0.6)', color: '#2A2018', backdropFilter: 'blur(12px)' }}>
                <Activity size={17} /> How It Works
              </motion.button>
            </Link>
          </motion.div>

        </div>
      </section>

      {/* ══════════════════════════════════════════════════════════════════
          TRENDING NOW — Warm sand cards
      ══════════════════════════════════════════════════════════════════ */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-20 space-y-8">
        <div className="flex items-end justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.2em] mb-2" style={{ color: '#0A7A3E' }}>Live Pricing</p>
            <h2 className="text-4xl font-black tracking-tight" style={{ color: '#1A1A1A' }}>Trending Now</h2>
            <p className="text-sm mt-1" style={{ color: 'rgba(0,0,0,0.4)' }}>Highest demand velocity — prices update every 30s</p>
          </div>
          <Link to="/products" className="inline-flex items-center gap-1.5 text-sm font-bold transition-colors group"
            style={{ color: 'rgba(0,0,0,0.4)' }}
            onMouseEnter={e => e.currentTarget.style.color='#0A7A3E'}
            onMouseLeave={e => e.currentTarget.style.color='rgba(0,0,0,0.4)'}>
            View all <ArrowRight size={14} className="group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {trending.map((p, i) => (
            <LuxProductCard 
              key={p.id} 
              product={{
                ...p,
                tag: p.demandVelocity > 80 ? 'DEMAND SPIKE' : 'TRENDING',
                demand: p.demandVelocity
              }} 
              index={i} 
            />
          ))}
        </div>
      </section>

      {/* ══════════════════════════════════════════════════════════════════
          RECOMMENDED — Dark minimal cards
      ══════════════════════════════════════════════════════════════════ */}
      <section style={{ background: '#E8DED2', borderTop: '1px solid rgba(0,0,0,0.06)' }}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 space-y-8">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.2em] mb-2" style={{ color: '#0A7A3E' }}>Personalised</p>
            <h2 className="text-4xl font-black tracking-tight" style={{ color: '#1A1A1A' }}>Recommended for Your Workspace</h2>
            <p className="text-sm mt-1" style={{ color: 'rgba(0,0,0,0.4)' }}>Curated by real-time session intelligence</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {(recs.length > 0 ? recs : PRODUCTS).map((p, i) => {
              const icons = [Monitor, Headphones, Laptop, ShoppingBag]
              const Icon  = icons[i % icons.length]
              return (
                <motion.div key={`rec-${p.id}`}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.08 }}
                  className="group cursor-pointer"
                >
                  <Link to={`/products/${p.id}`}>
                    <div className="rounded-2xl p-5 flex flex-col gap-4 transition-all duration-300 h-full"
                      style={{ background: 'rgba(255,255,255,0.6)', border: '1px solid rgba(0,0,0,0.07)', boxShadow: '0 2px 12px rgba(0,0,0,0.05)' }}>
                      <div className="aspect-square rounded-xl flex items-center justify-center overflow-hidden relative"
                        style={{ background: 'rgba(0,0,0,0.04)' }}>
                        {p.image ? (
                          <img src={p.image} alt={p.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 mix-blend-multiply" />
                        ) : (
                          <Icon size={40} style={{ color: 'rgba(0,0,0,0.2)' }} className="group-hover:text-[#16A34A] transition-colors duration-300" />
                        )}
                      </div>
                      <div className="space-y-0.5 flex-1">
                        <p className="text-2xs uppercase tracking-widest" style={{ color: '#8B7355' }}>{p.category || p.cat}</p>
                        <h4 className="font-bold text-sm line-clamp-2 transition-colors" style={{ color: '#2A2018' }}>{p.name}</h4>
                      </div>
                      <div className="flex items-center justify-between mt-auto">
                        <span className="text-lg font-black font-mono" style={{ color: '#1A1A1A' }}>₹{p.price.toLocaleString('en-IN')}</span>
                        <span className="text-xs font-bold rounded-xl px-3 py-1.5 transition-all" style={{ color: '#16A34A', border: '1px solid rgba(22,163,74,0.3)', background: 'rgba(22,163,74,0.08)' }}>View</span>
                      </div>
                    </div>
                  </Link>
                </motion.div>
              )
            })}
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════════════════════════════════
          CTA BANNER
      ══════════════════════════════════════════════════════════════════ */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="relative rounded-3xl overflow-hidden text-center px-10 py-20"
          style={{
            background: 'linear-gradient(135deg, #D4EDE0 0%, #F2EBE3 50%, #EDE0CC 100%)',
            border: '1px solid rgba(22,163,74,0.2)',
            boxShadow: '0 8px 48px rgba(0,0,0,0.08)',
          }}
        >
          <div className="absolute inset-0 pointer-events-none"
            style={{ background: 'radial-gradient(ellipse 80% 60% at 50% 10%, rgba(22,163,74,0.1) 0%, transparent 65%)' }} />
          <div className="relative z-10 space-y-6 max-w-lg mx-auto">
            <h2 className="text-5xl font-black leading-tight tracking-tight" style={{ color: '#1A1A1A' }}>
              Ready for hyper-<br />
              <span style={{ background: 'linear-gradient(135deg, #0A7A3E, #16A34A)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                efficient luxury?
              </span>
            </h2>
            <p className="text-base" style={{ color: 'rgba(0,0,0,0.4)' }}>Every product. Every second. Optimised by AI.</p>
            <Link to="/products">
              <motion.button
                whileHover={{ scale: 1.04, boxShadow: '0 0 40px rgba(22,163,74,0.25)' }}
                whileTap={{ scale: 0.97 }}
                className="inline-flex items-center gap-2.5 px-9 py-4 rounded-2xl font-bold text-base"
                style={{ background: '#16A34A', color: '#fff' }}
              >
                Start Shopping <ArrowRight size={16} />
              </motion.button>
            </Link>
          </div>
        </motion.div>
      </section>
    </div>
  )
}
