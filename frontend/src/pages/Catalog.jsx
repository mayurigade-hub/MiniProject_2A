import React, { useState, useEffect } from 'react';
import { Upload, Search, Filter, BookOpen, RefreshCw } from 'lucide-react';
import LectureCard from '../components/catalog/LectureCard';
import UploadModal from '../components/catalog/UploadModal';
import { fetchLectures } from '../api/client';

export default function Catalog({ onSelectLecture }) {
  const [lectures, setLectures] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [search, setSearch] = useState('');
  const [selectedSubject, setSelectedSubject] = useState('All');
  const [isUploadOpen, setIsUploadOpen] = useState(false);

  const loadCatalog = async () => {
    setLoading(true);
    setLoadError('');
    try {
      const data = await fetchLectures();
      setLectures(data.lectures || []);
    } catch (err) {
      console.error("Catalog load error:", err);
      setLoadError(err.message || 'Could not load the lecture catalog.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCatalog();
  }, []);

  const filteredLectures = lectures.filter(l => {
    const matchesSearch = l.title?.toLowerCase().includes(search.toLowerCase()) || l.description?.toLowerCase().includes(search.toLowerCase());
    const matchesSubject = selectedSubject === 'All' || l.subject?.toLowerCase() === selectedSubject.toLowerCase();
    return matchesSearch && matchesSubject;
  });

  return (
    <main className="container" style={{ paddingBottom: '2rem' }}>
      {/* Catalog Header */}
      <div className="page-heading">
        <div>
          <h1 style={{ fontSize: '2rem', fontWeight: 800 }}>Lecture Catalog</h1>
          <p style={{ color: 'var(--text-muted)' }}>Browse STEM lectures enhanced with AI diagram audio descriptions.</p>
        </div>

        <button onClick={() => setIsUploadOpen(true)} className="btn btn-primary">
          <Upload size={18} /> Upload New Lecture
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="card filter-panel">
        <div className="search-box">
          <Search size={18} style={{ color: 'var(--text-muted)' }} />
          <input
            type="text"
            placeholder="Search lectures by title or topic..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ background: 'none', border: 'none', color: '#fff', width: '100%', outline: 'none' }}
            aria-label="Search lectures"
          />
        </div>

        <div className="filter-tabs">
          <Filter size={18} style={{ color: 'var(--text-muted)' }} />
          {['All', 'Physics', 'Biology', 'Chemistry'].map(subj => (
            <button
              key={subj}
              onClick={() => setSelectedSubject(subj)}
              className={`btn ${selectedSubject === subj ? 'btn-primary' : 'btn-secondary'}`}
            >
              {subj}
            </button>
          ))}
        </div>
      </div>

      {/* Grid of Lectures */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '4rem 0', color: 'var(--text-muted)' }}>
          <RefreshCw className="spin" size={32} style={{ marginBottom: '1rem' }} />
          <p>Loading lecture catalog...</p>
        </div>
      ) : loadError ? (
        <div className="card empty-state" role="alert">
          <h3>Catalog could not be loaded</h3>
          <p style={{ color: 'var(--text-muted)', margin: '0.5rem 0 1.5rem' }}>{loadError}</p>
          <button onClick={loadCatalog} className="btn btn-secondary">Try again</button>
        </div>
      ) : filteredLectures.length === 0 ? (
        <div className="card empty-state">
          <BookOpen size={48} style={{ color: 'var(--text-muted)', marginBottom: '1rem' }} />
          <h3>No Lectures Found</h3>
          <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
            No lectures match your current search criteria. Upload a lecture video or reset filters.
          </p>
          <button onClick={() => { setSearch(''); setSelectedSubject('All'); }} className="btn btn-secondary">
            Reset Filters
          </button>
        </div>
      ) : (
        <div className="grid">
          {filteredLectures.map(lec => (
            <LectureCard key={lec.lecture_id} lecture={lec} onSelect={onSelectLecture} />
          ))}
        </div>
      )}

      {/* Upload Modal */}
      <UploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUploadSuccess={() => loadCatalog()}
      />
    </main>
  );
}
