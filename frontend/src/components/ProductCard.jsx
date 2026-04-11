import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { ShoppingCart, TrendingUp, Zap, Eye } from 'lucide-react'
import useCart from '../hooks/useCart'
import { captureView, captureAddToCart } from '../services/api'

// Generates a stable session ID per browser tab
const SESSION_ID = `sess_${Math.random().toString(36).slice(2, 10)}`

export default function ProductCard({ product }) {
  const { addToCart }   = useCart()
  const [price, setPrice]         = useState(product.price)
  const [prevPrice, setPrevPrice] = useState(product.price)
  const [pulsing, setPulsing]     = useState(false)
  const [added, setAdded]         = useState(false)

  // Detect external price updates
  useEffect(() => {
    if (product.price !== prevPrice) {
      setPrevPrice(price)
      setPrice(product.price)
      setPulsing(true)
      const t = setTimeout(() => setPulsing(false), 2400)
      return () => clearTimeout(t)
    }
  }, [product.price])

  // Signal capture: VIEW
  useEffect(() => {
    captureView(product.id, SESSION_ID).catch(() => {})
  }, [product.id])

  const handleAddToCart = useCallback(() => {
    addToCart(product)
    captureAddToCart(product.id, SESSION_ID).catch(() => {})
    setAdded(true)
    setTimeout(() => setAdded(false), 1800)
  }, [product, addToCart])

  const isDemandSpike = product.demandVelocity > 75  // velocity 0-100
  const priceDirection = product.price > prevPrice ? 'up' : product.price < prevPrice ? 'down' : null

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.96 }}
      transition={{ duration: 0.3 }}
      className="bg-[#E4EDE4] border border-[#C8D9C8] rounded-2xl p-5 shadow-sm hover:shadow-md hover:border-[#5A7A5A]/30 transition-all duration-300 group flex flex-col overflow-hidden relative"
    >
      {/* Demand Spike Badge */}
      <AnimatePresence>
        {isDemandSpike && (
          <motion.div
            initial={{ opacity: 0, scale: 0.7, y: -8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.7 }}
            className="absolute top-3 left-3 z-10 badge-red flex items-center gap-1 shadow-lg"
          >
            <Zap size={10} fill="currentColor" />
            DEMAND SPIKE
          </motion.div>
        )}
      </AnimatePresence>

      {/* Product Image */}
      <Link to={`/products/${product.id}`} className="block">
        <div className="relative overflow-hidden rounded-xl bg-[#F0F4F0] border border-[#C8D9C8] h-48 flex items-center justify-center mb-4 group-hover:ring-1 group-hover:ring-[#2D6A2D]/30 transition-all duration-300 shadow-inner">
          {product.image ? (
            <img
              src={product.image}
              alt={product.name}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
              loading="lazy"
            />
          ) : (
            <div className="flex flex-col items-center gap-2 text-[#5A7A5A]">
              <ShoppingCart size={32} />
              <span className="text-xs font-semibold">No Image</span>
            </div>
          )}
          {/* view overlay */}
          <div className="absolute inset-0 bg-[#1A2E1A]/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2 backdrop-blur-sm">
            <span className="text-sm font-bold text-[#F0F4F0] flex items-center gap-1.5">
              <Eye size={14} /> View Details
            </span>
          </div>
        </div>
      </Link>

      {/* Info */}
      <div className="flex-1 flex flex-col gap-2">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-widest text-[#5A7A5A] mb-1">
            {product.category || 'General'}
          </p>
          <Link to={`/products/${product.id}`}>
            <h3 className="font-bold text-[#1A2E1A] text-sm leading-snug line-clamp-2 hover:text-[#2D6A2D] transition-colors">
              {product.name}
            </h3>
          </Link>
        </div>

        {/* Rating */}
        {product.rating != null && (
          <div className="flex items-center gap-1.5 mt-0.5">
            <div className="flex gap-0.5">
              {[1,2,3,4,5].map((s) => (
                <span key={s} className={`text-[10px] ${s <= Math.round(product.rating) ? 'text-warn-amber' : 'text-[#C8D9C8]'}`}>★</span>
              ))}
            </div>
            <span className="text-[10px] font-medium text-[#5A7A5A]">({product.reviewCount ?? 0})</span>
          </div>
        )}

        {/* Demand velocity bar */}
        {product.demandVelocity != null && (
          <div className="space-y-1 mt-1">
            <div className="flex items-center justify-between text-[10px]">
              <span className="text-[#5A7A5A] font-semibold flex items-center gap-1"><TrendingUp size={9} /> Demand</span>
              <span className={isDemandSpike ? 'text-warn-red font-bold' : 'text-[#5A7A5A] font-bold'}>
                {product.demandVelocity}%
              </span>
            </div>
            <div className="h-1 bg-[#C8D9C8] rounded-full overflow-hidden">
              <motion.div
                className={`h-full rounded-full ${isDemandSpike ? 'bg-warn-red' : 'bg-[#2D6A2D]'}`}
                initial={{ width: 0 }}
                animate={{ width: `${product.demandVelocity}%` }}
                transition={{ duration: 0.8, ease: 'easeOut' }}
              />
            </div>
          </div>
        )}

        {/* Price + CTA */}
        <div className="flex items-center justify-between mt-auto pt-4 border-t border-[#C8D9C8]">
          <motion.div
            key={price}
            animate={pulsing ? { scale: [1, 1.06, 1] } : {}}
            transition={{ duration: 0.4 }}
            className={`rounded-lg transition-all duration-300 ${pulsing ? 'price-pulse' : ''}`}
          >
            <span className="text-xl font-black text-[#2D6A2D] font-mono tracking-tight">
              ${typeof price === 'number' ? price.toFixed(2) : price}
            </span>
            {priceDirection && (
              <span className={`ml-1.5 text-[10px] font-bold ${priceDirection === 'up' ? 'text-warn-red' : 'text-[#2D6A2D]'}`}>
                {priceDirection === 'up' ? '▲' : '▼'}
              </span>
            )}
          </motion.div>

          <motion.button
            whileTap={{ scale: 0.93 }}
            onClick={handleAddToCart}
            className={`inline-flex items-center gap-2 px-3 py-2 rounded-lg font-bold text-[#F0F4F0] text-xs shadow-sm transition-colors border ${added ? 'bg-[#5A7A5A] border-[#5A7A5A]' : 'bg-[#2D6A2D] border-[#2D6A2D] hover:bg-[#1A2E1A] hover:border-[#1A2E1A]'}`}
          >
            <ShoppingCart size={13} />
            {added ? 'Added!' : 'Add to Cart'}
          </motion.button>
        </div>
      </div>
    </motion.div>
  )
}
