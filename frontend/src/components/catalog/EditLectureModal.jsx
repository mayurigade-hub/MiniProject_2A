import React, { useEffect, useState } from 'react';
import { X } from 'lucide-react';

const SUBJECTS = ['Physics', 'Biology', 'Chemistry', 'Computer Science', 'Mathematics'];

export default function EditLectureModal({ lecture, onClose, onSave }) {
  const [title, setTitle] = useState(lecture.title || '');
  const [subject, setSubject] = useState(lecture.subject || 'Physics');
  const [description, setDescription] = useState(lecture.description || '');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    setTitle(lecture.title || '');
    setSubject(lecture.subject || 'Physics');
    setDescription(lecture.description || '');
    setError('');
  }, [lecture]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError('');
    try {
      await onSave({ title: title.trim(), subject: subject.trim(), description: description.trim() });
    } catch (saveError) {
      setError(saveError.message || 'Could not save lecture details.');
      setSaving(false);
    }
  };

  return (
    <div className="manage-modal-backdrop" role="presentation">
      <section className="card manage-modal" role="dialog" aria-modal="true" aria-labelledby="edit-lecture-title">
        <button className="manage-modal-close" onClick={onClose} disabled={saving} aria-label="Close edit lecture dialog">
          <X size={20} />
        </button>
        <h2 id="edit-lecture-title">Edit lecture</h2>
        <p className="manage-modal-intro">Update the title, subject, and description for this lecture.</p>
        {error && <p className="manage-modal-error" role="alert">{error}</p>}
        <form onSubmit={handleSubmit} className="manage-form">
          <label>
            <span>Lecture title</span>
            <input value={title} onChange={(event) => setTitle(event.target.value)} maxLength={200} required />
          </label>
          <label>
            <span>Subject</span>
            <select value={subject} onChange={(event) => setSubject(event.target.value)} required>
              {!SUBJECTS.includes(subject) && <option value={subject}>{subject}</option>}
              {SUBJECTS.map((value) => <option key={value} value={value}>{value}</option>)}
            </select>
          </label>
          <label>
            <span>Description</span>
            <textarea value={description} onChange={(event) => setDescription(event.target.value)} maxLength={2000} rows={4} />
          </label>
          <div className="manage-modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose} disabled={saving}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? 'Saving…' : 'Save changes'}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
