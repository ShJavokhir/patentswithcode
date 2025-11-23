'use client';

import { useState } from 'react';

export default function Home() {
  const [query, setQuery] = useState('');
  const [isFocused, setIsFocused] = useState(false);

  const exampleSearches = [
    'pull to refresh',
    'pinch to zoom',
    'swipe to delete',
    'double tap to like',
    'shake to undo',
  ];

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      console.log('Searching for:', query);
      // TODO: Implement search
    }
  };

  const handleExampleClick = (example: string) => {
    setQuery(example);
  };

  return (
    <div className="min-h-screen bg-canvas relative overflow-hidden">
      {/* Decorative background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-64 h-64 bg-accent-green/10 rounded-full blur-3xl"
             style={{ animation: 'fadeIn 1.5s ease-out' }} />
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-accent-clay/10 rounded-full blur-3xl"
             style={{ animation: 'fadeIn 2s ease-out' }} />
      </div>

      {/* Main content */}
      <main className="relative min-h-screen flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-3xl" style={{ animation: 'fadeInUp 0.8s ease-out' }}>
          {/* Header */}
          <div className="text-center mb-12" style={{ animation: 'fadeInUp 0.9s ease-out' }}>
            <h1 className="text-5xl md:text-6xl font-bold text-ink mb-4 tracking-tight">
              Patents<span className="text-accent-green">With</span>Code
            </h1>
            <p className="text-lg md:text-xl text-ink-secondary max-w-2xl mx-auto leading-relaxed">
              Turn software patents into interactive demos. Search for any invention and see it come to life.
            </p>
          </div>

          {/* Search card - floating island */}
          <div
            className="bg-surface rounded-3xl p-8 md:p-10 shadow-[0_10px_40px_rgba(0,0,0,0.04)] transition-all duration-300"
            style={{
              animation: 'scaleIn 1s ease-out',
              transform: isFocused ? 'translateY(-4px)' : 'translateY(0)',
              boxShadow: isFocused ? '0 20px 60px rgba(0,0,0,0.08)' : '0 10px 40px rgba(0,0,0,0.04)',
            }}
          >
            {/* Search form */}
            <form onSubmit={handleSearch} className="mb-6">
              <div className="relative">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onFocus={() => setIsFocused(true)}
                  onBlur={() => setIsFocused(false)}
                  placeholder="Search for a patent... e.g., 'pull to refresh'"
                  className="w-full px-6 py-5 bg-white rounded-full border-2 text-lg text-ink placeholder-ink-secondary/50
                           transition-all duration-300 focus:outline-none font-mono tracking-tight"
                  style={{
                    borderColor: isFocused ? 'var(--accent-green)' : 'var(--border-subtle)',
                  }}
                />
                <button
                  type="submit"
                  disabled={!query.trim()}
                  className="absolute right-2 top-1/2 -translate-y-1/2 px-8 py-3 bg-ink text-surface rounded-full
                           font-medium transition-all duration-300 hover:bg-accent-green hover:text-ink
                           disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:bg-ink disabled:hover:text-surface"
                >
                  Search
                </button>
              </div>
            </form>

            {/* Example searches */}
            <div className="space-y-3">
              <p className="text-sm font-medium text-ink-secondary uppercase tracking-wide">
                Try searching for:
              </p>
              <div className="flex flex-wrap gap-2">
                {exampleSearches.map((example, index) => (
                  <button
                    key={example}
                    onClick={() => handleExampleClick(example)}
                    className="px-4 py-2 bg-white rounded-full text-sm font-mono text-ink-secondary
                             hover:bg-accent-green/20 hover:text-accent-green transition-all duration-300
                             border border-border-subtle hover:border-accent-green"
                    style={{
                      animation: `fadeInUp ${1.1 + index * 0.1}s ease-out`,
                    }}
                  >
                    {example}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Info footer */}
          <div
            className="mt-8 text-center text-sm text-ink-secondary/70"
            style={{ animation: 'fadeIn 1.5s ease-out' }}
          >
            <p className="font-mono">
              Powered by Google Patents, Groq, Claude Code, and E2B
            </p>
          </div>
        </div>
      </main>

      {/* Subtle grid pattern overlay */}
      <div
        className="absolute inset-0 pointer-events-none opacity-[0.02]"
        style={{
          backgroundImage: `linear-gradient(var(--ink) 1px, transparent 1px),
                           linear-gradient(90deg, var(--ink) 1px, transparent 1px)`,
          backgroundSize: '40px 40px',
        }}
      />
    </div>
  );
}
