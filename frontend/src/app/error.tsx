'use client';

import React, { useEffect } from 'react';
import { RefreshCw, AlertCircle } from 'lucide-react';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('[Next.js Error Boundary]:', error);
  }, [error]);

  const handleClearCacheAndReset = () => {
    reset();
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-6 bg-[#0f0e0d] text-[#e8e6e3] text-center">
      <div className="w-14 h-14 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 mb-5 shadow-lg">
        <AlertCircle className="w-7 h-7" />
      </div>

      <h2 className="text-2xl sm:text-3xl font-display font-bold tracking-tight mb-3">
        Workspace Reset Required
      </h2>

      <p className="text-xs sm:text-sm text-[#9e9b97] max-w-md mb-6 leading-relaxed">
        A previous browser session state or cached token encountered a conflict. Clicking below will restore the clean conversation workspace.
      </p>

      <button
        onClick={handleClearCacheAndReset}
        type="button"
        className="flex items-center gap-2 px-5 py-3 rounded-2xl bg-[#c96442] hover:bg-[#b55535] text-white text-xs sm:text-sm font-semibold shadow-md transition-all cursor-pointer hover:scale-105"
      >
        <RefreshCw className="w-4 h-4" />
        <span>Restore Workspace & Chat</span>
      </button>
    </div>
  );
}
