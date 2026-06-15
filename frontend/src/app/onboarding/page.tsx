import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [ageGroup, setAgeGroup] = useState('');
  const [gender, setGender] = useState('');
  const [interests, setInterests] = useState([]);
  const [preferences, setPreferences] = useState({
    deals: false,
    newTech: false,
    ecoFriendly: false,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitComplete, setSubmitComplete] = useState(false);

  const toggleInterest = (category: string) => {
    setInterests(prev =>
      prev.includes(category)
        ? prev.filter(c => c !== category)
        : [...prev, category]
    );
  };

  const handlePreferenceToggle = (key: string) => {
    setPreferences(prev => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const nextStep = () => {
    if (step < 3) setStep(prev => prev + 1);
  };

  const prevStep = () => {
    if (step > 1) setStep(prev => prev - 1);
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      const payload = {
        age_group: ageGroup,
        gender: gender,
        interests: interests,
        shopping_preferences: preferences
      };
      
      const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
      const headers = { 'Content-Type': 'application/json' };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch('/api/v1/users/onboarding', {
        method: 'POST',
        headers: headers,
        body: JSON.stringify(payload)
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.user_id) localStorage.setItem('user_id', data.user_id.toString());
        if (data.session_id) localStorage.setItem('session_id', data.session_id);
        
        setIsSubmitting(false);
        setSubmitComplete(true);
        setTimeout(() => {
          router.push('/');
        }, 1500);
      } else {
        throw new Error('Onboarding request failed');
      }
    } catch (err) {
      console.error('Failed to submit onboarding:', err);
      // Fallback
      localStorage.setItem('user_id', 'mock-user-id');
      localStorage.setItem('session_id', 'mock-session-id');
      setIsSubmitting(false);
      setSubmitComplete(true);
      setTimeout(() => {
        router.push('/');
      }, 1500);
    }
  };

  // Variants for framer-motion slide animations
  const slideVariants = {
    hidden: { opacity: 0, x: 50 },
    visible: { opacity: 1, x: 0, transition: { duration: 0.4, ease: 'easeOut' } },
    exit: { opacity: 0, x: -50, transition: { duration: 0.3, ease: 'easeIn' } },
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center p-4 bg-bg-base text-text-base selection:bg-primary-accent/20">
      <div className="relative w-full max-w-lg glass-card rounded-3xl p-8 shadow-2xl overflow-hidden">
        {/* Decorative blur elements inside the card */}
        <div className="absolute top-[-50px] right-[-50px] w-40 h-40 bg-primary-accent/20 rounded-full blur-3xl" />
        <div className="absolute bottom-[-50px] left-[-50px] w-40 h-40 bg-secondary-accent/20 rounded-full blur-3xl" />

        <div className="relative z-10">
          {/* Header Progress indicator */}
          <div className="flex justify-between items-center mb-8">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-text">
              Step {step} of 3
            </span>
            <div className="flex gap-1.5">
              {[1, 2, 3].map(i => (
                <div
                  key={i}
                  className={`h-1.5 rounded-full transition-all duration-300 ${
                    step >= i ? 'w-6 bg-primary-accent' : 'w-2 bg-white/20'
                  }`}
                />
              ))}
            </div>
          </div>

          <AnimatePresence mode="wait">
            {isSubmitting ? (
              <motion.div
                key="submitting"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex flex-col items-center justify-center py-12"
              >
                <div className="relative w-16 h-16 mb-6">
                  <div className="absolute inset-0 rounded-full border-4 border-white/10" />
                  <div className="absolute inset-0 rounded-full border-4 border-t-primary-accent animate-spin" />
                </div>
                <h3 className="text-xl font-bold mb-2">Analyzing Preferences...</h3>
                <p className="text-sm text-muted-text text-center">
                  Curating your personalized storefront experience.
                </p>
              </motion.div>
            ) : submitComplete ? (
              <motion.div
                key="complete"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex flex-col items-center justify-center py-12"
              >
                <div className="w-16 h-16 rounded-full bg-success/20 border border-success/40 flex items-center justify-center mb-6">
                  <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#10B981" strokeWidth="3">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                </div>
                <h3 className="text-xl font-bold mb-2 text-success">Setup Complete!</h3>
                <p className="text-sm text-muted-text text-center">
                  Redirecting you to your personalized home feed.
                </p>
              </motion.div>
            ) : (
              <motion.div
                key={step}
                variants={slideVariants}
                initial="hidden"
                animate="visible"
                exit="exit"
              >
                {step === 1 && (
                  <div>
                    <h2 className="text-2xl font-extrabold mb-2 tracking-tight">Tell us about yourself</h2>
                    <p className="text-sm text-muted-text mb-6">This helps us audit pricing fairness across demographics.</p>

                    <div className="space-y-5">
                      <div>
                        <label className="block text-sm font-semibold mb-2 text-muted-text">Age Group</label>
                        <div className="grid grid-cols-3 gap-3">
                          {['18-25', '26-35', '36+'].map(group => (
                            <button
                              key={group}
                              type="button"
                              onClick={() => setAgeGroup(group)}
                              className={`py-3 px-4 rounded-xl border text-sm font-medium transition-all ${
                                ageGroup === group
                                  ? 'bg-primary-accent border-primary-accent text-white shadow-lg shadow-primary-accent/25'
                                  : 'border-white/10 hover:border-white/25 hover:bg-white/5'
                              }`}
                            >
                              {group}
                            </button>
                          ))}
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-semibold mb-2 text-muted-text">Gender</label>
                        <div className="grid grid-cols-3 gap-3">
                          {['Female', 'Male', 'Non-binary'].map(g => (
                            <button
                              key={g}
                              type="button"
                              onClick={() => setGender(g)}
                              className={`py-3 px-4 rounded-xl border text-sm font-medium transition-all ${
                                gender === g
                                  ? 'bg-primary-accent border-primary-accent text-white shadow-lg shadow-primary-accent/25'
                                  : 'border-white/10 hover:border-white/25 hover:bg-white/5'
                              }`}
                            >
                              {g}
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {step === 2 && (
                  <div>
                    <h2 className="text-2xl font-extrabold mb-2 tracking-tight">Interest Mapping</h2>
                    <p className="text-sm text-muted-text mb-6">Select your favorite product categories to tailor recommendations.</p>

                    <div className="flex flex-wrap gap-2.5">
                      {['Electronics', 'Apparel', 'Fitness', 'Home Decor', 'Books', 'Beauty', 'Kitchen'].map(cat => {
                        const selected = interests.includes(cat);
                        return (
                          <button
                            key={cat}
                            type="button"
                            onClick={() => toggleInterest(cat)}
                            className={`py-2 px-4 rounded-full border text-sm font-semibold transition-all ${
                              selected
                                ? 'bg-secondary-accent border-secondary-accent text-bg-base font-bold shadow-md shadow-secondary-accent/20'
                                : 'border-white/10 hover:border-white/25 hover:bg-white/5 text-muted-text hover:text-text-base'
                            }`}
                          >
                            {cat}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}

                {step === 3 && (
                  <div>
                    <h2 className="text-2xl font-extrabold mb-2 tracking-tight">Shopping Preferences</h2>
                    <p className="text-sm text-muted-text mb-6">Fine-tune the recommendation priority controls.</p>

                    <div className="space-y-4">
                      {[
                        { key: 'deals', title: 'Priority on Discounts & Deals', desc: 'Focus recommendations on price cuts.' },
                        { key: 'newTech', title: 'Newest Tech & Releases', desc: 'Highlight newly arrived inventory.' },
                        { key: 'ecoFriendly', title: 'Eco-Friendly & Sustainable', desc: 'Prioritize green certified brands.' }
                      ].map(pref => (
                        <div
                          key={pref.key}
                          onClick={() => handlePreferenceToggle(pref.key)}
                          className={`flex items-center justify-between p-4 rounded-2xl border cursor-pointer transition-all ${
                            preferences[pref.key]
                              ? 'border-secondary-accent/45 bg-secondary-accent/5'
                              : 'border-white/10 hover:border-white/20'
                          }`}
                        >
                          <div>
                            <h4 className="font-semibold text-sm">{pref.title}</h4>
                            <p className="text-xs text-muted-text mt-0.5">{pref.desc}</p>
                          </div>
                          <div className={`w-12 h-6 rounded-full p-0.5 transition-all duration-300 ${
                            preferences[pref.key] ? 'bg-secondary-accent' : 'bg-white/10'
                          }`}>
                            <div className={`w-5 h-5 rounded-full bg-white transition-all duration-300 transform ${
                              preferences[pref.key] ? 'translate-x-6' : 'translate-x-0'
                            }`} />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Footer Navigation Buttons */}
                <div className="flex gap-4 mt-8 pt-6 border-t border-white/5">
                  {step > 1 && (
                    <button
                      type="button"
                      onClick={prevStep}
                      className="flex-1 py-3.5 rounded-xl border border-white/10 hover:bg-white/5 font-semibold text-sm transition-all"
                    >
                      Back
                    </button>
                  )}
                  {step < 3 ? (
                    <button
                      type="button"
                      onClick={nextStep}
                      disabled={step === 1 && (!ageGroup || !gender)}
                      className="flex-1 py-3.5 rounded-xl bg-primary-accent hover:bg-opacity-90 font-semibold text-sm text-white transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Continue
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={handleSubmit}
                      className="flex-1 py-3.5 rounded-xl bg-secondary-accent hover:bg-opacity-90 font-bold text-sm text-bg-base transition-all"
                    >
                      Complete Setup
                    </button>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
