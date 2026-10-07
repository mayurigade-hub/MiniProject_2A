import React, { useState, useEffect, useRef } from 'react';
import { Upload, X, Loader } from 'lucide-react';
import { uploadLecture, checkLectureStatus } from '../../api/client';

export default function UploadModal({ isOpen, onClose, onUploadSuccess }) {
  const [title, setTitle] = useState('');
  const [subject, setSubject] = useState('Physics');
  const [description, setDescription] = useState('');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [progressPct, setProgressPct] = useState(0);
  const [progressMsg, setProgressMsg] = useState('');
  const pollTimeoutRef = useRef(null);
  const stoppedRef = useRef(false);

  useEffect(() => {
    if (isOpen) return undefined;
    stoppedRef.current = true;
    window.clearTimeout(pollTimeoutRef.current);
    setLoading(false);
    return undefined;
  }, [isOpen]);

  useEffect(() => () => {
    stoppedRef.current = true;
    window.clearTimeout(pollTimeoutRef.current);
  }, []);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a video file to upload.');
      return;
    }

    setLoading(true);
    setError('');
    stoppedRef.current = false;
    setProgressPct(5);
    setProgressMsg('Uploading video file...');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title || 'Untitled Lecture');
    formData.append('subject', subject);
    formData.append('description', description);

    try {
      const res = await uploadLecture(formData);
      const lectureId = res.lecture_id;
      if (stoppedRef.current) return;

      const pollStatus = async () => {
        if (stoppedRef.current) return;
        try {
          const statusRes = await checkLectureStatus(lectureId);
          const info = statusRes.status_info;
          if (typeof info.progress_pct === 'number') setProgressPct(info.progress_pct);
          if (info.progress_message) setProgressMsg(info.progress_message);

          if (info.status === 'completed') {
            setLoading(false);
            onUploadSuccess(lectureId);
            onClose();
            return;
          } else if (info.status === 'failed') {
            setLoading(false);
            setError(info.error || 'Pipeline processing failed');
            return;
          }
        } catch (pollErr) {
          console.error('Status polling error:', pollErr);
        }
        if (!stoppedRef.current) {
          pollTimeoutRef.current = window.setTimeout(pollStatus, 1500);
        }
      };
      pollTimeoutRef.current = window.setTimeout(pollStatus, 1500);

    } catch (err) {
      if (stoppedRef.current) return;
      setLoading(false);
      setError(err.message || 'Upload failed');
    }
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(0,0,0,0.85)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1500,
      padding: '1rem'
    }} role="dialog" aria-modal="true" aria-labelledby="upload-title">
      <div className="card" style={{ maxWidth: '500px', width: '100%', position: 'relative' }}>
        <button
          onClick={onClose}
          style={{ position: 'absolute', top: '1rem', right: '1rem', background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
          aria-label="Close upload modal"
        >
          <X size={24} />
        </button>

        <h2 id="upload-title" style={{ fontSize: '1.4rem', marginBottom: '1rem' }}>Upload Lecture Video</h2>

        {error && (
          <div style={{ background: '#7f1d1d', color: '#fca5a5', padding: '0.75rem', borderRadius: '8px', marginBottom: '1rem', fontSize: '0.9rem' }}>
            {error}
          </div>
        )}

        {loading ? (
          <div style={{ textAlign: 'center', padding: '2rem 0' }}>
            <Loader className="spin" size={36} style={{ color: 'var(--accent-primary)', marginBottom: '1rem' }} />
            <h4 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Processing AI Vision & Audio Descriptions</h4>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.5rem' }}>{progressMsg}</p>
            
            {/* Progress Bar */}
            <div style={{ width: '100%', background: 'var(--bg-dark)', height: '10px', borderRadius: '5px', overflow: 'hidden', border: '1px solid var(--border-color)' }}>
              <div style={{ width: `${progressPct}%`, background: 'var(--accent-primary)', height: '100%', transition: 'width 0.4s ease' }} />
            </div>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.5rem', display: 'block' }}>{progressPct}% Completed</span>
          </div>
        ) : (
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.25rem', fontWeight: 600 }}>Lecture Title</label>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Binary Search Flowchart Logic"
                style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'var(--bg-dark)', color: 'var(--text-main)' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.25rem', fontWeight: 600 }}>Subject</label>
              <select
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'var(--bg-dark)', color: 'var(--text-main)' }}
              >
                <option value="Physics">Physics</option>
                <option value="Biology">Biology</option>
                <option value="Chemistry">Chemistry</option>
                <option value="Computer Science">Computer Science</option>
                <option value="Mathematics">Mathematics</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.25rem', fontWeight: 600 }}>Description</label>
              <textarea
                rows={3}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Brief description of topics and diagrams..."
                style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'var(--bg-dark)', color: 'var(--text-main)' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.25rem', fontWeight: 600 }}>Video File (MP4, WebM, MOV, M4V, MKV)</label>
              <input
                type="file"
                accept=".mp4,.webm,.mov,.m4v,.mkv,video/mp4,video/webm,video/quicktime,video/x-m4v,video/x-matroska"
                required
                onChange={(e) => setFile(e.target.files[0])}
                style={{ width: '100%', color: 'var(--text-muted)' }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
              <button type="button" onClick={onClose} className="btn btn-secondary">Cancel</button>
              <button type="submit" className="btn btn-primary">
                <Upload size={18} /> Upload & Process
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
