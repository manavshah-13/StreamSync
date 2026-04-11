import { Link, NavLink, useNavigate } from 'react-router-dom'
import { ShoppingCart, Zap, User, Search, Menu, X, Mic } from 'lucide-react'
import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import useCart from '../hooks/useCart'

const navLinks = [
  { to: '/products',  label: 'Shop' },
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/cart',      label: 'Cart' },
]

export default function Navbar() {
  const { totalItems } = useCart()
  const [scrolled, setScrolled] = useState(false)
  const [open, setOpen] = useState(false)
  const [searchFocused, setSearchFocused] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 40)
    window.addEventListener('scroll', handler, { passive: true })
    return () => window.removeEventListener('scroll', handler)
  }, [])

  return (
    <header
      className="fixed top-0 inset-x-0 z-50 bg-[#0D0D0D] border-b border-white/8 shadow-xl shadow-black/40"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center gap-4">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 shrink-0 group">
          <div className="w-8 h-8 rounded-lg bg-accent-green flex items-center justify-center shadow-lg shadow-accent-green/30 group-hover:scale-110 transition-transform">
            <Zap size={15} className="text-navy-950" fill="currentColor" />
          </div>
          <span className="font-extrabold text-lg tracking-tight text-white">
            Stream<span className="text-accent-green">Sync</span>
          </span>
        </Link>

        {/* Search */}
        <div className={`hidden md:flex flex-1 max-w-xl mx-auto relative transition-all duration-300 ${searchFocused ? 'max-w-2xl' : ''}`}>
          <div className={`w-full flex items-center gap-2 rounded-2xl border px-4 py-2.5 transition-all duration-300 ${
            searchFocused
              ? 'bg-white/8 border-[#16A34A]/60 shadow-lg shadow-[#16A34A]/10'
              : 'bg-white/5 border-white/10 hover:border-white/20'
          }`}>
            <Search size={14} className="text-slate-400 shrink-0" />
            <input
              onFocus={() => setSearchFocused(true)}
              onBlur={() => setSearchFocused(false)}
              placeholder="Search products, brands, categories…"
              className="flex-1 bg-transparent text-sm text-white placeholder-slate-500 outline-none"
            />
            <div className="flex items-center gap-1.5 shrink-0">
              <span className="text-[9px] font-semibold text-[#16A34A] bg-[#16A34A]/10 border border-[#16A34A]/30 px-1.5 py-0.5 rounded-md">AI</span>
              <Mic size={13} className="text-slate-500 hover:text-[#16A34A] transition-colors cursor-pointer" />
            </div>
          </div>
        </div>

        {/* Desktop right */}
        <nav className="hidden md:flex items-center gap-1 shrink-0">
          {navLinks.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  isActive ? 'text-[#16A34A] bg-[#16A34A]/10' : 'text-slate-300 hover:text-white hover:bg-white/5'
                }`
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="flex items-center gap-2 ml-auto md:ml-0 shrink-0">
          <button className="p-2.5 rounded-xl text-slate-300 hover:text-white hover:bg-white/8 transition-all" aria-label="Profile">
            <User size={18} />
          </button>
          <button
            onClick={() => navigate('/cart')}
            className="relative p-2.5 rounded-xl text-slate-300 hover:text-white hover:bg-white/8 transition-all"
            aria-label="Cart"
          >
            <ShoppingCart size={18} />
            <AnimatePresence>
              {totalItems > 0 && (
                <motion.span
                  key={totalItems}
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  exit={{ scale: 0 }}
                  className="absolute -top-0.5 -right-0.5 w-4.5 h-4.5 min-w-[18px] text-[10px] font-bold rounded-full bg-[#16A34A] text-white flex items-center justify-center px-1"
                >
                  {totalItems}
                </motion.span>
              )}
            </AnimatePresence>
          </button>
          <button
            className="md:hidden p-2.5 rounded-xl text-slate-300 hover:text-white hover:bg-white/8 transition-all"
            onClick={() => setOpen(v => !v)}
          >
            {open ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden bg-[#05070A]/98 border-t border-white/8 overflow-hidden"
          >
            <div className="px-4 py-3 space-y-1">
              <div className="flex items-center gap-2 bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 mb-3">
                <Search size={14} className="text-slate-400" />
                <input placeholder="Search…" className="flex-1 bg-transparent text-sm text-white placeholder-slate-500 outline-none" />
              </div>
              {navLinks.map(({ to, label }) => (
                <NavLink key={to} to={to} onClick={() => setOpen(false)}
                  className={({ isActive }) =>
                    `block px-4 py-3 rounded-xl text-sm font-medium transition-all ${isActive ? 'text-accent-green bg-accent-green/10' : 'text-slate-300 hover:text-white hover:bg-white/5'}`
                  }
                >{label}</NavLink>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  )
}
