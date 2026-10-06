import React from 'react';
import { Eye, Volume2, ShieldCheck, ArrowRight, AudioLines, ScanEye, Languages, Play } from 'lucide-react';

const features = [
  { icon: Eye, title: 'See the structure', body: 'Visual STEM content is identified and interpreted in context, from plotted relationships to complex scientific diagrams.' },
  { icon: Volume2, title: 'Hear a clear explanation', body: 'Concise, teaching focused narration explains what matters in the figure and how its parts connect.' },
  { icon: ShieldCheck, title: 'Stay with the lecture', body: 'Playback pauses for each description, then continues when the narration ends. Students control language and replay.' },
];

const steps = [
  ['01', 'Extract frames', 'Lecture frames are sampled and mapped to their exact timestamps.'],
  ['02', 'Understand diagrams', 'Vision and OCR identify diagram elements and supporting text.'],
  ['03', 'Create narration', 'Short explanations are generated and voiced in English and Hindi.'],
  ['04', 'Learn in sync', 'Descriptions play at the right moment, then the video resumes.'],
];

export default function Landing({ setView }) {
  return (
    <main className="container landing">
      <section className="hero">
        <div className="hero-copy">
          <div className="eyebrow"><span className="eyebrow-dot" /> Accessible STEM, in sync</div>
          <h1>Make every diagram part of the <span>lesson.</span></h1>
          <p>EduVision turns the visual moments in STEM lectures into clear spoken explanations, so students can follow the ideas behind every chart, structure, and equation.</p>
          <div className="hero-actions">
            <button onClick={() => setView('catalog')} className="btn btn-primary">Explore lectures <ArrowRight size={17} /></button>
            <button onClick={() => setView('catalog')} className="btn btn-secondary"><Play size={16} /> Browse the catalog</button>
          </div>
        </div>

        <div className="hero-art" aria-label="Illustration of a scientific diagram becoming spoken audio">
          <div className="signal-frame">
            <div className="signal-line" />
            <span className="signal-label a">Diagram detected</span>
            <span className="signal-label b">Structure mapped</span>
            <span className="signal-label c">English · हिंदी</span>
            <span className="signal-label d">Lecture 04:32</span>
            <div className="signal-core"><AudioLines size={46} strokeWidth={1.35} /></div>
          </div>
          <div className="hero-note"><span className="hero-note-icon"><Languages size={19} /></span><span><strong>Audio description ready</strong>English narration · 18 seconds</span></div>
        </div>
      </section>

      <section className="feature-section">
        <div className="section-kicker">Built around the learning moment</div>
        <h2 className="section-title">From visual information<br />to understanding.</h2>
        <p className="section-intro">An accessible lecture experience that keeps the visual explanation connected to the teacher’s lesson.</p>
        <div className="grid">
          {features.map(({ icon: Icon, title, body }) => <article className="card feature-card" key={title}>
            <div className="feature-icon"><Icon size={19} /></div>
            <h3>{title}</h3><p>{body}</p>
          </article>)}
        </div>
      </section>

      <section className="card process-panel">
        <div className="process-head">
          <div><div className="section-kicker">Behind each description</div><h2 className="section-title">A thoughtful path from frame to voice.</h2></div>
          <ScanEye size={32} color="var(--text-soft)" strokeWidth={1.4} aria-hidden="true" />
        </div>
        <div className="process-steps">
          {steps.map(([number, title, body]) => <div className="process-step" key={number}>
            <span className="step-index">{number}</span><h4>{title}</h4><p>{body}</p>
          </div>)}
        </div>
      </section>
    </main>
  );
}
