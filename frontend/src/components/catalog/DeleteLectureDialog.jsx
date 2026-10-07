import React, { useState } from 'react';
import { X, Trash2 } from 'lucide-react';

export default function DeleteLectureDialog({ lecture, onClose, onConfirm }) {
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState('');

  const handleDelete = async () => {
    setDeleting(true);
    setError('');
    try {
      await onConfirm();
    } catch (deleteError) {
      setError(deleteError.message || 'Could not delete lecture.');
      setDeleting(false);
    }
  };

  return (
    <div className="manage-modal-backdrop" role="presentation">
      <section className="card manage-modal" role="alertdialog" aria-modal="true" aria-labelledby="delete-lecture-title" aria-describedby="delete-lecture-description">
        <button className="manage-modal-close" onClick={onClose} disabled={deleting} aria-label="Close delete lecture dialog">
          <X size={20} />
        </button>
        <div className="delete-dialog-icon"><Trash2 size={20} /></div>
        <h2 id="delete-lecture-title">Delete lecture?</h2>
        <p className="manage-modal-intro" id="delete-lecture-description">
          “{lecture.title}” and its generated audio and video files will be permanently deleted.
        </p>
        {error && <p className="manage-modal-error" role="alert">{error}</p>}
        <div className="manage-modal-actions">
          <button className="btn btn-secondary" onClick={onClose} disabled={deleting}>Cancel</button>
          <button className="btn btn-danger" onClick={handleDelete} disabled={deleting}>
            <Trash2 size={16} /> {deleting ? 'Deleting…' : 'Delete lecture'}
          </button>
        </div>
      </section>
    </div>
  );
}
