import React, { useRef, useState, useEffect, useMemo } from 'react';
import { Play, Pause, Volume2, VolumeX, Maximize, Minimize, RotateCcw, SkipForward } from 'lucide-react';
import LanguageSelector from './LanguageSelector';
import AccessibilityControls from './AccessibilityControls';
import { AUDIO_LANGUAGES } from './languages';

const getEventTriggerTime = (event) => {
  const startTime = Number(event?.start_time);
  if (Number.isFinite(startTime)) return startTime;
  const triggerTime = Number(event?.trigger_timestamp);
  if (Number.isFinite(triggerTime)) return triggerTime;
  return Number(event?.timestamp) || 0;
};

export default function VideoPlayer({ lecture, metadata }) {
  const videoRef = useRef(null);
  const audioRef = useRef(null);
  const playerRef = useRef(null);
  const userPausedRef = useRef(false);
  const lastVideoTimeRef = useRef(0);
  const pendingAudioStartRef = useRef(null);
  const adEnabledRef = useRef(true);
  const languageRef = useRef('en');

  const [isPlaying, setIsPlaying] = useState(false);
  const [isAdPlaying, setIsAdPlaying] = useState(false);
  const [adEnabled, setAdEnabled] = useState(true);
  const [language, setLanguage] = useState(() => {
    try {
      return window.localStorage.getItem('eduvision-audio-language') || 'en';
    } catch {
      return 'en';
    }
  });
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [muted, setMuted] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [currentEvent, setCurrentEvent] = useState(null);
  const [playedEventIds, setPlayedEventIds] = useState(new Set());
  const [announcement, setAnnouncement] = useState('');
  const [isAudioLoading, setIsAudioLoading] = useState(false);

  const events = metadata?.events || [];
  const availableLanguages = useMemo(() => {
    if (!events.length) return AUDIO_LANGUAGES.filter(({ code }) => code === 'en' || code === 'hi');
    const tracks = AUDIO_LANGUAGES.filter(({ code }) => events.every((event) => Boolean(event[`audio_${code}`])));
    return tracks.length ? tracks : AUDIO_LANGUAGES.filter(({ code }) => code === 'en' || code === 'hi');
  }, [events]);
  const languageName = availableLanguages.find(({ code }) => code === language)?.label || 'English';

  const resolveMediaUrl = (url) => {
    if (!url) return '';
    try {
      return new URL(url, window.location.href).href;
    } catch {
      return '';
    }
  };

  const cancelPendingAudioStart = () => {
    const pendingStart = pendingAudioStartRef.current;
    if (pendingStart && audioRef.current) audioRef.current.removeEventListener('canplay', pendingStart);
    pendingAudioStartRef.current = null;
  };

  useEffect(() => { adEnabledRef.current = adEnabled; }, [adEnabled]);
  useEffect(() => { languageRef.current = language; }, [language]);
  useEffect(() => () => cancelPendingAudioStart(), []);

  useEffect(() => {
    if (events.length && !availableLanguages.some(({ code }) => code === language)) {
      setLanguage('en');
      try {
        window.localStorage.setItem('eduvision-audio-language', 'en');
      } catch {
        // Playback still works when browser storage is unavailable.
      }
    }
  }, [events, availableLanguages, language]);

  const handleLanguageChange = (nextLanguage) => {
    setLanguage(nextLanguage);
    languageRef.current = nextLanguage;
    try {
      window.localStorage.setItem('eduvision-audio-language', nextLanguage);
    } catch {
      // Keep the current selection for this page even when storage is unavailable.
    }

    // If the user changes language while a description is playing, switch the
    // audio track too. The displayed explanation already follows `language`.
    if (!isAdPlaying || !currentEvent || !audioRef.current) return;
    const nextAudioSrc = currentEvent[`audio_${nextLanguage}`];
    if (!nextAudioSrc) {
      audioRef.current.pause();
      resumeVideoPlayback();
      setAnnouncement(`${AUDIO_LANGUAGES.find(({ code }) => code === nextLanguage)?.label || nextLanguage} narration is not available for this diagram.`);
      return;
    }

    const audio = audioRef.current;
    cancelPendingAudioStart();
    audio.pause();
    audio.src = resolveMediaUrl(nextAudioSrc);
    audio.currentTime = 0;
    audio.preload = 'auto';
    audio.load();
    audio.play().catch((error) => {
      console.error('Audio playback error:', error);
      resumeVideoPlayback();
      setAnnouncement(`${AUDIO_LANGUAGES.find(({ code }) => code === nextLanguage)?.label || nextLanguage} audio could not be played.`);
    });
  };

  const toggleAudioDescriptions = () => {
    const nextEnabled = !adEnabled;
    setAdEnabled(nextEnabled);
    adEnabledRef.current = nextEnabled;
    setAnnouncement(`Audio description ${nextEnabled ? 'enabled' : 'disabled'}`);
    if (!nextEnabled && isAdPlaying) {
      audioRef.current?.pause();
      resumeVideoPlayback();
    }
  };

  // Global Keyboard Navigation Listener
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Don't intercept when focused inside text input or textarea
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) return;

      switch (e.key) {
        case ' ':
        case 'k':
        case 'K':
          e.preventDefault();
          togglePlay();
          break;
        case 'm':
        case 'M':
          e.preventDefault();
          toggleMute();
          break;
        case 'd':
        case 'D':
          e.preventDefault();
          toggleAudioDescriptions();
          break;
        case 'l':
        case 'L':
          e.preventDefault();
          if (availableLanguages.length) {
            const currentIndex = availableLanguages.findIndex(({ code }) => code === language);
            const nextLanguage = availableLanguages[(currentIndex + 1) % availableLanguages.length];
            handleLanguageChange(nextLanguage.code);
            setAnnouncement(`Language switched to ${nextLanguage.label}`);
          }
          break;
        case 'n':
        case 'N':
          e.preventDefault();
          jumpToNextDiagram();
          break;
        case 'p':
        case 'P':
          e.preventDefault();
          jumpToPrevDiagram();
          break;
        case 'ArrowLeft':
          e.preventDefault();
          if (videoRef.current) {
            const newTime = Math.max(0, videoRef.current.currentTime - 5);
            performSeek(newTime);
          }
          break;
        case 'ArrowRight':
          e.preventDefault();
          if (videoRef.current) {
            const newTime = Math.min(duration, videoRef.current.currentTime + 5);
            performSeek(newTime);
          }
          break;
        default:
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isPlaying, isAdPlaying, adEnabled, language, duration, events, availableLanguages]);

  const jumpToNextDiagram = () => {
    if (!events.length || !videoRef.current) return;
    const cur = videoRef.current.currentTime;
    const nextEvt = events.find(evt => getEventTriggerTime(evt) > cur + 0.5);
    if (nextEvt) {
      const triggerTime = getEventTriggerTime(nextEvt);
      performSeek(triggerTime);
      setAnnouncement(`Jumped to next diagram at ${triggerTime} seconds: ${nextEvt.diagram_type}`);
    } else {
      setAnnouncement("No subsequent diagram events in this lecture.");
    }
  };

  const jumpToPrevDiagram = () => {
    if (!events.length || !videoRef.current) return;
    const cur = videoRef.current.currentTime;
    const pastEvts = events.filter(evt => getEventTriggerTime(evt) < cur - 1.0);
    if (pastEvts.length > 0) {
      const prevEvt = pastEvts[pastEvts.length - 1];
      const triggerTime = getEventTriggerTime(prevEvt);
      performSeek(triggerTime);
      setAnnouncement(`Jumped to previous diagram at ${triggerTime} seconds: ${prevEvt.diagram_type}`);
    } else {
      setAnnouncement("No prior diagram events in this lecture.");
    }
  };

  // Handle Video Time Update & Diagram Event Audio Triggers
  const handleTimeUpdate = () => {
    if (!videoRef.current) return;

    const time = videoRef.current.currentTime;
    const previousTime = lastVideoTimeRef.current;
    lastVideoTimeRef.current = time;
    setCurrentTime(time);
    if (isAdPlaying || !adEnabledRef.current) return;

    // Detect a crossed timestamp rather than requiring a timeupdate to land
    // inside a narrow window. Browsers can skip over that window while
    // buffering, resuming, or playing at a higher playback rate.
    for (const evt of events) {
      const triggerTime = getEventTriggerTime(evt);
      const crossedTrigger = triggerTime >= previousTime - 0.25 && triggerTime <= time + 0.25;
      const startedNearTrigger = Math.abs(time - triggerTime) <= 0.35;
      if (!playedEventIds.has(evt.event_id) && (crossedTrigger || startedNearTrigger)) {
        triggerAudioDescription(evt);
        break;
      }
    }
  };

  const triggerAudioDescription = (evt) => {
    if (!videoRef.current || !audioRef.current) return;

    const selectedLanguage = languageRef.current;
    const audioSrc = resolveMediaUrl(evt[`audio_${selectedLanguage}`]);
    if (!audioSrc) {
      setPlayedEventIds((previous) => new Set(previous).add(evt.event_id));
      setAnnouncement(`${languageName} narration is not available for this diagram. Resuming the lecture.`);
      return;
    }

    // Pause lecture video
    videoRef.current.pause();
    setIsPlaying(false);
    setIsAdPlaying(true);
    setCurrentEvent(evt);
    setIsAudioLoading(true);
    userPausedRef.current = false;

    // Mark event as played
    setPlayedEventIds(prev => new Set(prev).add(evt.event_id));

    // Select audio & text based on language setting
    const diagramType = evt.diagram_type || 'diagram';

    const audio = audioRef.current;
    cancelPendingAudioStart();
    audio.pause();
    audio.src = audioSrc;
    audio.currentTime = 0;
    audio.preload = 'auto';
    audio.load();
    setAnnouncement(`Audio description playing: ${diagramType} in ${languageName}`);

    const startAudio = () => {
      pendingAudioStartRef.current = null;
      setIsAudioLoading(false);
      audio.play().catch((error) => {
        console.error('Audio description playback error:', error);
        resumeVideoPlayback();
        setAnnouncement(`${languageName} audio could not be played. Resuming the lecture.`);
      });
    };

    if (audio.readyState >= 3) {
      startAudio();
    } else {
      pendingAudioStartRef.current = startAudio;
      audio.addEventListener('canplay', startAudio, { once: true });
    }
  };

  const handleAudioEnded = () => {
    setIsAudioLoading(false);
    resumeVideoPlayback();
  };

  const skipAudioDescription = () => {
    if (!isAdPlaying) return;
    if (audioRef.current) {
      audioRef.current.pause();
      cancelPendingAudioStart();
      audioRef.current.currentTime = 0;
      audioRef.current.removeAttribute('src');
      audioRef.current.load();
    }
    setIsAudioLoading(false);
    userPausedRef.current = false;
    setIsAdPlaying(false);
    setCurrentEvent(null);
    setAnnouncement('Audio description skipped. Resuming the lecture.');
    if (videoRef.current) {
      setIsPlaying(true);
      videoRef.current.play().catch((error) => {
        console.error('Video playback error:', error);
        setIsPlaying(false);
        setAnnouncement('Could not resume the lecture video. Press Play to continue.');
      });
    }
  };

  const handleAudioError = () => {
    setIsAudioLoading(false);
    cancelPendingAudioStart();
    if (!isAdPlaying) return;
    resumeVideoPlayback();
    setAnnouncement(`${languageName} audio could not be loaded. Resuming the lecture.`);
  };

  const resumeVideoPlayback = () => {
    cancelPendingAudioStart();
    setIsAudioLoading(false);
    setIsAdPlaying(false);
    setCurrentEvent(null);
    if (!userPausedRef.current && videoRef.current) {
      setIsPlaying(true);
      setAnnouncement("Audio description finished. Resuming video.");
      videoRef.current.play().catch((error) => {
        console.error('Video playback error:', error);
        setIsPlaying(false);
        setAnnouncement('Could not resume the lecture video. Press Play to continue.');
      });
    } else {
      setAnnouncement("Audio description finished. Video paused.");
    }
  };

  const togglePlay = () => {
    if (isAdPlaying) {
      // If user pauses while AD is playing, track manual pause intent
      if (audioRef.current && !audioRef.current.paused) {
        audioRef.current.pause();
        userPausedRef.current = true;
        setAnnouncement("Audio description paused.");
      } else if (audioRef.current && audioRef.current.paused) {
        userPausedRef.current = false;
        setAnnouncement("Resuming audio description.");
        audioRef.current.play().catch((error) => {
          console.error('Audio playback error:', error);
          resumeVideoPlayback();
          setAnnouncement(`${languageName} audio could not be played.`);
        });
      }
      return;
    }

    if (!videoRef.current) return;

    if (isPlaying) {
      videoRef.current.pause();
      setIsPlaying(false);
      userPausedRef.current = true;
    } else {
      setIsPlaying(true);
      userPausedRef.current = false;
      videoRef.current.play().catch((error) => {
        console.error('Video playback error:', error);
        setIsPlaying(false);
        setAnnouncement('Could not play the lecture video.');
      });
    }
  };

  const performSeek = (seekTime) => {
    if (videoRef.current) {
      videoRef.current.currentTime = seekTime;
      lastVideoTimeRef.current = seekTime;
      setCurrentTime(seekTime);

      // Replayability / Seek Invalidation:
      // Clear playedEventIds for all events at or after seekTime so re-watching triggers AD again
      setPlayedEventIds(prev => {
        const nextSet = new Set(prev);
        events.forEach(evt => {
          if (getEventTriggerTime(evt) >= seekTime - 0.5) {
            nextSet.delete(evt.event_id);
          }
        });
        return nextSet;
      });

      // Stop any active AD audio on seek
      if (isAdPlaying && audioRef.current) {
        audioRef.current.pause();
        setIsAdPlaying(false);
        setCurrentEvent(null);
      }
    }
  };

  const handleSeek = (e) => {
    const seekTime = parseFloat(e.target.value);
    performSeek(seekTime);
  };

  const toggleMute = () => {
    if (videoRef.current) {
      const nextMuted = !muted;
      videoRef.current.muted = nextMuted;
      if (audioRef.current) audioRef.current.muted = nextMuted;
      setMuted(nextMuted);
    }
  };

  const changeVolume = (event) => {
    const nextVolume = Number(event.target.value);
    setVolume(nextVolume);
    setMuted(nextVolume === 0);
    if (videoRef.current) {
      videoRef.current.volume = nextVolume;
      videoRef.current.muted = nextVolume === 0;
    }
    if (audioRef.current) {
      audioRef.current.volume = nextVolume;
      audioRef.current.muted = nextVolume === 0;
    }
  };

  const toggleFullscreen = async () => {
    if (!playerRef.current) return;
    try {
      if (!document.fullscreenElement) await playerRef.current.requestFullscreen();
      else await document.exitFullscreen();
    } catch (error) {
      console.error('Fullscreen unavailable:', error);
    }
  };

  useEffect(() => {
    const syncFullscreen = () => setIsFullscreen(document.fullscreenElement === playerRef.current);
    document.addEventListener('fullscreenchange', syncFullscreen);
    return () => document.removeEventListener('fullscreenchange', syncFullscreen);
  }, []);

  const formatTime = (time) => `${Math.floor(time / 60)}:${String(Math.floor(time % 60)).padStart(2, '0')}`;

  return (
    <div ref={playerRef} className="video-player-shell">
      {/* Screen Reader Live Region for ARIA Announcements */}
      <div 
        role="status" 
        aria-live="polite" 
        style={{ position: 'absolute', width: '1px', height: '1px', overflow: 'hidden', clip: 'rect(0,0,0,0)' }}
      >
        {announcement}
      </div>

      {/* Video Container */}
      <div className="video-stage">
        <video
          ref={videoRef}
          src={resolveMediaUrl(lecture.video_url || "/storage/uploads/sample.mp4")}
          className="video-element"
          onTimeUpdate={handleTimeUpdate}
          onLoadedMetadata={() => setDuration(videoRef.current?.duration || 0)}
          onEnded={() => setIsPlaying(false)}
          onClick={togglePlay}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
          aria-label={lecture.title}
        />

        {/* Hidden HTML5 Audio Element for AD Playback */}
        <audio ref={audioRef} preload="auto" onEnded={handleAudioEnded} onError={handleAudioError} />

        {/* Overlay when Diagram AD is Active */}
        {isAdPlaying && currentEvent && (
          <div style={{
            position: 'absolute',
            inset: 0,
            background: 'rgba(15, 23, 42, 0.94)',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            padding: '1.5rem',
            textAlign: 'center',
            zIndex: 10
          }}>
            <div style={{ background: 'var(--accent-primary)', color: '#fff', padding: '0.4rem 1rem', borderRadius: '20px', fontSize: '0.85rem', fontWeight: 700, marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Volume2 className="spin" size={16} /> Audio Description Playing ({languageName})
              <span style={{ background: 'rgba(255,255,255,0.2)', padding: '0.1rem 0.5rem', borderRadius: '10px', fontSize: '0.75rem' }}>
                {currentEvent.diagram_state || "NEW DIAGRAM ENTRY"}
              </span>
            </div>
            {currentEvent.entry_context && (
              <div style={{ fontSize: '0.8rem', color: 'var(--accent-secondary)', marginBottom: '0.5rem', fontWeight: 600 }}>
                {currentEvent.entry_context}
              </div>
            )}
            
            {/* Visual Callout Overlay for Low-Vision and Sighted Peers */}
            {(currentEvent.annotated_image_url || currentEvent.image_url) && (
              <div style={{ maxWidth: '65%', maxHeight: '45%', marginBottom: '0.75rem', borderRadius: '8px', overflow: 'hidden', border: '2px solid var(--accent-primary)' }}>
                <img
                  src={currentEvent.annotated_image_url || currentEvent.image_url}
                  alt={`Diagram region visual callout for event ${currentEvent.event_id}`}
                  style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                />
              </div>
            )}

            <p style={{ fontSize: '1.1rem', color: '#fff', maxWidth: '700px', lineHeight: 1.4, marginBottom: '0.75rem', fontStyle: 'italic' }}>
              "{currentEvent[`explanation_${language}`]}"
            </p>

            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              {isAudioLoading ? 'Preparing audio description…' : 'Lecture paused for the diagram explanation. Press Space or K to pause narration.'}
            </span>
            <button
              type="button"
              onClick={skipAudioDescription}
              className="btn btn-primary"
              style={{ marginTop: '1rem' }}
              aria-label="Skip audio explanation and continue lecture"
            >
              <SkipForward size={17} /> Skip explanation and continue
            </button>
          </div>
        )}
      </div>

      {/* Interactive Player Controls */}
      <div className="video-controls">
        <div className="video-timeline">
          <input type="range" min="0" max={duration || 100} value={currentTime} onChange={handleSeek}
            style={{ '--progress': `${duration ? (currentTime / duration) * 100 : 0}%` }} aria-label="Seek video position" />
        </div>
        <div className="video-control-row">
          <div className="video-control-group">
            <button 
              onClick={togglePlay} 
              className="player-icon-button player-play-button"
              aria-label={isPlaying || isAdPlaying ? "Pause" : "Play"}
            >
              {isPlaying || (isAdPlaying && !audioRef.current?.paused) ? <Pause size={19} fill="currentColor" /> : <Play size={19} fill="currentColor" />}
            </button>

            <button onClick={toggleMute} className="player-icon-button" aria-label={muted ? "Unmute" : "Mute"}>
              {muted || volume === 0 ? <VolumeX size={18} /> : <Volume2 size={18} />}
            </button>
            <input className="volume-slider" type="range" min="0" max="1" step="0.05" value={muted ? 0 : volume} onChange={changeVolume} aria-label="Volume" />
            <span className="player-time">{formatTime(currentTime)} <span>/</span> {formatTime(duration)}</span>
          </div>
          <div className="video-control-group">

            <AccessibilityControls
              adEnabled={adEnabled}
              onToggle={toggleAudioDescriptions}
            />

            <button 
              onClick={jumpToPrevDiagram} 
              className="btn btn-secondary" 
              title="Jump to Previous Diagram (P)"
              aria-label="Jump to Previous Diagram"
            >
              <RotateCcw size={16} /> <span>Prev (P)</span>
            </button>

            <button 
              onClick={jumpToNextDiagram} 
              className="btn btn-secondary" 
              title="Jump to Next Diagram (N)"
              aria-label="Jump to Next Diagram"
            >
              <RotateCcw size={16} style={{ transform: 'scaleX(-1)' }} /> <span>Next (N)</span>
            </button>
          </div>

          <LanguageSelector
            currentLanguage={language}
            onChangeLanguage={handleLanguageChange}
            availableLanguages={availableLanguages}
          />
          <button onClick={toggleFullscreen} className="player-icon-button" aria-label={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}>
            {isFullscreen ? <Minimize size={18} /> : <Maximize size={18} />}
          </button>
        </div>
      </div>
    </div>
  );
}
