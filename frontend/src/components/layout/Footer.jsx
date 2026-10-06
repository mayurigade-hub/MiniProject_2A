import React from 'react';
import { Eye } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="footer">
      <div className="container footer-inner">
        <span className="footer-mark"><Eye size={14} style={{ verticalAlign: '-2px', marginRight: 7 }} />EduVision · Diagram to speech</span>
        <span>Designed for more accessible STEM learning.</span>
      </div>
    </footer>
  );
}
