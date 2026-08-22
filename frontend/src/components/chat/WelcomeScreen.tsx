'use client';

import React from 'react';
import { Sparkles } from 'lucide-react';

interface WelcomeScreenProps {
  onSelectPrompt: (prompt: string) => void;
  selectedModel: string;
}

export function WelcomeScreen({ selectedModel }: WelcomeScreenProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[55vh] px-4 text-center max-w-2xl mx-auto select-none">
      {/* Centered Minimal Brand Icon */}
      <div className="w-14 h-14 rounded-2xl bg-[var(--accent-muted)] border border-[var(--border-accent)] flex items-center justify-center text-[var(--accent-primary)] mb-6 shadow-[var(--shadow-md)]">
        <Sparkles className="w-7 h-7" />
      </div>

      {/* Clean Welcome Heading */}
      <h1 className="text-3xl sm:text-5xl font-display text-[var(--text-primary)] mb-3 tracking-tight font-bold leading-tight">
        Welcome to <span className="text-[var(--accent-primary)] font-bold">Aarka AI</span>
      </h1>

      {/* Clean Minimal Tagline */}
      <p className="text-sm sm:text-base text-[var(--text-secondary)] max-w-md font-sans leading-relaxed">
        How can Aarka assist your research, financial engineering, or architecture today?
      </p>
    </div>
  );
}
