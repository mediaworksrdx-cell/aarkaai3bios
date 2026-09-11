'use client';

import React from 'react';
import { Sparkles } from 'lucide-react';

interface WelcomeScreenProps {
  onSelectPrompt?: (prompt: string) => void;
  selectedModel: string;
  userName?: string;
  isGuest?: boolean;
}

export function WelcomeScreen({ selectedModel, userName, isGuest }: WelcomeScreenProps) {
  const isLoggedIn = !isGuest && userName && userName !== 'Guest User' && userName !== 'Web Visitor';

  return (
    <div className="flex flex-col items-center justify-center min-h-[55vh] px-4 text-center max-w-2xl mx-auto select-none">
      {/* Centered Minimal Brand Icon */}
      <div className="w-16 h-16 rounded-2xl bg-white border border-[var(--border)] flex items-center justify-center p-2 mb-6 shadow-[var(--shadow-md)]">
        <img src="/logo.png" alt="Aarka AI Logo" className="w-12 h-12 object-contain" />
      </div>

      {/* Clean Welcome Heading */}
      <h1 className="text-3xl sm:text-5xl font-display text-[var(--text-primary)] mb-3 tracking-tight font-bold leading-tight">
        {isLoggedIn ? (
          <>
            Welcome, <span className="text-[var(--accent-primary)] font-bold">{userName}</span>
          </>
        ) : (
          <>
            Welcome to <span className="text-[var(--accent-primary)] font-bold">Aarka AI</span>
          </>
        )}
      </h1>

      {/* Clean Minimal Tagline */}
      <p className="text-sm sm:text-base text-[var(--text-secondary)] max-w-md font-sans leading-relaxed">
        How can Aarka assist your research, financial engineering, or architecture today?
      </p>
    </div>
  );
}
