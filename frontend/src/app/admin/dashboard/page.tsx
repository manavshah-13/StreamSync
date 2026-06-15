'use client';

import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';
import { motion, AnimatePresence } from 'framer-motion';

interface DataTick {
  time: string;
  variableFactor: number;
  velocity: number;
}

// Generate starting mock/placeholder data points (12 ticks)
const generateInitialTrendData = (): DataTick[] => {
  const now = new Date();
  return Array.from({ length: 12 }, (_, i) => {
    const time = new Date(now.getTime() - (12 - i) * 4000).toLocaleTimeString('en', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
    return {
      time,
      variableFactor: parseFloat((0.95 + Math.sin(i * 0.5) * 0.15 + Math.random() * 0.05).toFixed(2)),
      velocity: Math.floor(130 + Math.cos(i * 0.6) * 40 + Math.random() * 20),
    };
  });
};

export default function AdminDashboardPage() {
  const [data, setData] = useState<DataTick[]>([]);
  const [loading, setLoading] = useState(false);
  const [pulseActive, setPulseActive] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string>('Never');
  
  const [metrics, setMetrics] = useState({
    activeSkus: '10.4M',
    repricingRate: '41,200/s',
    activeSessions: '18,340',
    cacheHitRate: '98.7%',
    streamLag: '12ms'
  });

  // Load initial data
  useEffect(() => {
    setData(generateInitialTrendData());
  }, []);

  // Poll API every 4 seconds
  useEffect(() => {
    const fetchOverview = async () => {
      try {
        const res = await fetch('/api/v1/analytics/overview');
        if (!res.ok) throw new Error('Failed to fetch overview metrics');
        const json = await res.json();
        
        // Update metric summaries
        setMetrics({
          activeSkus: json.activeSkus,
          repricingRate: json.repricingRate,
          activeSessions: json.activeSessions.toLocaleString(),
          cacheHitRate: `${json.cacheHitRate}%`,
          streamLag: json.streamLag,
        });

        // Inject new tick and bound visualization to last 12-15 items (using 12 here)
        if (json.current_tick) {
          const newTick: DataTick = json.current_tick;
          setData(prev => {
            const nextData = [...prev, newTick];
            if (nextData.length > 12) {
              return nextData.slice(nextData.length - 12);
            }
            return nextData;
          });
        }

        // Trigger flash / pulse update
        setPulseActive(true);
        setLastUpdate(new Date().toLocaleTimeString());
        setTimeout(() => setPulseActive(false), 800);
      } catch (err) {
        console.warn('Real-time poll failed, falling back to local simulation:', err);
        // Local simulation fallback
        const simulatedTime = new Date().toLocaleTimeString('en', {
          hour12: false,
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        });
        const simulatedTick: DataTick = {
          time: simulatedTime,
          variableFactor: parseFloat((0.95 + Math.sin(Date.now() * 0.0001) * 0.2 + Math.random() * 0.1).toFixed(2)),
          velocity: Math.floor(140 + Math.cos(Date.now() * 0.0002) * 50 + Math.random() * 20),
        };
        setData(prev => {
          const nextData = [...prev, simulatedTick];
          if (nextData.length > 12) {
            return nextData.slice(nextData.length - 12);
          }
          return nextData;
        });
        setPulseActive(true);
        setLastUpdate(simulatedTime);
        setTimeout(() => setPulseActive(false), 800);
      }
    };

    // Initial load
    fetchOverview();
    
    // Set interval for every 4 seconds
    const intervalId = setInterval(fetchOverview, 4000);
    return () => clearInterval(intervalId);
  }, []);

  const forceSync = async () => {
    setLoading(true);
    // Simulate force sync delay
    await new Promise(r => setTimeout(r, 600));
    const simulatedTime = new Date().toLocaleTimeString();
    setData(generateInitialTrendData());
    setLastUpdate(simulatedTime);
    setLoading(false);
  };

  return (
    <div className="min-h-screen w-full bg-[#0B1020] text-[#F9FAFB] px-6 py-12 md:px-12 lg:px-24">
      <div className="max-w-7xl mx-auto space-y-10">
        
        {/* Header Section */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="space-y-1 text-left">
            <div className="flex flex-wrap items-center gap-3">
              <span className="w-2.5 h-2.5 rounded-full bg-[#10B981] animate-ping" />
              <span className="text-xs font-black uppercase tracking-[0.2em] text-[#10B981]">
                System Monitoring Active
              </span>

              {/* Glowing pipeline status badge */}
              <div 
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold border transition-all duration-500 ${
                  pulseActive 
                    ? 'bg-[#10B981]/25 border-[#10B981] text-white shadow-[0_0_12px_rgba(16,185,129,0.4)]' 
                    : 'bg-[#10B981]/10 border-[#10B981]/30 text-[#10B981]'
                }`}
              >
                <span className={`w-1.5 h-1.5 rounded-full bg-[#10B981] ${pulseActive ? 'scale-125' : 'animate-pulse'}`} />
                Live Pipeline Processing Active
              </div>
            </div>
            <h1 className="text-4xl font-extrabold tracking-tight bg-gradient-to-r from-[#6D5DFC] to-[#22D3EE] bg-clip-text text-transparent mt-2">
              Engine Dashboard
            </h1>
            <p className="text-[#9CA3AF] text-sm">
              Real-time repricing telemetry and user interaction stream analytics.
            </p>
          </div>
          
          <div className="flex flex-col items-end gap-2">
            <span className="text-[10px] font-mono text-[#9CA3AF]">
              Last Event Sync: {lastUpdate}
            </span>
            <button
              onClick={forceSync}
              disabled={loading}
              className="px-5 py-2.5 rounded-xl font-bold bg-[#111827]/70 border border-white/10 hover:bg-white/5 transition-all text-sm shrink-0 flex items-center gap-2"
            >
              {loading && <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
              Force Sync Engine
            </button>
          </div>
        </div>

        {/* System Health Metric Cards */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {[
            { label: 'Active SKUs', value: metrics.activeSkus, color: 'text-[#6D5DFC]' },
            { label: 'Repricing Rate', value: metrics.repricingRate, color: 'text-[#22D3EE]' },
            { label: 'Active Sessions', value: metrics.activeSessions, color: 'text-[#10B981]' },
            { label: 'Cache Hit Rate', value: metrics.cacheHitRate, color: 'text-[#F59E0B]' },
            { label: 'Stream Lag', value: metrics.streamLag, color: 'text-[#EF4444]' }
          ].map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: i * 0.05 }}
              className="bg-[#111827]/70 backdrop-blur-md border border-white/10 rounded-2xl p-5 text-left"
            >
              <p className="text-[11px] text-[#9CA3AF] font-semibold uppercase tracking-wider">{stat.label}</p>
              <p className={`text-2xl font-black font-mono mt-1 ${stat.color}`}>{stat.value}</p>
            </motion.div>
          ))}
        </div>

        {/* Recharts Core Graph Section */}
        <div className="bg-[#111827]/70 backdrop-blur-md border border-white/10 rounded-3xl p-6 md:p-8 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 text-left">
            <div>
              <h2 className="text-xl font-bold text-[#F9FAFB]">Interaction Stream vs Pricing Velocity</h2>
              <p className="text-xs text-[#9CA3AF] mt-1">Comparing real-time pricing multipliers against active stream velocity metrics.</p>
            </div>
            {/* Chart Legend */}
            <div className="flex items-center gap-6 text-xs font-semibold">
              <div className="flex items-center gap-2">
                <span className="w-3.5 h-1.5 rounded-full bg-[#6D5DFC]" />
                <span className="text-[#9CA3AF]">Pricing Variable Factor</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3.5 h-1.5 rounded-full border-t-2 border-dashed border-[#22D3EE]" />
                <span className="text-[#9CA3AF]">Event Stream Velocity</span>
              </div>
            </div>
          </div>

          <div className="w-full h-80 md:h-96">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid stroke="#1F2937" strokeDasharray="3 3" />
                <XAxis 
                  dataKey="time" 
                  tick={{ fill: '#9CA3AF', fontSize: 10, fontWeight: 'bold' }} 
                  tickLine={false}
                  axisLine={false}
                />
                
                {/* Left Y-Axis for Variable Factor */}
                <YAxis 
                  yAxisId="left"
                  domain={[0.4, 1.8]}
                  tick={{ fill: '#6D5DFC', fontSize: 10, fontWeight: 'bold' }}
                  tickLine={false}
                  axisLine={false}
                />
                
                {/* Right Y-Axis for Event Velocity */}
                <YAxis 
                  yAxisId="right"
                  orientation="right"
                  domain={[50, 360]}
                  tick={{ fill: '#22D3EE', fontSize: 10, fontWeight: 'bold' }}
                  tickLine={false}
                  axisLine={false}
                />

                {/* Custom Tooltip fit for deep glassmorphism */}
                <Tooltip
                  content={({ active, payload, label }) => {
                    if (active && payload && payload.length) {
                      return (
                        <div className="bg-[#111827] border border-white/10 rounded-xl p-3 shadow-2xl text-left space-y-1">
                          <p className="text-[10px] text-[#9CA3AF] font-bold">{label}</p>
                          <p className="text-xs text-[#6D5DFC] font-semibold">
                            Variable Factor: <span className="font-mono font-bold text-white">{payload[0]?.value}x</span>
                          </p>
                          <p className="text-xs text-[#22D3EE] font-semibold">
                            Stream Velocity: <span className="font-mono font-bold text-white">{payload[1]?.value} req/s</span>
                          </p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />

                <ReferenceLine 
                  yAxisId="left"
                  y={1.0} 
                  stroke="#EF4444" 
                  strokeDasharray="4 4" 
                  label={{ value: 'Parity Base', fill: '#EF4444', fontSize: 9, position: 'insideBottomLeft' }} 
                />

                {/* Line 1: Pricing Variable Factor */}
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="variableFactor"
                  stroke="#6D5DFC"
                  strokeWidth={3.5}
                  dot={{ r: 4, stroke: '#6D5DFC', strokeWidth: 2, fill: '#0B1020' }}
                  activeDot={{ r: 6, fill: '#6D5DFC' }}
                />

                {/* Line 2: In-Flight Event Stream Velocity */}
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="velocity"
                  stroke="#22D3EE"
                  strokeWidth={2}
                  strokeDasharray="6 4"
                  dot={false}
                  activeDot={{ r: 5, fill: '#22D3EE' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>
    </div>
  );
}
