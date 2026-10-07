import React from 'react';
import { Play, Volume2, Pencil, Trash2 } from 'lucide-react';

export default function LectureCard({ lecture, onSelect, onEdit, onDelete, busy }) {
  const getSubjectBadge = (subject) => {
    return { bg: 'var(--bg-card-hover)', text: 'var(--text-main)' };
  };

  const badge = getSubjectBadge(lecture.subject);

  return (
    <article className="card lecture-card">
      <div>
        <div className="lecture-card-top">
          <span className="subject-badge" style={{ 
            backgroundColor: badge.bg, 
            color: badge.text, 
            padding: '5px 10px',
            borderRadius: '999px',
            fontSize: '11px',
            fontWeight: 600
          }}>
            {lecture.subject || 'General Science'}
          </span>
          <span className="event-count">
            <Volume2 size={14} /> {lecture.events_count || 0} Audio Descriptions
          </span>
        </div>

        <h3 style={{ fontSize: '1.2rem', marginBottom: '0.5rem', color: 'var(--text-main)' }}>
          {lecture.title}
        </h3>

        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.5rem', display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
          {lecture.description || 'Interactive lecture video with automated diagram vision analysis and bilingual audio description.'}
        </p>
      </div>

      <div className="lecture-card-actions">
        <button
          onClick={() => onSelect(lecture)}
          className="btn btn-primary"
          aria-label={`Play lecture: ${lecture.title}`}
        >
          <Play size={18} /> Play Lecture
        </button>
        <button onClick={() => onEdit(lecture)} className="btn btn-secondary" disabled={busy} aria-label={`Edit ${lecture.title}`} title="Edit lecture">
          <Pencil size={17} /> <span className="sr-only">Edit</span>
        </button>
        <button onClick={() => onDelete(lecture)} className="btn btn-danger" disabled={busy} aria-label={`Delete ${lecture.title}`} title="Delete lecture">
          <Trash2 size={17} /> <span className="sr-only">Delete</span>
        </button>
      </div>
    </article>
  );
}
