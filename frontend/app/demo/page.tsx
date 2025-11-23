'use client';

import { useState, useEffect, useMemo } from 'react';
import { useSearchParams } from 'next/navigation';

export default function DemoPage() {
  const searchParams = useSearchParams();
  const codeParam = searchParams.get('code');
  const [code, setCode] = useState<string>(codeParam || '');

  // Listen for postMessage from parent window
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.data.type === 'PATENT_CODE') {
        setCode(event.data.code);
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, []);

  // Convert React/TypeScript code to runnable HTML
  const htmlContent = useMemo(() => {
    if (!code) return '';

    // Extract code from markdown code blocks if present
    let cleanCode = code;
    const codeBlockMatch = code.match(/```(?:tsx?|jsx?|typescript|javascript)?\n([\s\S]*?)```/);
    if (codeBlockMatch) {
      cleanCode = codeBlockMatch[1];
    }

    // Remove import statements (we're using CDN React)
    cleanCode = cleanCode.replace(/import\s+.*?from\s+['"].*?['"];?\s*/g, '');
    
    // Remove CSS imports
    cleanCode = cleanCode.replace(/import\s+['"].*?\.css['"];?\s*/g, '');
    
    // Remove export statements
    cleanCode = cleanCode.replace(/export\s+default\s+/g, '');
    cleanCode = cleanCode.replace(/export\s+/g, '');

    // Create a standalone HTML document with React via CDN
    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Patent Demo</title>
  <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
  <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body {
      margin: 0;
      padding: 0;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
      overflow-x: hidden;
    }
    #root {
      width: 100%;
      height: 100vh;
    }
  </style>
</head>
<body>
  <div id="root"></div>
  <script type="text/babel">
    const { useState, useEffect, useRef, useMemo, useCallback } = React;
    
    ${cleanCode}
    
    // Find the default export or main component
    const AppComponent = typeof App !== 'undefined' ? App : 
                        typeof PatentDemo !== 'undefined' ? PatentDemo :
                        typeof Demo !== 'undefined' ? Demo :
                        () => React.createElement('div', { style: { padding: '20px', textAlign: 'center' } }, 
                          React.createElement('p', null, 'Component not found. Make sure to export a component named App, PatentDemo, or Demo.'));
    
    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(React.createElement(AppComponent));
  </script>
</body>
</html>`;
  }, [code]);

  if (!code) {
    return (
      <div className="min-h-screen bg-canvas flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-ink mb-4">No Demo Code</h1>
          <p className="text-ink-secondary">
            This page displays generated patent demos. Navigate here from the results page.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-canvas">
      {/* Header */}
      <header className="bg-canvas sticky top-0 z-50 border-b border-border-subtle">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <a href="/" className="text-2xl font-bold text-ink">
              Patents<span className="text-accent-green">With</span>Code
            </a>
            <button
              onClick={() => window.close()}
              className="text-sm text-ink-secondary hover:text-accent-green transition-colors"
            >
              Close Demo
            </button>
          </div>
        </div>
      </header>

      {/* Full-screen Demo */}
      <main className="h-[calc(100vh-73px)]">
        <iframe
          srcDoc={htmlContent}
          className="w-full h-full border-0"
          title="Patent Demo"
          sandbox="allow-scripts"
        />
      </main>
    </div>
  );
}
