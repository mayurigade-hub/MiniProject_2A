import React from 'react';
import { Keyboard, X } from 'lucide-react';

export default function KeyboardShortcutsModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  const shortcuts = [
    { key: 'Space / K', action: 'Play or Pause lecture video' },
    { key: 'M', action: 'Mute or Unmute audio' },
    { key: 'AD / A', action: 'Toggle Audio Description Mode (ON / OFF)' },
    { key: 'L', action: 'Cycle through available audio description languages' },
    { key: 'H', action: 'Toggle High Contrast Accessibility Mode' },
    { key: 'Tab / Shift+Tab', action: 'Navigate accessible interactive controls' },
    { key: '?', action: 'Open Keyboard Shortcuts Guide' },
  ];

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(0,0,0,0.85)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 2000,
      padding: '1rem'
    }} role="dialog" aria-modal="true" aria-labelledby="shortcut-title">
      <div className="card" style={{ maxWidth: '550px', width: '100%', position: 'relative' }}>
        <button
          onClick={onClose}
          style={{ position: 'absolute', top: '1rem', right: '1rem', background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
          aria-label="Close keyboard shortcuts guide"
        >
          <X size={24} />
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
          <div style={{ background: 'var(--accent-primary)', padding: '0.5rem', borderRadius: '8px', display: 'flex' }}>
            <Keyboard size={24} color="#fff" />
          </div>
          <h2 id="shortcut-title" style={{ fontSize: '1.4rem', margin: 0 }}>Accessibility Keyboard Shortcuts</h2>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1.5rem' }}>
          {shortcuts.map((sc, idx) => (
            <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-dark)', padding: '0.6rem 1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
              <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>{sc.action}</span>
              <kbd style={{ background: 'var(--bg-card-hover)', color: 'var(--accent-secondary)', padding: '0.25rem 0.6rem', borderRadius: '6px', fontSize: '0.85rem', fontWeight: 700, border: '1px solid var(--border-color)' }}>
                {sc.key}
              </kbd>
            </div>
          ))}
        </div>

        <button onClick={onClose} className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }}>
          Got It
        </button>
      </div>
    </div>
  );
}
