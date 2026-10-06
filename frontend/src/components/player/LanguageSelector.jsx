import React from 'react';
import { Captions, ChevronDown } from 'lucide-react';

export default function LanguageSelector({ currentLanguage, onChangeLanguage }) {
  return (
    <label className="language-select">
      <Captions size={16} aria-hidden="true" />
      <span className="sr-only">Audio description language</span>
      <span className="language-select-value">{currentLanguage === 'hi' ? 'हिंदी' : 'English'}</span>
      <ChevronDown size={14} aria-hidden="true" />
      <select value={currentLanguage} onChange={(event) => onChangeLanguage(event.target.value)} aria-label="Audio description language">
        <option value="en">English</option>
        <option value="hi">हिंदी (Hindi)</option>
      </select>
    </label>
  );
}
