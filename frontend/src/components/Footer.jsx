import { Link } from 'react-router-dom'
import { Zap, Github, Twitter, CheckCircle2 } from 'lucide-react'
import { motion } from 'framer-motion'

export default function Footer() {
  return (
    <footer className="border-t border-white/5 bg-[#0D0D0D]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
          {/* Brand */}
          <div className="space-y-3">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-md bg-accent-green flex items-center justify-center shadow-lg shadow-accent-green/20">
                <Zap size={13} className="text-navy-950" fill="currentColor" />
              </div>
              <span className="font-bold text-base text-white">
                Stream<span className="text-accent-green">Sync</span>
              </span>
            </Link>
            <p className="text-sm text-slate-500 leading-relaxed max-w-xs">
              AI-driven dynamic pricing. Sub-200ms signal capture via Redis Streams.
            </p>
          </div>

          {/* Navigation */}
          <div>
            <p className="text-[10px] font-semibold text-slate-600 uppercase tracking-widest mb-4">Navigation</p>
            <ul className="space-y-2.5">
              {[['/', 'Home'], ['/products', 'Products'], ['/cart', 'Cart'], ['/dashboard', 'Dashboard']].map(([to, label]) => (
                <li key={to}>
                  <Link to={to} className="text-sm text-slate-400 hover:text-accent-green transition-colors">{label}</Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal */}
          <div>
            <p className="text-[10px] font-semibold text-slate-600 uppercase tracking-widest mb-4">Legal</p>
            <ul className="space-y-2.5">
              {['Privacy Policy', 'Terms of Service', 'AI Ethics Policy', 'Cookie Policy'].map(l => (
                <li key={l}>
                  <a href="#" className="text-sm text-slate-400 hover:text-accent-green transition-colors">{l}</a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-10 pt-6 border-t border-white/5 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-600">
          <span>© 2026 StreamSync. All rights reserved.</span>
          <div className="flex items-center gap-4">
            <a href="#" className="hover:text-slate-300 flex items-center gap-1.5 transition-colors"><Github size={13} /> GitHub</a>
            <a href="#" className="hover:text-slate-300 flex items-center gap-1.5 transition-colors"><Twitter size={13} /> Twitter</a>
          </div>
        </div>
      </div>

      {/* Persistent engine status bar */}
      <div className="border-t border-accent-green/15 bg-accent-green/5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2.5 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <motion.div
              animate={{ scale: [1, 1.3, 1], opacity: [1, 0.6, 1] }}
              transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
              className="w-2 h-2 rounded-full bg-accent-green"
            />
            <span className="text-[11px] font-semibold text-accent-green tracking-wide">Connected to StreamSync Engine</span>
          </div>
          <div className="flex items-center gap-4 text-[10px] text-slate-500 font-mono">
            <span>p99: <span className="text-accent-green">145ms</span></span>
            <span>uptime: <span className="text-accent-green">99.97%</span></span>
            <span className="hidden sm:inline">Redis lag: <span className="text-accent-green">12ms</span></span>
          </div>
        </div>
      </div>
    </footer>
  )
}
