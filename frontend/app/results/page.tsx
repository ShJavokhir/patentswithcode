'use client';

import { useState } from 'react';

export default function ResultsPage() {
  const [activeTab, setActiveTab] = useState<'patent' | 'specs' | 'code'>('patent');

  // Mock data - in real app, this would come from API/database
  const patentId = 'US9733811';
  const patentTitle = 'Matching Process System and Method';

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
              <span className="text-sm text-ink-secondary font-mono">Patent: {patentId}</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Title Section */}
        <div className="mb-8" style={{ animation: 'fadeInUp 0.6s ease-out' }}>
          <h1 className="text-4xl font-bold text-ink mb-2">{patentTitle}</h1>
          <p className="text-lg text-ink-secondary">
            Interactive demo of patented swipe-based matching interaction
          </p>
        </div>

        {/* Tab Navigation - Progressive Disclosure */}
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
            Patent Document
          </button>
          <button
            onClick={() => setActiveTab('specs')}
            className={`px-6 py-3 rounded-full font-medium transition-all duration-300 ${
              activeTab === 'specs'
                ? 'bg-ink text-surface'
                : 'bg-transparent text-ink-secondary hover:bg-canvas'
            }`}
          >
            Technical Specs
          </button>
          <button
            onClick={() => setActiveTab('code')}
            className={`px-6 py-3 rounded-full font-medium transition-all duration-300 ${
              activeTab === 'code'
                ? 'bg-ink text-surface'
                : 'bg-transparent text-ink-secondary hover:bg-canvas'
            }`}
          >
            Implementation
          </button>
        </div>

        {/* Content Panels */}
        <div className="bg-surface rounded-3xl shadow-[0_10px_40px_rgba(0,0,0,0.04)] overflow-hidden">
          {activeTab === 'patent' && <PatentView />}
          {activeTab === 'specs' && <SpecsView />}
          {activeTab === 'code' && <CodeView />}
        </div>
      </main>
    </div>
  );
}

function PatentView() {
  return (
    <div className="p-8" style={{ animation: 'fadeIn 0.4s ease-out' }}>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-ink mb-4">Original Patent Document</h2>
        <div className="flex gap-3 mb-6">
          <span className="px-4 py-2 bg-accent-green/20 text-accent-green rounded-full text-sm font-medium">
            US9733811B2
          </span>
          <span className="px-4 py-2 bg-canvas rounded-full text-sm text-ink-secondary">
            Filed: Oct 21, 2013
          </span>
          <span className="px-4 py-2 bg-canvas rounded-full text-sm text-ink-secondary">
            Granted: Aug 15, 2017
          </span>
        </div>
      </div>

      {/* PDF Viewer */}
      <div className="bg-canvas rounded-2xl p-6 border border-border-subtle">
        <div className="aspect-[8.5/11] bg-white rounded-xl shadow-inner flex items-center justify-center">
          <iframe
            src="/examples/matching-process-US9733811.pdf"
            className="w-full h-full rounded-xl"
            title="Patent Document"
          />
        </div>
        <div className="mt-4 text-center">
          <a
            href="/examples/matching-process-US9733811.pdf"
            target="_blank"
            className="text-accent-green hover:underline text-sm font-medium"
          >
            Open in new tab →
          </a>
        </div>
      </div>

      {/* Patent Summary */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-canvas rounded-2xl p-6">
          <h3 className="text-lg font-bold text-ink mb-3">Abstract</h3>
          <p className="text-ink-secondary leading-relaxed font-mono text-sm">
            A method for profile matching includes receiving a plurality of user profiles,
            each comprising traits of a respective user. The method includes receiving a
            preference indication for a first user profile and determining a potential match
            user profile based on the preference indication.
          </p>
        </div>
        <div className="bg-canvas rounded-2xl p-6">
          <h3 className="text-lg font-bold text-ink mb-3">Inventors</h3>
          <ul className="space-y-2 text-ink-secondary font-mono text-sm">
            <li>• Sean Rad (Los Angeles, CA)</li>
            <li>• Todd M. Carrico (Melissa, TX)</li>
            <li>• Kenneth B. Hoskins (Plano, TX)</li>
            <li>• James C. Stone (Addison, TX)</li>
            <li>• Jonathan Badeen (North Hollywood, CA)</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

function SpecsView() {
  return (
    <div className="p-8" style={{ animation: 'fadeIn 0.4s ease-out' }}>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-ink mb-2">Technical Specification</h2>
        <p className="text-ink-secondary">
          Extracted implementation requirements for the core patented interaction
        </p>
      </div>

      <div className="prose prose-lg max-w-none">
        <div className="bg-canvas rounded-2xl p-8 font-mono text-sm leading-relaxed">
          <div className="mb-6">
            <h3 className="text-xl font-bold text-ink mb-3">Core Innovation</h3>
            <p className="text-ink-secondary">
              Gesture-based mutual matching system using swipeable profile cards with binary
              approval mechanism and anonymous preference disclosure.
            </p>
          </div>

          <div className="mb-6">
            <h3 className="text-xl font-bold text-ink mb-3">Implementation Overview</h3>
            <p className="text-ink-secondary">
              Single-page React component displaying sequential user profile cards that respond
              to horizontal swipe gestures (or button taps). Left swipe indicates rejection,
              right swipe indicates approval. When two users mutually approve each other's profiles,
              the system reveals the match and enables direct communication.
            </p>
          </div>

          <div className="mb-6">
            <h3 className="text-xl font-bold text-ink mb-3">Component Structure</h3>
            <ul className="space-y-2 text-ink-secondary ml-4">
              <li>• <strong>Main container:</strong> Full-screen viewport with centered card stack</li>
              <li>• <strong>Profile card:</strong> 400x600px card displaying photo, name, age, brief bio</li>
              <li>• <strong>Interaction buttons:</strong> Three circular buttons (Dislike, Info, Like)</li>
              <li>• <strong>Swipe overlay:</strong> Full-card overlay showing "NOPE" or "LIKE"</li>
              <li>• <strong>Match modal:</strong> Centered popup showing matched user photos</li>
            </ul>
          </div>

          <div className="mb-6">
            <h3 className="text-xl font-bold text-ink mb-3">Interaction Flow</h3>
            <ol className="space-y-2 text-ink-secondary ml-4 list-decimal">
              <li>User sees profile card with photo and basic info</li>
              <li>User can tap info button, swipe left (reject), or swipe right (approve)</li>
              <li>If mutual match exists, display match modal with both photos</li>
              <li>If no mutual match, present next profile card from stack</li>
              <li>Repeat until card stack depleted</li>
            </ol>
          </div>

          <div className="bg-surface rounded-xl p-6 mt-6">
            <h3 className="text-xl font-bold text-ink mb-3">Visual Details</h3>
            <ul className="space-y-2 text-ink-secondary ml-4">
              <li>• Card has rounded corners (8px radius)</li>
              <li>• Profile photo fills top 70% of card</li>
              <li>• Name/age overlay at bottom with semi-transparent gradient</li>
              <li>• Swipe overlay appears at 30° rotation when drag exceeds 50px threshold</li>
              <li>• "NOPE" text: red, bold, 72px, rotated -30°</li>
              <li>• "LIKE" text: green, bold, 72px, rotated 30°</li>
              <li>• Card exit animation: 200ms ease-out, translating 150% viewport width</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

function CodeView() {
  const [showPreview, setShowPreview] = useState(false);

  return (
    <div className="p-8" style={{ animation: 'fadeIn 0.4s ease-out' }}>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-ink mb-2">React Implementation</h2>
          <p className="text-ink-secondary">
            Working code demonstrating the patented swipe interaction
          </p>
        </div>
        <button
          onClick={() => setShowPreview(!showPreview)}
          className="px-6 py-3 bg-accent-green text-ink rounded-full font-medium
                   hover:bg-accent-green/80 transition-all duration-300"
        >
          {showPreview ? 'View Code' : 'Preview Demo'}
        </button>
      </div>

      {showPreview ? (
        <div className="bg-canvas rounded-2xl p-6">
          <div className="aspect-[9/16] max-w-md mx-auto bg-white rounded-3xl shadow-2xl overflow-hidden">
            <iframe
              src="/examples/swipe-interface.html"
              className="w-full h-full"
              title="Swipe Interface Demo"
            />
          </div>
          <p className="text-center mt-4 text-sm text-ink-secondary font-mono">
            Live interactive demo • Try swiping left or right
          </p>
        </div>
      ) : (
        <div className="bg-canvas rounded-2xl overflow-hidden">
          <div className="bg-ink text-surface px-6 py-3 flex items-center justify-between">
            <span className="font-mono text-sm">swipe-interface.html</span>
            <a
              href="/examples/swipe-interface.html"
              target="_blank"
              className="text-accent-green hover:underline text-sm"
            >
              Open in new tab →
            </a>
          </div>
          <div className="p-6 overflow-x-auto">
            <pre className="text-sm font-mono text-ink-secondary leading-relaxed">
              <code>{`<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Swipe Match Interface</title>
  <style>
    /* Sunset gradient background */
    body {
      background: linear-gradient(135deg,
        #FFB3BA 0%, #FFDFBA 50%, #E0BBE4 100%);
    }

    .profile-card {
      width: 400px;
      height: 600px;
      background: white;
      border-radius: 12px;
      cursor: grab;
      transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }

    .profile-card.dragging {
      cursor: grabbing;
    }

    /* Swipe animations */
    .profile-card.exit-left {
      animation: slideOutLeft 0.3s ease-out forwards;
    }

    .profile-card.exit-right {
      animation: slideOutRight 0.3s ease-out forwards;
    }

    @keyframes slideOutLeft {
      to {
        transform: translateX(-150%) rotate(-30deg);
        opacity: 0;
      }
    }

    @keyframes slideOutRight {
      to {
        transform: translateX(150%) rotate(30deg);
        opacity: 0;
      }
    }
  </style>
</head>
<body>
  <!-- Interactive swipe demo implementation -->
  <div id="root"></div>

  <script>
    // Swipe gesture detection
    // Match creation logic
    // Profile card stack management
  </script>
</body>
</html>`}</code>
            </pre>
          </div>
          <div className="px-6 pb-6">
            <div className="bg-surface rounded-xl p-4 border-l-4 border-accent-clay">
              <p className="text-sm text-ink-secondary font-mono">
                <strong className="text-accent-clay">Note:</strong> This is a simplified demonstration.
                Full source code includes gesture detection, match logic, and state management.
                View the complete implementation above.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
