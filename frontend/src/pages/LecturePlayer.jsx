import React, { useState, useEffect } from 'react';
import { ArrowLeft, Clock, FileText, Eye, Volume2, Sparkles, RefreshCw, Keyboard, Image } from 'lucide-react';
import VideoPlayer from '../components/player/VideoPlayer';
import KeyboardShortcutsModal from '../components/player/KeyboardShortcutsModal';
import { fetchLectureDetails, fetchLectureMetadata } from '../api/client';

export default function LecturePlayer({ lectureId, onBack }) {
  const [lecture, setLecture] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('events'); // 'events' | 'breakdown' | 'annotations'
  const [isShortcutOpen, setIsShortcutOpen] = useState(false);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const [lecRes, metaRes] = await Promise.all([
          fetchLectureDetails(lectureId),
          fetchLectureMetadata(lectureId)
        ]);
        setLecture(lecRes.lecture);
        setMetadata(metaRes);
      } catch (err) {
        console.error("Error loading lecture details:", err);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [lectureId]);

  if (loading) {
    return (
      <div className="container" style={{ textAlign: 'center', padding: '5rem 0', color: 'var(--text-muted)' }}>
        <RefreshCw className="spin" size={32} style={{ marginBottom: '1rem' }} />
        <p>Loading lecture player & AI audio descriptions...</p>
      </div>
    );
  }

  if (!lecture) {
    return (
      <div className="container" style={{ paddingTop: '3rem' }}>
        <button onClick={onBack} className="btn btn-secondary"><ArrowLeft size={18} /> Back to Catalog</button>
        <p style={{ marginTop: '2rem' }}>Lecture details not found.</p>
      </div>
    );
  }

  return (
    <main className="container" style={{ paddingTop: '1.5rem', paddingBottom: '3rem' }}>
      <div className="player-toolbar">
        <button onClick={onBack} className="btn btn-secondary">
          <ArrowLeft size={18} /> Back to Catalog
        </button>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <a
            href={`/api/lectures/${lectureId}/export-notes`}
            download={`accessible_notes_${lectureId}.md`}
            className="btn btn-primary"
            style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}
            title="Download accessible study guide in Markdown for screen readers & Braille displays"
          >
            <FileText size={18} /> Download Accessible Notes (.md)
          </a>

          <button onClick={() => setIsShortcutOpen(true)} className="btn btn-secondary" title="Keyboard Shortcuts Guide">
            <Keyboard size={18} /> Shortcuts (?)
          </button>
        </div>
      </div>

      {/* Header Info */}
      <div className="player-info">
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginBottom: '0.5rem' }}>
          <span style={{ background: 'var(--accent-primary)', color: '#fff', padding: '0.2rem 0.6rem', borderRadius: '12px', fontSize: '0.75rem', fontWeight: 700 }}>
            {lecture.subject}
          </span>
          <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>ID: {lecture.lecture_id}</span>
        </div>

        <h1 style={{ fontSize: '2rem', fontWeight: 800, marginBottom: '0.5rem' }}>{lecture.title}</h1>
        <p style={{ color: 'var(--text-muted)' }}>{lecture.description}</p>
      </div>

      {/* Video Player */}
      <VideoPlayer lecture={lecture} metadata={metadata} />

      {/* Detailed Metadata Tabs */}
      <div className="card metadata-panel">
        <div className="tab-list">
          <button
            onClick={() => setActiveTab('events')}
            style={{
              padding: '0.75rem 1.25rem',
              border: 'none',
              background: 'none',
              borderBottom: activeTab === 'events' ? '3px solid var(--accent-primary)' : 'none',
              color: activeTab === 'events' ? 'var(--accent-primary)' : 'var(--text-muted)',
              fontWeight: 700,
              cursor: 'pointer'
            }}
          >
            Diagram Events Timeline ({metadata?.events?.length || 0})
          </button>

          <button
            onClick={() => setActiveTab('annotations')}
            style={{
              padding: '0.75rem 1.25rem',
              border: 'none',
              background: 'none',
              borderBottom: activeTab === 'annotations' ? '3px solid var(--accent-primary)' : 'none',
              color: activeTab === 'annotations' ? 'var(--accent-primary)' : 'var(--text-muted)',
              fontWeight: 700,
              cursor: 'pointer'
            }}
          >
            Visual Bounding-Box Overlays (M3.6)
          </button>

          <button
            onClick={() => setActiveTab('breakdown')}
            style={{
              padding: '0.75rem 1.25rem',
              border: 'none',
              background: 'none',
              borderBottom: activeTab === 'breakdown' ? '3px solid var(--accent-primary)' : 'none',
              color: activeTab === 'breakdown' ? 'var(--accent-primary)' : 'var(--text-muted)',
              fontWeight: 700,
              cursor: 'pointer'
            }}
          >
            AI Vision & OCR Technical Breakdown
          </button>
        </div>

        {activeTab === 'events' && (
          <div>
            {!metadata?.events || metadata.events.length === 0 ? (
              <p style={{ color: 'var(--text-muted)' }}>No diagram events detected in this lecture video.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {metadata.events.map((evt, idx) => (
                  <div key={evt.event_id} style={{ background: 'var(--bg-dark)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                      <span style={{ fontWeight: 700, color: 'var(--accent-secondary)' }}>
                        Diagram Event #{idx + 1} — Timestamp: {evt.timestamp}s
                      </span>
                      <span style={{ fontSize: '0.8rem', background: 'var(--bg-card-hover)', padding: '0.2rem 0.5rem', borderRadius: '4px' }}>
                        Type: {evt.diagram_type}
                      </span>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '0.75rem' }}>
                      <div>
                        <h5 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>English Audio Narrative</h5>
                        <p style={{ fontSize: '0.9rem' }}>"{evt.explanation_en}"</p>
                      </div>
                      <div>
                        <h5 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>हिंदी (Hindi) Audio Narrative</h5>
                        <p style={{ fontSize: '0.9rem' }}>"{evt.explanation_hi}"</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'annotations' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
            {metadata?.events?.map((evt, idx) => (
              <div key={evt.event_id} style={{ background: 'var(--bg-dark)', padding: '1rem', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
                <h4 style={{ fontSize: '1rem', marginBottom: '0.5rem', color: 'var(--accent-secondary)' }}>
                  Event #{idx + 1}: Bounding Box Region Callout
                </h4>
                <div style={{ width: '100%', aspectRatio: '16/9', background: '#000', borderRadius: '8px', overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <img
                    src={evt.annotated_image_url || evt.image_url || "/storage/sample.jpg"}
                    alt={`Annotated diagram region for event ${idx + 1}`}
                    style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }}
                    onError={(e) => { e.target.src = "https://placehold.co/600x400/1e293b/6366f1?text=Annotated+Diagram+Region"; }}
                  />
                </div>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                  Computer vision detected region box highlight (Contract 2).
                </p>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'breakdown' && (
          <div>
            {metadata?.events?.map((evt, idx) => (
              <div key={evt.event_id} style={{ marginBottom: '1.5rem', background: 'var(--bg-dark)', padding: '1rem', borderRadius: '8px' }}>
                <h4 style={{ color: 'var(--accent-primary)', marginBottom: '0.5rem' }}>Event #{idx + 1} ({evt.timestamp}s)</h4>
                
                <div style={{ marginBottom: '1rem' }}>
                  <h5 style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>OCR Extracted Text Context:</h5>
                  <pre style={{ background: 'var(--bg-card)', padding: '0.5rem', borderRadius: '4px', fontSize: '0.85rem', overflowX: 'auto', color: '#38bdf8' }}>
                    {evt.ocr_text || "No text extracted"}
                  </pre>
                </div>

                <div>
                  <h5 style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Groq VLM Visual Understanding:</h5>
                  <p style={{ fontSize: '0.9rem', color: 'var(--text-main)', whiteSpace: 'pre-line' }}>
                    {evt.vlm_analysis || "Visual understanding generated"}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <KeyboardShortcutsModal
        isOpen={isShortcutOpen}
        onClose={() => setIsShortcutOpen(false)}
      />
    </main>
  );
}
