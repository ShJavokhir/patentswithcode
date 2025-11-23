'use client';

import { useState, useEffect, useMemo } from 'react';

export default function Results2Page() {
  const [patentText, setPatentText] = useState<string>('');
  const [patentUrl, setPatentUrl] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'patent' | 'specs' | 'code' | 'demo'>('patent');
  const [specs, setSpecs] = useState<string>('');
  const [code, setCode] = useState<string>('');
  const [loadingSpecs, setLoadingSpecs] = useState(false);
  const [loadingCode, setLoadingCode] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [e2bUrl, setE2bUrl] = useState<string>('');
  const [sandboxId, setSandboxId] = useState<string>('');
  const [loadingE2B, setLoadingE2B] = useState(false);

  // Load patent data from sessionStorage on mount
  useEffect(() => {
    const storedData = sessionStorage.getItem('patentData');
    if (storedData) {
      try {
        const data = JSON.parse(storedData);
        setPatentText(data.text || '');
        setPatentUrl(data.url || '');
      } catch (err) {
        console.error('Failed to parse patent data:', err);
      }
    }
  }, []);

  // Auto-generate specs when patent text is available
  useEffect(() => {
    if (patentText && !specs && !loadingSpecs) {
      generateSpecs();
    }
  }, [patentText]);

  const generateSpecs = async () => {
    setLoadingSpecs(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/patent-to-specs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: patentText }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate specs');
      }

      const data = await response.json();
      setSpecs(data.specs);
      setActiveTab('specs');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate specs');
    } finally {
      setLoadingSpecs(false);
    }
  };

  const generateCode = async () => {
    if (!specs) return;
    
    setLoadingCode(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/specs-to-code', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ specs }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate code');
      }

      const data = await response.json();
      setCode(data.code);
      setActiveTab('code');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate code');
    } finally {
      setLoadingCode(false);
    }
  };

  const runInE2B = async () => {
    if (!code) return;
    
    setLoadingE2B(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/run-in-e2b', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code, specs }),
      });

      if (!response.ok) {
        throw new Error('Failed to run in E2B');
      }

      const data = await response.json();
      setE2bUrl(data.url);
      setSandboxId(data.sandbox_id);
      setActiveTab('demo');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run in E2B');
    } finally {
      setLoadingE2B(false);
    }
  };

  const killSandbox = async () => {
    if (!sandboxId) return;
    
    try {
      await fetch('http://localhost:8000/kill-sandbox', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ sandbox_id: sandboxId }),
      });
      
      setE2bUrl('');
      setSandboxId('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to kill sandbox');
    }
  };

  return (
    <div className="min-h-screen bg-canvas">
      {/* Header */}
      <header className="bg-canvas sticky top-0 z-50 border-b border-border-subtle">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <a href="/" className="text-2xl font-bold text-ink">
              Patents<span className="text-accent-green">With</span>Code
            </a>
            <div className="flex items-center gap-4">
              {code && !e2bUrl && (
                <button
                  onClick={runInE2B}
                  disabled={loadingE2B}
                  className="px-6 py-2 bg-accent-green text-ink rounded-full font-medium
                           hover:bg-ink hover:text-surface transition-all duration-300
                           disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loadingE2B ? '⏳ Starting...' : '🎮 Run Demo'}
                </button>
              )}
              {e2bUrl && (
                <div className="flex items-center gap-3">
                  <a
                    href={e2bUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-6 py-2 bg-accent-green text-ink rounded-full font-medium
                             hover:bg-ink hover:text-surface transition-all duration-300"
                  >
                    🔗 Open Demo
                  </a>
                  <button
                    onClick={killSandbox}
                    className="px-4 py-2 bg-red-500 text-white rounded-full font-medium
                             hover:bg-red-600 transition-all duration-300"
                  >
                    ❌ Kill
                  </button>
                </div>
              )}
              <a
                href="http://localhost:3000/examples/swipe-interface.html"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-ink-secondary hover:text-accent-green transition-colors"
              >
                📦 View Example Demo
              </a>
              <a
                href="/search-results"
                className="text-sm text-ink-secondary hover:text-accent-green transition-colors"
              >
                ← Back to Search
              </a>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Title Section */}
        <div className="mb-8" style={{ animation: 'fadeInUp 0.6s ease-out' }}>
          <h1 className="text-4xl font-bold text-ink mb-2">Generated Demo</h1>
          <p className="text-lg text-ink-secondary">
            Patent → Specs → Code → Interactive Demo
          </p>
          {patentUrl && (
            <a
              href={patentUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-accent-green hover:underline mt-2 inline-block"
            >
              {patentUrl}
            </a>
          )}
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-2xl p-6 mb-6">
            <p className="text-red-800 font-medium">Error: {error}</p>
          </div>
        )}

        {/* Tab Navigation */}
        <div
          className="bg-surface rounded-3xl p-2 mb-6 inline-flex gap-2 shadow-[0_10px_40px_rgba(0,0,0,0.04)]"
          style={{ animation: 'scaleIn 0.7s ease-out' }}
        >
          <button
            onClick={() => setActiveTab('patent')}
            className={`px-6 py-3 rounded-full font-medium transition-all duration-300 ${
              activeTab === 'patent'
                ? 'bg-ink text-surface'
                : 'bg-transparent text-ink-secondary hover:bg-canvas'
            }`}
          >
            Patent Text
          </button>
          <button
            onClick={() => setActiveTab('specs')}
            disabled={!specs && !loadingSpecs}
            className={`px-6 py-3 rounded-full font-medium transition-all duration-300 ${
              activeTab === 'specs'
                ? 'bg-ink text-surface'
                : 'bg-transparent text-ink-secondary hover:bg-canvas disabled:opacity-30'
            }`}
          >
            Specs {loadingSpecs && '⏳'}
          </button>
          <button
            onClick={() => setActiveTab('code')}
            disabled={!code && !loadingCode}
            className={`px-6 py-3 rounded-full font-medium transition-all duration-300 ${
              activeTab === 'code'
                ? 'bg-ink text-surface'
                : 'bg-transparent text-ink-secondary hover:bg-canvas disabled:opacity-30'
            }`}
          >
            Code {loadingCode && '⏳'}
          </button>
          <button
            onClick={() => setActiveTab('demo')}
            disabled={!code}
            className={`px-6 py-3 rounded-full font-medium transition-all duration-300 ${
              activeTab === 'demo'
                ? 'bg-ink text-surface'
                : 'bg-transparent text-ink-secondary hover:bg-canvas disabled:opacity-30'
            }`}
          >
            Demo
          </button>
        </div>

        {/* Content Area */}
        <div className="bg-surface rounded-3xl p-8 shadow-[0_10px_40px_rgba(0,0,0,0.04)]">
          {/* Patent Text Tab */}
          {activeTab === 'patent' && (
            <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
              <h2 className="text-2xl font-bold text-ink mb-4">Patent Text</h2>
              <div className="bg-canvas rounded-xl p-6 border border-border-subtle max-h-[600px] overflow-y-auto">
                <pre className="whitespace-pre-wrap text-sm text-ink-secondary font-mono">
                  {patentText || 'No patent text provided'}
                </pre>
              </div>
              {patentText && !specs && (
                <div className="mt-6 text-center">
                  <button
                    onClick={generateSpecs}
                    disabled={loadingSpecs}
                    className="px-8 py-4 bg-accent-green text-ink rounded-full font-bold text-lg
                             transition-all duration-300 hover:bg-ink hover:text-surface
                             disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loadingSpecs ? 'Generating Specs...' : '→ Generate Specs'}
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Specs Tab */}
          {activeTab === 'specs' && (
            <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
              <h2 className="text-2xl font-bold text-ink mb-4">Implementation Specs</h2>
              {loadingSpecs ? (
                <div className="flex flex-col items-center justify-center py-20">
                  <div className="w-12 h-12 border-4 border-accent-green border-t-transparent rounded-full animate-spin mb-4" />
                  <p className="text-ink-secondary">Generating specs...</p>
                </div>
              ) : specs ? (
                <>
                  <div className="bg-canvas rounded-xl p-6 border border-border-subtle max-h-[600px] overflow-y-auto">
                    <pre className="whitespace-pre-wrap text-sm text-ink font-mono">
                      {specs}
                    </pre>
                  </div>
                  {!code && (
                    <div className="mt-6 text-center">
                      <button
                        onClick={generateCode}
                        disabled={loadingCode}
                        className="px-8 py-4 bg-accent-green text-ink rounded-full font-bold text-lg
                                 transition-all duration-300 hover:bg-ink hover:text-surface
                                 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {loadingCode ? 'Generating Code...' : 'Generate Code'}
                      </button>
                    </div>
                  )}
                </>
              ) : (
                <p className="text-ink-secondary">No specs generated yet</p>
              )}
            </div>
          )}

          {/* Code Tab */}
          {activeTab === 'code' && (
            <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
              <h2 className="text-2xl font-bold text-ink mb-4">React Implementation</h2>
              {loadingCode ? (
                <div className="flex flex-col items-center justify-center py-20">
                  <div className="w-12 h-12 border-4 border-accent-green border-t-transparent rounded-full animate-spin mb-4" />
                  <p className="text-ink-secondary">Generating code with Claude Code sandbox...</p>
                </div>
              ) : code ? (
                <div className="bg-canvas rounded-xl p-6 border border-border-subtle max-h-[600px] overflow-y-auto">
                  <pre className="whitespace-pre-wrap text-sm text-ink-secondary font-mono">
                    {code}
                  </pre>
                </div>
              ) : (
                <p className="text-ink-secondary">No code generated yet</p>
              )}
            </div>
          )}

          {/* Demo Tab */}
          {activeTab === 'demo' && (
            <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
              <h2 className="text-2xl font-bold text-ink mb-4">Interactive Demo</h2>
              {loadingE2B ? (
                <div className="flex flex-col items-center justify-center py-20">
                  <div className="w-12 h-12 border-4 border-accent-green border-t-transparent rounded-full animate-spin mb-4" />
                  <p className="text-ink-secondary">Starting E2B sandbox...</p>
                </div>
              ) : e2bUrl ? (
                <div>
                  <div className="mb-6 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="text-sm text-ink-secondary">Live at:</span>
                      <a
                        href={e2bUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-accent-green hover:underline font-mono text-sm"
                      >
                        {e2bUrl}
                      </a>
                    </div>
                    <button
                      onClick={killSandbox}
                      className="px-4 py-2 bg-red-500 text-white rounded-full font-medium
                               hover:bg-red-600 transition-all duration-300"
                    >
                      ❌ Kill Sandbox
                    </button>
                  </div>
                  <div className="bg-canvas rounded-2xl p-6 border border-border-subtle">
                    <iframe
                      src={e2bUrl}
                      className="w-full h-[600px] border-0 rounded-xl"
                      title="E2B Demo"
                    />
                  </div>
                </div>
              ) : code ? (
                <div className="text-center py-20">
                  <p className="text-ink-secondary mb-6">Click "Run Demo" in the header to start E2B sandbox</p>
                  <button
                    onClick={runInE2B}
                    disabled={loadingE2B}
                    className="px-8 py-4 bg-accent-green text-ink rounded-full font-bold text-lg
                             transition-all duration-300 hover:bg-ink hover:text-surface
                             disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loadingE2B ? '⏳ Starting...' : '🎮 Run Demo in E2B'}
                  </button>
                </div>
              ) : (
                <p className="text-ink-secondary">Generate code first to see the demo</p>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
