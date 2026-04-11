import { Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Trash2, ShoppingCart, ArrowLeft, Package } from 'lucide-react'
import useCart from '../hooks/useCart'
import { EmptyState } from '../components/Loader'

export default function Cart() {
  const { items, totalItems, totalPrice, removeFromCart, updateQty, clearCart } = useCart()

  if (items.length === 0) {
    return (
      <div className="bg-[#F0F4F0] min-h-[100vh] flex flex-col items-center justify-center py-20 px-4">
        <div className="w-16 h-16 rounded-2xl bg-[#E4EDE4] border border-[#C8D9C8] flex items-center justify-center mb-4 shadow-sm">
          <Package size={28} className="text-[#5A7A5A]" />
        </div>
        <p className="text-[#1A2E1A] font-bold text-xl mb-1">Your cart is empty</p>
        <p className="text-[#5A7A5A] text-sm max-w-xs text-center mb-6">Browse our live-priced products and add something.</p>
        <Link to="/products" className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-[#F0F4F0] bg-[#2D6A2D] hover:bg-[#1A2E1A] transition-colors shadow-md">
          <Package size={15} /> Browse Products
        </Link>
      </div>
    )
  }

  const shipping = totalPrice > 100 ? 0 : 9.99
  const tax      = totalPrice * 0.08
  const total    = totalPrice + shipping + tax

  return (
    <div className="bg-[#F0F4F0] min-h-[100vh] text-[#1A2E1A]">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-6">
        <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-[#1A2E1A]">Cart</h1>
          <p className="text-[#5A7A5A] font-medium text-sm mt-1">{totalItems} item{totalItems !== 1 ? 's' : ''} — prices updated live</p>
        </div>
        <Link to="/products" className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-[#5A7A5A] hover:text-[#1A2E1A] hover:bg-[#C8D9C8]/40 transition-colors text-sm font-semibold"><ArrowLeft size={14} /> Continue Shopping</Link>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Items */}
        <div className="lg:col-span-2 space-y-3">
          <AnimatePresence>
            {items.map(item => (
              <motion.div
                key={item.id}
                layout
                initial={{ opacity: 0, x: -16 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 16, height: 0 }}
                transition={{ duration: 0.25 }}
                className="bg-[#E4EDE4] border border-[#C8D9C8] rounded-2xl p-6 shadow-md flex gap-4 items-center"
              >
                {/* Thumbnail */}
                <div className="w-20 h-20 rounded-xl bg-[#F0F4F0] border border-[#C8D9C8] overflow-hidden flex-shrink-0 flex items-center justify-center">
                  {item.image
                    ? <img src={item.image} alt={item.name} className="w-full h-full object-cover" />
                    : <ShoppingCart size={24} className="text-[#5A7A5A]" />
                  }
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0 space-y-1">
                  <Link to={`/products/${item.id}`}>
                    <p className="font-bold text-sm text-[#1A2E1A] hover:text-[#2D6A2D] transition-colors line-clamp-1">{item.name}</p>
                  </Link>
                  <p className="text-xs font-semibold uppercase tracking-wider text-[#5A7A5A]">{item.category}</p>
                  <p className="text-[#2D6A2D] font-bold font-mono">${(item.price * item.qty).toFixed(2)}</p>
                </div>

                {/* Qty controls */}
                <div className="flex items-center gap-2 flex-shrink-0">
                  <div className="flex items-center bg-[#F0F4F0] border border-[#C8D9C8] rounded-xl overflow-hidden shadow-sm">
                    <button
                      onClick={() => updateQty(item.id, item.qty - 1)}
                      className="px-3.5 py-2 text-[#5A7A5A] hover:text-[#1A2E1A] hover:bg-[#C8D9C8]/50 transition-colors font-bold text-sm"
                    >−</button>
                    <span className="px-2 text-[#1A2E1A] text-sm font-mono font-bold">{item.qty}</span>
                    <button
                      onClick={() => updateQty(item.id, item.qty + 1)}
                      className="px-3.5 py-2 text-[#5A7A5A] hover:text-[#1A2E1A] hover:bg-[#C8D9C8]/50 transition-colors font-bold text-sm"
                    >+</button>
                  </div>

                  <button
                    onClick={() => removeFromCart(item.id)}
                    className="p-2.5 text-[#5A7A5A] hover:text-[#1A2E1A] transition-colors rounded-xl hover:bg-[#C8D9C8]/50"
                    aria-label="Remove"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          <button onClick={clearCart} className="text-xs font-semibold text-[#5A7A5A] hover:text-[#1A2E1A] transition-colors flex items-center gap-1.5 pt-2">
            <Trash2 size={12} /> Clear cart
          </button>
        </div>

        {/* Order Summary */}
        <div className="bg-[#E4EDE4] border border-[#C8D9C8] rounded-2xl p-6 shadow-md h-fit space-y-5 sticky top-20">
          <h2 className="font-bold text-xl text-[#1A2E1A]">Order Summary</h2>

          <div className="space-y-3.5 text-sm">
            <div className="flex justify-between text-[#5A7A5A] font-medium">
              <span>Subtotal ({totalItems} items)</span>
              <span className="text-[#1A2E1A] font-mono font-bold">${totalPrice.toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-[#5A7A5A] font-medium">
              <span>Shipping</span>
              <span className={shipping === 0 ? 'text-[#2D6A2D] font-bold' : 'text-[#1A2E1A] font-mono font-bold'}>
                {shipping === 0 ? 'FREE' : `$${shipping.toFixed(2)}`}
              </span>
            </div>
            <div className="flex justify-between text-[#5A7A5A] font-medium">
              <span>Tax (8%)</span>
              <span className="text-[#1A2E1A] font-mono font-bold">${tax.toFixed(2)}</span>
            </div>
          </div>

          <div className="border-t border-[#C8D9C8] pt-4 flex justify-between font-black text-lg text-[#1A2E1A]">
            <span>Total</span>
            <span className="text-[#2D6A2D] font-mono text-xl">${total.toFixed(2)}</span>
          </div>

          {shipping === 0 && (
            <p className="text-xs font-semibold text-[#2D6A2D] bg-[#2D6A2D]/10 border border-[#2D6A2D]/20 rounded-xl px-3.5 py-3">
              🎉 You qualify for free shipping!
            </p>
          )}
          {shipping > 0 && (
            <p className="text-xs font-semibold text-[#5A7A5A]">
              Spend ${(100 - totalPrice).toFixed(2)} more for free shipping.
            </p>
          )}

          <motion.button
            whileTap={{ scale: 0.97 }}
            className="w-full flex items-center justify-center gap-2 px-5 py-3.5 rounded-xl font-bold text-[#F0F4F0] bg-[#2D6A2D] hover:bg-[#1A2E1A] active:scale-95 transition-all text-base shadow-md mt-2"
          >
            Proceed to Checkout
          </motion.button>
        </div>
      </div>
      </div>
    </div>
  )
}
