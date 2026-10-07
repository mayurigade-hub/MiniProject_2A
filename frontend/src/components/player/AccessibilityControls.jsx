import React from 'react';
import { Volume2, VolumeX } from 'lucide-react';

export default function AccessibilityControls({ adEnabled, onToggle }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
      <button
        onClick={onToggle}
        className={`btn ${adEnabled ? 'btn-primary' : 'btn-secondary'}`}
        style={{
          backgroundColor: adEnabled ? 'var(--accent-secondary)' : undefined,
          color: adEnabled ? '#000' : undefined
        }}
        aria-pressed={adEnabled}
        aria-label="Toggle Audio Description mode"
        title="Toggle automatic diagram audio description pauses"
      >
        {adEnabled ? <Volume2 size={18} /> : <VolumeX size={18} />}
        <span>AD {adEnabled ? 'ON' : 'OFF'}</span>
      </button>
    </div>
  );
}
