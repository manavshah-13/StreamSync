'use client';

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { motion } from 'framer-motion';

interface Product {
  id: string;
  name: string;
  category?: string;
  description?: string;
  image?: string;
  base_price?: number;
  original_price?: number;
  current_price?: number;
  price_change_percentage?: number;
  change_reason?: string;
  rating?: number;
  review_count?: number;
}

export default function ProductDetailPage() {
  const params = useParams();
  const id = params?.id as string;

  const [product, setProduct] = useState<Product | null>(null);
  const [recommendations, setRecommendations] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [added, setAdded] = useState(false);

  useEffect(() => {
    if (!id) return;

    const getUserId = () => {
      if (typeof window === 'undefined') return 'guest';
      return localStorage.getItem('user_id') || 'guest';
    };

    const getSessionId = () => {
      if (typeof window === 'undefined') return 'anon';
      let sid = localStorage.getItem('session_id') || localStorage.getItem('streamsync_session_id');
      if (!sid) {
        sid = `sess_${Math.random().toString(36).slice(2, 10)}_${Date.now().toString(36)}`;
        localStorage.setItem('streamsync_session_id', sid);
      }
      return sid;
    };

    const loadProductData = async () => {
      try {
        setLoading(true);
        // 1. Fetch Product details
        const response = await fetch(`/api/v1/products/${id}`);
        if (!response.ok) {
          throw new Error('Product not found');
        }
        const data = await response.json();
        setProduct(data);

        const userId = getUserId();
        const sessionId = getSessionId();

        // 2. Non-blocking call to log 'view' event
        fetch('/api/v1/events', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            user_id: userId,
            session_id: sessionId,
            event_type: 'view',
            sku: id,
            metadata: {},
          }),
        }).catch(err => console.error('Failed to log event:', err));

        // 3. Fetch Personalized recommendations
        try {
          const recsRes = await fetch(`/api/v1/recommendations/personalized?session_id=${sessionId}&user_id=${userId}`);
          if (recsRes.ok) {
            const recsData = await recsRes.json();
            // Filter out current product if returned
            const filteredRecs = (recsData.products || []).filter((p: any) => p.id !== id).slice(0, 4);
            setRecommendations(filteredRecs);
          }
        } catch (recErr) {
          console.error('Failed to load recommendations:', recErr);
        }

      } catch (err: any) {
        console.error('Error loading product details:', err);
        setError(err.message || 'Product could not be loaded.');
      } finally {
        setLoading(false);
      }
    };

    loadProductData();
  }, [id]);

  const handleAddToCart = () => {
    setAdded(true);
    setTimeout(() => setAdded(false), 2000);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0B1020] flex items-center justify-center text-[#F9FAFB]">
        <div className="flex flex-col items-center space-y-4">
          <div className="w-12 h-12 rounded-full border-4 border-[#6D5DFC]/20 border-t-[#6D5DFC] animate-spin" />
          <p className="text-sm font-semibold tracking-wider text-[#9CA3AF]">Loading Dynamic Product Suite...</p>
        </div>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="min-h-screen bg-[#0B1020] text-[#F9FAFB] flex flex-col items-center justify-center p-6 text-center space-y-4">
        <div className="w-16 h-16 rounded-full bg-[#EF4444]/20 border border-[#EF4444]/40 flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#EF4444" strokeWidth="2.5">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
        </div>
        <h2 className="text-2xl font-bold">Failed to load product</h2>
        <p className="text-[#9CA3AF] text-sm max-w-sm">{error || 'The requested product detail view does not exist.'}</p>
        <a href="/products" className="px-5 py-2.5 rounded-xl font-bold bg-[#6D5DFC] text-[#0B1020] hover:opacity-95 transition-opacity">
          Back to Catalog
        </a>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full bg-[#0B1020] text-[#F9FAFB] px-6 py-12 md:px-12 lg:px-24">
      <div className="max-w-7xl mx-auto space-y-16">
        
        {/* Navigation Breadcrumb / Link */}
        <div className="text-left">
          <a href="/products" className="inline-flex items-center gap-2 text-sm text-[#9CA3AF] hover:text-[#6D5DFC] transition-colors font-medium">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="19" y1="12" x2="5" y2="12" />
              <polyline points="12 19 5 12 12 5" />
            </svg>
            Back to Products Catalog
          </a>
        </div>

        {/* Main Details Panel (Two-Column Layout) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-start">
          
          {/* Left Column: Large Product Image with a Gradient Border */}
          <div className="lg:col-span-6 flex justify-center">
            <div className="p-[2px] bg-gradient-to-tr from-[#6D5DFC] to-[#22D3EE] rounded-3xl w-full max-w-lg aspect-square overflow-hidden shadow-2xl">
              <div className="w-full h-full bg-[#111827]/90 backdrop-blur-md flex items-center justify-center p-8 rounded-[22px]">
                {product.image ? (
                  <img
                    src={product.image}
                    alt={product.name}
                    className="w-full h-full object-contain rounded-2xl"
                  />
                ) : (
                  <svg className="w-24 h-24 text-[#9CA3AF]/20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                  </svg>
                )}
              </div>
            </div>
          </div>

          {/* Right Column: Full Text Details, Live Pricing Structures & Add to Cart */}
          <div className="lg:col-span-6 space-y-6 text-left">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-[#22D3EE] px-3 py-1.5 rounded-full bg-[#22D3EE]/10 border border-[#22D3EE]/25">
                {product.category || 'General'}
              </span>
              <h1 className="text-4xl font-extrabold tracking-tight text-[#F9FAFB] mt-4">
                {product.name}
              </h1>
            </div>

            <p className="text-[#9CA3AF] text-sm md:text-base leading-relaxed">
              {product.description || "Designed for premium capability and daily durability. StreamSync products utilize real-time personalization algorithms and continuous edge testing to deliver unparalleled value to your device."}
            </p>

            {/* Live Pricing Structures */}
            <div className="p-6 rounded-2xl bg-[#111827]/70 backdrop-blur-md border border-white/10 space-y-4">
              <div className="flex items-baseline gap-3">
                <span className="text-3xl font-extrabold text-[#F9FAFB]">
                  ₹{product.current_price ? Math.floor(product.current_price).toLocaleString('en-IN') : '0'}
                </span>
                {product.current_price && product.original_price && product.current_price !== product.original_price && (
                  <span className="text-[#9CA3AF] line-through text-sm">
                    ₹{Math.floor(product.original_price).toLocaleString('en-IN')}
                  </span>
                )}

                {/* Price Change Percentage */}
                {product.price_change_percentage !== undefined && product.price_change_percentage !== 0 && (
                  <span className={`text-xs font-black px-2.5 py-1 rounded-full ${
                    product.price_change_percentage > 0
                      ? 'bg-[#10B981]/10 text-[#10B981]'
                      : 'bg-[#EF4444]/10 text-[#EF4444]'
                  }`}>
                    {product.price_change_percentage > 0 ? `▲ ${product.price_change_percentage}%` : `▼ ${Math.abs(product.price_change_percentage)}%`}
                  </span>
                )}
              </div>

              {/* Dynamic Explainer Text */}
              {product.change_reason && (
                <div className="flex items-start gap-2 text-xs text-[#22D3EE] font-medium leading-normal italic">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="shrink-0 mt-0.5">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="12" y1="16" x2="12" y2="12" />
                    <line x1="12" y1="8" x2="12.01" y2="8" />
                  </svg>
                  <span>{product.change_reason}</span>
                </div>
              )}
            </div>

            {/* Add to Cart Actions */}
            <div className="flex flex-col sm:flex-row gap-4 pt-4">
              <button
                onClick={handleAddToCart}
                className={`flex-1 py-3.5 rounded-xl font-bold text-center transition-all ${
                  added 
                    ? 'bg-[#10B981] text-[#0B1020]' 
                    : 'bg-gradient-to-r from-[#6D5DFC] to-[#22D3EE] hover:opacity-90 text-[#0B1020]'
                }`}
              >
                {added ? '✓ Added to Cart!' : 'Add to Cart'}
              </button>
              <button className="px-8 py-3.5 rounded-xl font-bold border border-white/10 text-[#F9FAFB] hover:bg-white/5 transition-colors">
                Add to Wishlist
              </button>
            </div>
          </div>
        </div>

        {/* Tailored For You Recommendation Row */}
        <div className="space-y-6 pt-10 border-t border-white/10 text-left">
          <div>
            <h2 className="text-2xl font-extrabold text-[#F9FAFB] tracking-tight flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-[#6D5DFC]/10 text-[#6D5DFC]">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                </svg>
              </span>
              Tailored For You
            </h2>
            <p className="text-xs text-[#9CA3AF] mt-1">Real-time suggestions calculated based on your current session affinity and interaction stream.</p>
          </div>

          {recommendations.length > 0 ? (
            <div className="flex gap-6 overflow-x-auto pb-4 pt-2 no-scrollbar scroll-smooth">
              {recommendations.map(item => (
                <div
                  key={item.id}
                  className="bg-[#111827]/50 backdrop-blur-sm border border-white/5 rounded-2xl p-4 min-w-[260px] max-w-[260px] flex flex-col justify-between shrink-0 hover:border-[#6D5DFC]/40 transition-colors duration-300"
                >
                  <div className="space-y-3">
                    <div className="w-full h-32 bg-white/5 rounded-xl flex items-center justify-center overflow-hidden">
                      {item.image ? (
                        <img src={item.image} className="w-full h-full object-cover" alt={item.name} />
                      ) : (
                        <svg className="w-10 h-10 text-[#9CA3AF]/20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                        </svg>
                      )}
                    </div>
                    <div>
                      <h4 className="font-bold text-sm text-[#F9FAFB] line-clamp-1">{item.name}</h4>
                      <p className="text-xs text-[#9CA3AF] line-clamp-2 mt-1 leading-relaxed">
                        {item.description || 'Dynamic design engineered for peak catalog compatibility.'}
                      </p>
                    </div>
                  </div>

                  <div className="mt-4 flex items-center justify-between pt-2 border-t border-white/5">
                    <span className="text-[#F9FAFB] font-black text-sm">
                      ₹{item.current_price ? Math.floor(item.current_price).toLocaleString('en-IN') : '0'}
                    </span>
                    <a
                      href={`/products/${item.id}`}
                      className="text-xs font-bold text-[#6D5DFC] hover:underline"
                    >
                      View Detail
                    </a>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-10 text-center text-sm font-semibold text-[#9CA3AF]">
              Aggregating machine learning recommendations...
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
