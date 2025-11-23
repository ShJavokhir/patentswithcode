'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';

export default function RenderPage() {
  const searchParams = useSearchParams();
  const codeParam = searchParams.get('code');
  const [code, setCode] = useState<string>(codeParam || '');
  const [error, setError] = useState<string>('');

  useEffect(() => {
    // Also check sessionStorage for code
    if (!code) {
      const storedCode = sessionStorage.getItem('generatedCode');
      if (storedCode) {
        setCode(storedCode);
      }
    }
  }, []);

  useEffect(() => {
    if (!code) return;

    try {
      // Clean the code
      let cleanCode = code;
      
      // Extract from markdown if needed
      const codeBlockMatch = code.match(/```(?:tsx?|jsx?|typescript|javascript)?\n([\s\S]*?)```/);
      if (codeBlockMatch) {
        cleanCode = codeBlockMatch[1];
      }

      // Remove imports and exports
      cleanCode = cleanCode.replace(/import\s+.*?from\s+['"].*?['"];?\s*/g, '');
      cleanCode = cleanCode.replace(/import\s+['"].*?\.css['"];?\s*/g, '');
      cleanCode = cleanCode.replace(/export\s+default\s+/g, '');
      cleanCode = cleanCode.replace(/export\s+/g, '');

      // Create script element with the code
      const script = document.createElement('script');
      script.type = 'text/babel';
      script.innerHTML = `
        const { useState, useEffect, useRef, useMemo, useCallback } = React;
        
        ${cleanCode}
        
        // Try to find and render the component
        const findComponent = () => {
          // Check for common component names
          if (typeof App !== 'undefined') return App;
          if (typeof PatentDemo !== 'undefined') return PatentDemo;
          if (typeof Demo !== 'undefined') return Demo;
          if (typeof TouchScreenKeyboard !== 'undefined') return TouchScreenKeyboard;
          if (typeof SwipeKeyboard !== 'undefined') return SwipeKeyboard;
          
          // Try to find any function that looks like a component
          const globals = Object.keys(window).filter(key => {
            const val = window[key];
            return typeof val === 'function' && 
                   val.toString().includes('return') && 
                   (val.toString().includes('React.createElement') || 
                    val.toString().includes('jsx') ||
                    val.toString().includes('<'));
          });
          
          if (globals.length > 0) {
            return window[globals[0]];
          }
          
          return null;
        };
        
        const AppComponent = findComponent();
        
        if (AppComponent) {
          const root = ReactDOM.createRoot(document.getElementById('root'));
          root.render(React.createElement(AppComponent));
        } else {
          document.getElementById('root').innerHTML = '<div style="padding: 40px; text-align: center; color: #666;"><h2>Component Not Found</h2><p>Could not find a React component to render. Make sure your code exports a component.</p></div>';
        }
      `;

      document.body.appendChild(script);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to render component');
    }
  }, [code]);

  if (error) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <h2 style={{ color: '#e53e3e' }}>Render Error</h2>
        <p style={{ color: '#666' }}>{error}</p>
      </div>
    );
  }

  if (!code) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <h2 style={{ color: '#666' }}>No Code Provided</h2>
        <p style={{ color: '#999' }}>No code was provided to render.</p>
      </div>
    );
  }

  return <div id="root" style={{ width: '100%', height: '100vh' }} />;
}
