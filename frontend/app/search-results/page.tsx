'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';

interface SearchResult {
  title: string;
  url: string;
  snippet: string;
}

export default function SearchResultsPage() {
  const searchParams = useSearchParams();
  const query = searchParams.get('q') || '';
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedResult, setSelectedResult] = useState<SearchResult | null>(null);
  const [crawling, setCrawling] = useState(false);
  const [patentText, setPatentText] = useState<string>('');
  const [showSlowMessage, setShowSlowMessage] = useState(false);
  const [showCrawlSlowMessage, setShowCrawlSlowMessage] = useState(false);

  useEffect(() => {
    if (query) {
      fetchSearchResults();
    }
  }, [query]);

  useEffect(() => {
    // Show "taking too long" message after 5 seconds of loading
    let timer: NodeJS.Timeout;
    if (loading) {
      timer = setTimeout(() => {
        setShowSlowMessage(true);
      }, 5000);
    } else {
      setShowSlowMessage(false);
    }
    return () => clearTimeout(timer);
  }, [loading]);

  useEffect(() => {
    // Show "taking too long" message after 5 seconds of crawling
    let timer: NodeJS.Timeout;
    if (crawling) {
      timer = setTimeout(() => {
        setShowCrawlSlowMessage(true);
      }, 5000);
    } else {
      setShowCrawlSlowMessage(false);
    }
    return () => clearTimeout(timer);
  }, [crawling]);

  const fetchSearchResults = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch search results');
      }

      const data = await response.json();
      setResults(data.results || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleResultClick = async (result: SearchResult) => {
    setSelectedResult(result);
    setCrawling(true);
    setPatentText('');

    try {
      const response = await fetch('http://localhost:8000/scrape', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: result.url }),
      });

      if (!response.ok) {
        throw new Error('Failed to scrape patent');
      }

      const data = await response.json();
      setPatentText(data.text);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to scrape patent');
    } finally {
      setCrawling(false);
    }
  };

  const handleViewDemo = () => {
    if (selectedResult && patentText) {
      // Store patent data in sessionStorage to avoid URL length limits
      sessionStorage.setItem('patentData', JSON.stringify({
        text: patentText,
        url: selectedResult.url,
      }));
      window.location.href = '/results2';
    } else {
      // Fallback to old demo page
      window.location.href = '/results';
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
              <span className="text-sm text-ink-secondary font-mono">
                Search: "{query}"
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="text-center max-w-md mx-auto">
              <div className="inline-block w-12 h-12 border-4 border-accent-green border-t-transparent rounded-full animate-spin mb-4" />
              <p className="text-ink-secondary mb-6">Searching patents...</p>
              
              {showSlowMessage && (
                <div className="mt-8 space-y-4" style={{ animation: 'fadeInUp 0.6s ease-out' }}>
                  <p className="text-ink-secondary text-sm">
                    This is taking longer than expected...
                  </p>
                  <a
                    href="/results"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-block px-6 py-3 bg-accent-clay text-ink rounded-full font-medium
                             transition-all duration-300 hover:bg-accent-green hover:shadow-lg"
                  >
                    🎮 View Demo Example
                  </a>
                  <p className="text-ink-secondary/70 text-xs">
                    Opens in new tab while search continues
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Error State */}
        {error && !crawling && (
          <div className="bg-red-50 border border-red-200 rounded-2xl p-6 mb-6">
            <p className="text-red-800 font-medium">Error: {error}</p>
          </div>
        )}

        {/* Search Results */}
        {!loading && !selectedResult && results.length > 0 && (
          <div style={{ animation: 'fadeInUp 0.6s ease-out' }}>
            <h1 className="text-3xl font-bold text-ink mb-6">
              Top 10 Patent Results
            </h1>
            <div className="space-y-4">
              {results.map((result, index) => (
                <button
                  key={index}
                  onClick={() => handleResultClick(result)}
                  className="w-full bg-surface rounded-2xl p-6 text-left transition-all duration-300
                           hover:shadow-[0_10px_40px_rgba(0,0,0,0.08)] hover:-translate-y-1
                           border border-border-subtle hover:border-accent-green"
                  style={{ animation: `fadeInUp ${0.7 + index * 0.05}s ease-out` }}
                >
                  <h3 className="text-xl font-bold text-ink mb-2">{result.title}</h3>
                  <p className="text-sm text-accent-green font-mono mb-2">{result.url}</p>
                  {result.snippet && (
                    <p className="text-ink-secondary line-clamp-2">{result.snippet}</p>
                  )}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* No Results */}
        {!loading && !selectedResult && results.length === 0 && (
          <div className="text-center py-20">
            <p className="text-xl text-ink-secondary">No results found for "{query}"</p>
          </div>
        )}

        {/* Selected Result - Crawling State */}
        {selectedResult && crawling && (
          <div className="space-y-6" style={{ animation: 'fadeInUp 0.6s ease-out' }}>
            <button
              onClick={() => {
                setSelectedResult(null);
                setPatentText('');
              }}
              className="text-accent-green hover:text-ink transition-colors mb-4"
            >
              ← Back to results
            </button>

            <div className="bg-surface rounded-2xl p-8 border border-border-subtle">
              <h2 className="text-2xl font-bold text-ink mb-4">{selectedResult.title}</h2>
              <p className="text-sm text-accent-green font-mono mb-6">{selectedResult.url}</p>

              <div className="flex flex-col items-center justify-center py-20">
                <div className="relative mb-6">
                  <div className="w-16 h-16 border-4 border-accent-green border-t-transparent rounded-full animate-spin" />
                  <div className="absolute inset-0 w-16 h-16 border-4 border-accent-clay/30 border-t-transparent rounded-full animate-spin"
                       style={{ animationDirection: 'reverse', animationDuration: '1.5s' }} />
                </div>
                <p className="text-lg text-ink-secondary mb-2">Crawling patent content...</p>
                <p className="text-sm text-ink-secondary/70 mb-6">This may take a moment</p>
                
                {showCrawlSlowMessage && (
                  <div className="mt-8 space-y-4" style={{ animation: 'fadeInUp 0.6s ease-out' }}>
                    <p className="text-ink-secondary text-sm">
                      Still working on it...
                    </p>
                    <a
                      href="/results"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-block px-6 py-3 bg-accent-clay text-ink rounded-full font-medium
                               transition-all duration-300 hover:bg-accent-green hover:shadow-lg"
                    >
                      🎮 View Demo Example
                    </a>
                    <p className="text-ink-secondary/70 text-xs">
                      Opens in new tab while crawling continues
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Selected Result - Patent Content */}
        {selectedResult && !crawling && patentText && (
          <div className="space-y-6" style={{ animation: 'fadeInUp 0.6s ease-out' }}>
            <button
              onClick={() => {
                setSelectedResult(null);
                setPatentText('');
              }}
              className="text-accent-green hover:text-ink transition-colors mb-4"
            >
              ← Back to results
            </button>

            <div className="bg-surface rounded-2xl p-8 border border-border-subtle">
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-ink mb-2">{selectedResult.title}</h2>
                  <p className="text-sm text-accent-green font-mono">{selectedResult.url}</p>
                </div>
                <button
                  onClick={handleViewDemo}
                  className="px-6 py-3 bg-accent-green text-ink rounded-full font-bold
                           transition-all duration-300 hover:bg-ink hover:text-surface
                           shadow-[0_10px_40px_rgba(0,0,0,0.08)] hover:shadow-[0_20px_60px_rgba(0,0,0,0.12)]
                           hover:-translate-y-1 flex-shrink-0"
                >
                  🎮 View Interactive Demo
                </button>
              </div>

              {/* Patent Text */}
              <div className="prose prose-lg max-w-none">
                <div className="bg-canvas rounded-xl p-6 border border-border-subtle">
                  <pre className="whitespace-pre-wrap text-sm text-ink-secondary font-mono">
                    {patentText}
                  </pre>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
