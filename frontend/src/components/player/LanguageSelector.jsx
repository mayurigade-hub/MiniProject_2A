import React from 'react';
import { Captions, ChevronDown } from 'lucide-react';
import { AUDIO_LANGUAGES } from './languages';

export default function LanguageSelector({ currentLanguage, onChangeLanguage, availableLanguages = AUDIO_LANGUAGES }) {
  const selectedLanguage = availableLanguages.find(({ code }) => code === currentLanguage);
  return (
    <label className="language-select">
      <Captions size={16} aria-hidden="true" />
      <span className="sr-only">Audio description language</span>
      <span className="language-select-value">{selectedLanguage?.label || 'English'}</span>
      <ChevronDown size={14} aria-hidden="true" />
      <select value={currentLanguage} onChange={(event) => onChangeLanguage(event.target.value)} aria-label="Audio description language">
        {availableLanguages.map(({ code, label }) => <option key={code} value={code}>{label}</option>)}
      </select>
    </label>
  );
}
