import { useEffect, useState, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ShoppingCart, Star, StarHalf, Monitor, Headphones, Laptop, Coffee } from 'lucide-react'
import useCart from '../hooks/useCart'
import { PageLoader, ErrorState } from '../components/Loader'
import { fetchProductById, captureView, captureAddToCart } from '../services/api'

const SESSION_ID = `sess_${Math.random().toString(36).slice(2, 10)}`

export default function ProductDetails() {
  const { id } = useParams()
  const { addToCart } = useCart()
  const [product, setProduct] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)
  const [price, setPrice]     = useState(null)
  const [qty, setQty]         = useState(1)
  const [added, setAdded]     = useState(false)

  useEffect(() => {
    setLoading(true)
    fetchProductById(id)
      .then(p => {
        setProduct(p)
        setPrice(p.price)
        captureView(id, SESSION_ID).catch(() => {})
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [id])

  const handleAddToCart = () => {
    if (!product) return
    addToCart({ ...product, price }, qty)
    captureAddToCart(id, SESSION_ID, qty).catch(() => {})
    setAdded(true)
    setTimeout(() => setAdded(false), 2000)
  }

  if (loading) return <PageLoader />
  if (error)   return <ErrorState message={error} />
  if (!product) return null

  // Layout placeholders mimicking the provided screenshot structure
  const images = [
    product.image || null,
    product.image || null,
    product.image || null,
    product.image || null,
  ]

  const listPrice = Math.round(price * 1.15)
  const discount = listPrice - price

  return (
    <div className="bg-[#F0F4F0] min-h-screen text-[#1A2E1A] pt-28 pb-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Main Product Stage */}
        <div className="flex flex-col lg:flex-row gap-8 lg:gap-12">
          
          {/* Left Column: Image Gallery */}
          <div className="lg:w-5/12 flex flex-col-reverse sm:flex-row gap-4">
            {/* Thumbnails */}
            <div className="flex sm:flex-col gap-3 overflow-x-auto sm:overflow-visible w-full sm:w-[70px] shrink-0 pb-2 sm:pb-0 no-scrollbar">
              {['A','B','C','D','E'].map((letter, i) => (
                <div key={i} className={`w-[60px] h-[60px] sm:w-[70px] sm:h-[70px] border rounded-xl cursor-pointer overflow-hidden flex items-center justify-center shrink-0 transition-all ${i===0 ? 'border-[#2D6A2D] ring-1 ring-[#2D6A2D] bg-[#E4EDE4]' : 'border-[#C8D9C8] hover:border-[#5A7A5A] bg-[#F0F4F0]'}`}>
                   {product.image ? (
                     <img src={product.image} alt="thumb" className="w-[80%] h-[80%] object-contain mix-blend-multiply" />
                   ) : (
                     <Monitor size={24} className="text-[#5A7A5A]" />
                   )}
                </div>
              ))}
            </div>
            
            {/* Main Image */}
            <div className="flex-1 flex items-start justify-center bg-[#E4EDE4] rounded-2xl border border-[#C8D9C8] p-6 lg:p-10 shrink-0 min-h-[300px]">
               {product.image ? (
                 <img src={product.image} className="w-full h-auto object-contain max-h-[400px] mix-blend-multiply" alt={product.name}/>
               ) : (
                 <Monitor size={100} className="text-[#C8D9C8]" />
               )}
            </div>
          </div>

          {/* Middle Column: Title & Bullets */}
          <div className="lg:w-4/12 flex flex-col gap-4">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold leading-snug text-[#1A2E1A]">
                {product.name}
              </h1>
              
              <div className="flex items-center gap-4 mt-3 border-b border-[#C8D9C8] pb-4">
                 <div className="flex items-center gap-1.5">
                   <span className="text-[#2D6A2D] font-bold text-sm hover:underline cursor-pointer flex items-center mr-1">
                      {product.rating || 4.8}
                   </span>
                   {[1,2,3,4,5].map(s => (
                     <Star key={s} size={15} className={s <= Math.round(product.rating || 4) ? 'text-[#2D6A2D] fill-[#2D6A2D]' : 'text-[#C8D9C8]'} />
                   ))}
                   <span className="text-[#5A7A5A] text-sm ml-2 hover:underline cursor-pointer font-medium">({product.reviewCount || '1,234'} reviews)</span>
                 </div>
              </div>
            </div>

            <div className="mt-2">
               <p className="font-bold text-[15px] mb-3 text-[#1A2E1A] leading-snug">Optimized in Real-Time | 10M+ SKU Catalogue | &lt; 200ms Repricing | 99.97% Uptime Guarantees.</p>
               
               <ul className="list-disc pl-5 space-y-2 text-sm font-medium text-[#5A7A5A]">
                 <li>Dynamic Pricing. (Example pricing based on a {product.name})</li>
                 <li><span className="font-bold text-[#1A2E1A]">{product.name}</span> | Optimized in Real-Time - {product.category}</li>
                 <li><span className="font-bold text-[#1A2E1A]">10M+ SKU Catalogue</span> | &lt; 200ms | Repricing updates.</li>
                 <li>Wireless Noise-Canceling Headphone categories.</li>
                 <li>Redimensionable tracking and compute running.</li>
                 <li><span className="font-bold text-[#1A2E1A]">99.97% Uptime Guarantee.</span> Platform updates with invent</li>
                 <li><span className="font-bold text-[#1A2E1A]">42K Messages.</span> Compatibility, formats and text.</li>
               </ul>
            </div>
          </div>

          {/* Right Column: Checkout Box */}
          <div className="lg:w-3/12">
            <div className="bg-[#E4EDE4] border border-[#C8D9C8] rounded-2xl p-6 flex flex-col gap-4 text-sm shadow-md sticky top-24">
              
              {/* Pricing */}
              <div className="flex flex-col gap-1">
                 <div className="flex items-baseline gap-2">
                   <span className="text-[#5A7A5A] font-medium">List Price:</span>
                   <span className="text-[#5A7A5A] line-through">${listPrice.toFixed(2)}</span>
                 </div>
                 <div className="flex flex-wrap items-baseline gap-2">
                   <span className="text-[#5A7A5A] font-medium">Our Price:</span>
                   <span className="text-3xl font-black text-[#2D6A2D] font-mono">${price?.toFixed(2)}</span>
                 </div>
                 <div className="text-[#5A7A5A] text-xs font-semibold">
                   (${discount.toFixed(2)} off)
                 </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-col gap-3 mt-2">
                 <button 
                  onClick={handleAddToCart}
                  className={`w-full flex items-center justify-center gap-2 rounded-xl py-3 shadow-sm font-bold text-base transition-colors ${added ? 'bg-[#5A7A5A] text-[#F0F4F0]' : 'bg-[#2D6A2D] hover:bg-[#1A2E1A] text-[#F0F4F0]'}`}
                 >
                   <ShoppingCart size={16} />
                   {added ? 'Added!' : 'Add to Cart'}
                 </button>
                 <button 
                  className="w-full flex items-center justify-center gap-2 rounded-xl py-3 shadow-sm font-bold text-[#2D6A2D] bg-transparent border-2 border-[#2D6A2D]/40 hover:border-[#2D6A2D] hover:bg-[#2D6A2D]/10 transition-colors"
                 >
                   Buy Now
                 </button>
              </div>

              <div className="space-y-2 mt-2 border-t border-[#C8D9C8] pt-4">
                 <p className="text-[#2D6A2D] hover:underline cursor-pointer font-bold">FREE Delivery</p>
                 <p className="text-lg text-[#2D6A2D] font-black leading-none">In Stock</p>
                 <div className="flex flex-col text-[#5A7A5A] mt-2 space-y-1 text-xs font-medium">
                   <div className="flex justify-between"><span className="w-16">Sold by:</span> <span className="text-[#1A2E1A] font-bold flex-1">StreamSync</span></div>
                   <div className="flex justify-between"><span className="w-16">Returns:</span> <span className="text-[#2D6A2D] hover:underline flex-1">Eligible</span></div>
                 </div>
              </div>

              <div className="mt-2 border border-[#C8D9C8] rounded-xl shadow-sm bg-[#F0F4F0] hover:bg-[#C8D9C8]/40 cursor-pointer overflow-hidden transition-colors">
                 <select 
                   className="w-full bg-transparent px-4 py-2.5 outline-none cursor-pointer font-semibold text-[#1A2E1A]"
                   value={qty}
                   onChange={e => setQty(Number(e.target.value))}
                 >
                   {[1,2,3,4,5,6,7,8,9,10].map(n => (
                     <option key={n} value={n}>Quantity: {n}</option>
                   ))}
                 </select>
              </div>
            </div>
          </div>

        </div>

        <hr className="my-12 border-[#C8D9C8]" />

        {/* Lower Section Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
           
           {/* Detailed Features */}
           <div className="lg:col-span-4">
             <h3 className="text-xl font-bold mb-5 text-[#1A2E1A]">Product Details & Features</h3>
             <p className="text-sm leading-relaxed mb-5 text-[#5A7A5A] font-medium">
               Experience a curated shopping environment where every price of real-time data is optimized in real-time. <span className="font-bold text-[#1A2E1A]">10M+ SKUs repriced every 200ms.</span>
             </p>
             <ul className="list-disc pl-5 space-y-3 text-sm text-[#5A7A5A] font-medium">
               <li><span className="font-bold text-[#1A2E1A]">Optimized in Real-Time</span> | <span className="font-bold text-[#1A2E1A]">10M+ SKU Catalogue</span> | <span className="font-bold text-[#1A2E1A]">&lt; 200ms Repricing</span> | <span className="font-bold text-[#1A2E1A]">99.97% Uptime Guarantee</span>. Integrated and process refinement in unknown answers.</li>
               <li><span className="font-bold text-[#1A2E1A]">Optimized brand</span> | Wireless, rates perfectly monitors and part new distances.</li>
               <li>Comes sample multiple alignment, among uncommon insurance and nonconnectives-cavanes active test-connect.</li>
               <li><span className="font-bold text-[#1A2E1A]">High-Quality</span> investment taxonomy system, with the best unvisionary chances and limited data technologies to users.</li>
               <li>Optimize all corners, with the latency for non codes.</li>
               <li>Sample ultimate <span className="font-bold text-[#1A2E1A]">Wireless Noise-Cancel Headphone ANC</span> for all noise-canceling product.</li>
             </ul>
           </div>

           {/* Reviews */}
           <div className="lg:col-span-4">
             <h3 className="text-xl font-bold mb-4 text-[#1A2E1A]">Customer Reviews</h3>
             <div className="flex items-center gap-2 mb-2">
               <div className="flex gap-0.5">
                 {[1,2,3,4,5].map(s => (
                   <Star key={s} size={20} className={s <= Math.round(product.rating || 4) ? 'text-[#2D6A2D] fill-[#2D6A2D]' : 'text-[#C8D9C8]'} />
                 ))}
               </div>
               <span className="text-lg font-bold text-[#1A2E1A]">{product.rating || 4.8} out of 5</span>
             </div>
             <p className="text-[#5A7A5A] font-medium text-sm mb-6 hover:underline cursor-pointer">177 global ratings</p>
             
             {/* Progress bars */}
             <div className="space-y-4 mb-8">
               {[
                 {star: 5, pct: 53}, {star: 4, pct: 33}, {star: 3, pct: 10}, {star: 2, pct: 10}, {star: 1, pct: 7}
               ].map(({star, pct}) => (
                 <div key={star} className="flex items-center gap-3 text-sm text-[#5A7A5A] font-semibold whitespace-nowrap">
                   <span className="w-12 hover:text-[#1A2E1A] cursor-pointer">{star} star</span>
                   <div className="flex-1 h-3.5 bg-[#E4EDE4] rounded-full overflow-hidden relative">
                     <div className="h-full bg-[#2D6A2D] rounded-full" style={{width: `${pct}%`}}/>
                   </div>
                   <span className="w-9 text-right hover:text-[#1A2E1A] cursor-pointer">{pct}%</span>
                 </div>
               ))}
             </div>
             
             <button className="border-2 border-[#2D6A2D]/40 text-[#2D6A2D] rounded-xl px-6 py-2.5 text-sm font-bold bg-transparent hover:border-[#2D6A2D] hover:bg-[#2D6A2D]/10 transition-colors w-full sm:w-auto">
               Write a product review
             </button>

             {/* Review Items */}
             <div className="mt-10 space-y-8">
                {[1,2].map(i => (
                  <div key={i} className="space-y-2 bg-[#E4EDE4] p-5 rounded-2xl border border-[#C8D9C8]">
                     <div className="flex gap-1">
                       <Star size={16} className="text-[#2D6A2D] fill-[#2D6A2D]"/><Star size={16} className="text-[#2D6A2D] fill-[#2D6A2D]"/><Star size={16} className="text-[#2D6A2D] fill-[#2D6A2D]"/><Star size={16} className="text-[#2D6A2D] fill-[#2D6A2D]"/><Star size={16} className="text-[#2D6A2D] fill-[#2D6A2D]"/>
                     </div>
                     <p className="font-bold text-base text-[#1A2E1A]">Sample review title</p>
                     <p className="text-sm text-[#5A7A5A] font-medium leading-relaxed">
                       I am someone the quality been amazing on and creating completely products to any amount your center testing, and wants to a lesser document contribution of entries a professionals.
                     </p>
                  </div>
                ))}
             </div>
           </div>

           {/* Carousel blocks */}
           <div className="lg:col-span-4">
             {/* Related */}
             <h3 className="text-xl font-bold mb-5 text-[#1A2E1A]">Related Products</h3>
             <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-2 xl:grid-cols-4 gap-4 mb-10">
                {[
                  {n: 'Surface Pro AI', p: 18.00},
                  {n: 'Pro Wireless ANC', p: 18.00},
                  {n: 'Studio Laptop X1', p: 15.00},
                  {n: 'Studio Monitor X', p: 13.00}
                ].map((item, i) => (
                  <div key={i} className="flex flex-col gap-1.5 relative group cursor-pointer">
                    <div className="aspect-square bg-[#E4EDE4] rounded-xl border border-[#C8D9C8] flex items-center justify-center p-2 mb-1 group-hover:border-[#5A7A5A]/50 transition-colors">
                      <img src={`https://picsum.photos/seed/${i+10}/80/80`} className="w-full h-full object-cover rounded-lg opacity-90 mix-blend-multiply" alt="rel" />
                    </div>
                    <p className="text-[#5A7A5A] font-semibold text-xs leading-tight line-clamp-2 group-hover:text-[#1A2E1A]">{item.n}</p>
                    <div className="flex items-center text-[#2D6A2D]"><Star size={10} className="fill-[#2D6A2D]" /><Star size={10} className="fill-[#2D6A2D]" /><Star size={10} className="fill-[#2D6A2D]" /><span className="text-[#5A7A5A] ml-1.5 font-bold text-[10px]">4</span></div>
                    <p className="text-[#2D6A2D] font-black text-sm">${item.p.toFixed(2)}</p>
                  </div>
                ))}
             </div>

             {/* FBT */}
             <h3 className="text-xl font-bold mb-5 text-[#1A2E1A]">Frequently Bought Together</h3>
             <div className="flex flex-wrap gap-3 items-center mb-6">
                {[1,2,3].map((i, idx) => (
                  <div key={i} className="flex items-center gap-3">
                    <div className="w-[80px] h-[80px] bg-[#E4EDE4] rounded-xl border border-[#C8D9C8] flex items-center justify-center overflow-hidden">
                       <img src={`https://picsum.photos/seed/${i+20}/64/64`} className="w-full h-full object-cover opacity-90 mix-blend-multiply" alt="fbt" />
                    </div>
                    {idx < 2 && <span className="text-[#5A7A5A] font-black text-2xl px-1">+</span>}
                  </div>
                ))}
             </div>
             
             <button className="bg-[#2D6A2D] hover:bg-[#1A2E1A] text-[#F0F4F0] rounded-xl px-6 py-3 font-bold shadow-md transition-colors w-full sm:w-auto">
               Add all three to Cart
             </button>
           </div>
           
        </div>
      </div>
    </div>
  )
}
