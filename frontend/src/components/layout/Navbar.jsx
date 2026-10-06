import React from 'react';
import { BookOpen, Moon, Sun } from 'lucide-react';

export default function Navbar({ currentView, setView, isHighContrast, toggleHighContrast }) {
  return (
    <header className="topbar">
      <div className="container topbar-inner">
        <a href="#home" className="brand" onClick={(event) => { event.preventDefault(); setView('landing'); }} aria-label="EduVision home">
          <span><span className="brand-name">EduVision</span><span className="brand-caption">Accessible STEM lectures</span></span>
        </a>
        <nav aria-label="Main navigation">
          <ul className="nav-links">
            <li><button onClick={() => setView('landing')} className={`btn ${currentView === 'landing' ? 'btn-primary' : 'btn-secondary'}`} aria-current={currentView === 'landing' ? 'page' : undefined}>Overview</button></li>
            <li><button onClick={() => setView('catalog')} className={`btn ${currentView !== 'landing' ? 'btn-primary' : 'btn-secondary'}`} aria-current={currentView === 'catalog' ? 'page' : undefined}><BookOpen size={15} /> Lectures</button></li>
          </ul>
        </nav>
        <div className="nav-actions">
          <button onClick={toggleHighContrast} className="btn btn-secondary" aria-label={isHighContrast ? 'Disable high contrast mode' : 'Enable high contrast mode'} title="Toggle high contrast mode">
            {isHighContrast ? <Sun size={16} /> : <Moon size={16} />}<span>{isHighContrast ? 'Standard contrast' : 'High contrast'}</span>
          </button>
        </div>
      </div>
    </header>
  );
}
