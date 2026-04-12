import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'

const AppInput = (props) => {
  const { label, placeholder, icon, ...rest } = props;
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [isHovering, setIsHovering] = useState(false);

  const handleMouseMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setMousePosition({ x: e.clientX - rect.left, y: e.clientY - rect.top });
  };

  return (
    <div className="w-full relative">
      <div className="relative w-full">
        <input
          className="peer relative z-10 border-2 border-[var(--color-border)] h-12 w-full rounded-lg bg-[var(--color-surface)] px-4 font-normal text-[var(--color-text-primary)] outline-none drop-shadow-sm transition-all duration-200 ease-in-out focus:bg-[var(--color-bg)] placeholder:font-medium placeholder-[#888]"
          placeholder={placeholder}
          onMouseMove={handleMouseMove}
          onMouseEnter={() => setIsHovering(true)}
          onMouseLeave={() => setIsHovering(false)}
          {...rest}
        />
        {/* Premium glowing hover borders */}
        {isHovering && (
          <>
            <div className="absolute pointer-events-none top-0 left-0 right-0 h-[2px] z-20 rounded-t-lg overflow-hidden" 
                 style={{ background: `radial-gradient(35px circle at ${mousePosition.x}px 0px, #16A34A 0%, transparent 80%)` }} />
            <div className="absolute pointer-events-none bottom-0 left-0 right-0 h-[2px] z-20 rounded-b-lg overflow-hidden" 
                 style={{ background: `radial-gradient(35px circle at ${mousePosition.x}px 2px, #16A34A 0%, transparent 80%)` }} />
          </>
        )}
      </div>
    </div>
  )
}

export default function Login() {
  const [isSignUp, setIsSignUp] = useState(false);
  const navigate = useNavigate();

  // Mouse tracking state for the background blur effect under the forms
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [isHovering, setIsHovering] = useState(false);
  
  const handleMouseMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setMousePosition({ x: e.clientX - rect.left, y: e.clientY - rect.top });
  };

  const handleAuthSubmit = (e) => {
    e.preventDefault();
    localStorage.setItem('user', 'alex_stream');
    navigate('/');
  };

  const socialIcons = [
    { icon: <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24"><path fill="currentColor" d="M7.8 2h8.4C19.4 2 22 4.6 22 7.8v8.4a5.8 5.8 0 0 1-5.8 5.8H7.8C4.6 22 2 19.4 2 16.2V7.8A5.8 5.8 0 0 1 7.8 2m-.2 2A3.6 3.6 0 0 0 4 7.6v8.8C4 18.39 5.61 20 7.6 20h8.8a3.6 3.6 0 0 0 3.6-3.6V7.6C20 5.61 18.39 4 16.4 4zm9.65 1.5a1.25 1.25 0 0 1 1.25 1.25A1.25 1.25 0 0 1 17.25 8A1.25 1.25 0 0 1 16 6.75a1.25 1.25 0 0 1 1.25-1.25M12 7a5 5 0 0 1 5 5a5 5 0 0 1-5 5a5 5 0 0 1-5-5a5 5 0 0 1 5-5m0 2a3 3 0 0 0-3 3a3 3 0 0 0 3 3a3 3 0 0 0 3-3a3 3 0 0 0-3-3"/></svg> },
    { icon: <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24"><path fill="currentColor" d="M6.94 5a2 2 0 1 1-4-.002a2 2 0 0 1 4 .002M7 8.48H3V21h4zm6.32 0H9.34V21h3.94v-6.57c0-3.66 4.77-4 4.77 0V21H22v-7.93c0-6.17-7.06-5.94-8.72-2.91z"/></svg> },
    { icon: <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24"><path fill="currentColor" d="M9.198 21.5h4v-8.01h3.604l.396-3.98h-4V7.5a1 1 0 0 1 1-1h3v-4h-3a5 5 0 0 0-5 5v2.01h-2l-.396 3.98h2.396z"/></svg> }
  ];

  return (
    <div className="min-h-screen w-full bg-[var(--color-bg)] text-[var(--color-heading)] flex items-center justify-center p-4 selection:bg-[#16A34A]/20">
      
      {/* 
        Main Container
        Contains both forms (left and right) and the sliding image overlay.
      */}
      <div className='relative w-full max-w-[1000px] h-[640px] bg-[var(--color-surface)] border border-[var(--color-border)] rounded-[24px] overflow-hidden shadow-2xl'>

        {/* Global Blur Blob Background under forms */}
        <div
            className={`absolute pointer-events-none w-[500px] h-[500px] bg-gradient-to-r from-emerald-400/20 via-green-400/20 to-teal-400/20 rounded-full blur-3xl transition-opacity duration-300 z-0 ${isHovering ? 'opacity-100' : 'opacity-0'}`}
            style={{ transform: `translate(${mousePosition.x - 250}px, ${mousePosition.y - 250}px)`, transition: 'transform 0.1s ease-out' }}
        />

        {/* ========================================================= */}
        {/* LEFT PANEL: SIGN IN FORM */}
        {/* ========================================================= */}
        <div className={`absolute top-0 left-0 w-full lg:w-1/2 h-full z-10 px-8 lg:px-14 flex flex-col justify-center transition-all duration-[800ms] ${isSignUp ? 'opacity-0 pointer-events-none' : 'opacity-100'}`}
             onMouseMove={handleMouseMove} onMouseEnter={()=>setIsHovering(true)} onMouseLeave={()=>setIsHovering(false)}>
          <form className='text-center flex flex-col justify-center h-full relative z-10' onSubmit={handleAuthSubmit}>
            <h1 className='text-4xl font-extrabold tracking-tight mb-6'>Sign in</h1>
            
            <div className="flex justify-center gap-4 mb-6">
              {socialIcons.map((social, i) => (
                <button type="button" key={i} className="w-12 h-12 rounded-full border-2 border-[var(--color-border)] flex items-center justify-center text-[var(--color-text-primary)] hover:border-[#16A34A] hover:text-[#16A34A] transition-all duration-300 hover:scale-105 bg-[var(--color-bg)] shadow-sm">
                  {social.icon}
                </button>
              ))}
            </div>
            
            <span className='text-sm text-[var(--color-text-secondary)] font-medium mb-6'>or use your email account</span>
            
            <div className='flex flex-col gap-4 items-center'>
              <AppInput placeholder="Email" type="email" required />
              <AppInput placeholder="Password" type="password" required />
            </div>
            
            <div className="flex flex-col gap-2 mt-6">
              <a href="#" className='font-medium text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors'>Forgot your password?</a>
              <button 
                type="button" 
                onClick={() => setIsSignUp(true)} 
                className='font-bold text-sm text-[#16A34A] hover:text-[#15803d] transition-colors mt-2 uppercase tracking-wide'
              >
                Create Account
              </button>
            </div>
            
            <button type="submit" className="mt-8 relative inline-flex self-center justify-center items-center overflow-hidden rounded-xl bg-[#1A2E1A] px-12 py-3.5 font-bold text-white transition-all duration-300 hover:scale-[1.02] hover:bg-black shadow-lg shadow-black/10">
              Sign In
            </button>
          </form>
        </div>


        {/* ========================================================= */}
        {/* RIGHT PANEL: SIGN UP FORM */}
        {/* ========================================================= */}
        <div className={`absolute top-0 right-0 w-full lg:w-1/2 h-full z-10 px-8 lg:px-14 flex flex-col justify-center transition-all duration-[800ms] ${!isSignUp ? 'opacity-0 pointer-events-none' : 'opacity-100'}`}
             onMouseMove={handleMouseMove} onMouseEnter={()=>setIsHovering(true)} onMouseLeave={()=>setIsHovering(false)}>
          <form className='text-center flex flex-col justify-center h-full relative z-10' onSubmit={handleAuthSubmit}>
            <h1 className='text-4xl font-extrabold tracking-tight mb-6'>Create Account</h1>
            
            <div className="flex justify-center gap-4 mb-6">
              {socialIcons.map((social, i) => (
                <button type="button" key={i} className="w-12 h-12 rounded-full border-2 border-[var(--color-border)] flex items-center justify-center text-[var(--color-text-primary)] hover:border-[#16A34A] hover:text-[#16A34A] transition-all duration-300 hover:scale-105 bg-[var(--color-bg)] shadow-sm">
                  {social.icon}
                </button>
              ))}
            </div>
            
            <span className='text-sm text-[var(--color-text-secondary)] font-medium mb-6'>or use your email for registration</span>
            
            <div className='flex flex-col gap-4 items-center'>
              <AppInput placeholder="Full Name" type="text" required />
              <AppInput placeholder="Email" type="email" required />
              <AppInput placeholder="Password" type="password" required />
            </div>
            
            <div className="flex flex-col gap-1 mt-6">
              <span className='font-medium text-sm text-[var(--color-text-secondary)] mt-2'>Already have an account?</span>
              <button 
                type="button" 
                onClick={() => setIsSignUp(false)} 
                className='font-bold text-sm text-[#16A34A] hover:text-[#15803d] transition-colors uppercase tracking-wide'
              >
                Sign In Instead
              </button>
            </div>
            
            <button type="submit" className="mt-8 relative inline-flex self-center justify-center items-center overflow-hidden rounded-xl bg-[#1A2E1A] px-12 py-3.5 font-bold text-white transition-all duration-300 hover:scale-[1.02] hover:bg-black shadow-lg shadow-black/10">
              Sign Up
            </button>
          </form>
        </div>


        {/* ========================================================= */}
        {/* THE SLIDING IMAGE OVERLAY PANEL */}
        {/* When isSignUp is true, we slide this from Right (0) to Left (-100%) */}
        {/* ========================================================= */}
        <div 
          className="hidden lg:block absolute top-0 right-0 w-1/2 h-full z-50 bg-black transition-transform duration-[800ms] ease-[cubic-bezier(0.87,0,0.13,1)] shadow-2xl"
          style={{ transform: isSignUp ? 'translateX(-100%)' : 'translateX(0)' }}
        >
          <div className="relative w-full h-full overflow-hidden flex items-center justify-center group">
            {/* The stunning red Nike shoe, explicitly requested */}
            <img
              src="https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=1200&q=80"
              alt="Nike Shoes"
              className={`absolute inset-0 w-full h-full object-cover transition-transform duration-[1.5s] ease-out select-none ${isSignUp ? 'scale-110 rotate-1' : 'scale-100 rotate-0'}`}
            />
            
            {/* Gradient Overlay for contrast */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/10 to-transparent" />
            
            {/* Dynamic Overlay Text syncing with the animation state */}
            <div className="absolute bottom-12 inset-x-0 px-12 text-center transition-opacity duration-700 pointer-events-none">
              <h2 className="text-3xl font-extrabold text-white tracking-tight mb-2 drop-shadow-md">
                {isSignUp ? "Join the Movement." : "Welcome Back."}
              </h2>
              <p className="text-white/80 text-sm font-medium drop-shadow-sm max-w-[80%] mx-auto">
                {isSignUp 
                  ? "Sign up today to discover curated drops and exclusive gear."
                  : "Sign in to pick up right where you left off."}
              </p>
            </div>
          </div>
        </div>

      </div>
    </div>
  )
}
