import React, { useRef, useState } from 'react';
import { Play, Pause, RotateCcw, ShieldCheck, Terminal, Cpu, LayoutDashboard, BarChart3, CheckCircle2 } from 'lucide-react';

interface Chapter {
  title: string;
  timestamp: number;
  icon: React.ReactNode;
  description: string;
}

export const ProjectDemoSection: React.FC = () => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [currentTime, setCurrentTime] = useState<number>(0);
  const [duration, setDuration] = useState<number>(92);

  const chapters: Chapter[] = [
    {
      title: 'Terminal Telemetry',
      timestamp: 6,
      icon: <Terminal className="w-3.5 h-3.5 text-cyan-400" />,
      description: 'Interactive character-by-character shell command ingress in Cowrie',
    },
    {
      title: 'Animated Architecture',
      timestamp: 17,
      icon: <Cpu className="w-3.5 h-3.5 text-emerald-400" />,
      description: '8-stage circuit topology with animated data particles & flowing arrows',
    },
    {
      title: 'ML Classification',
      timestamp: 34,
      icon: <Cpu className="w-3.5 h-3.5 text-purple-400" />,
      description: 'Feature extraction, Platt sigmoid calibration, and metric distinctions',
    },
    {
      title: '10-Class Taxonomy',
      timestamp: 45,
      icon: <BarChart3 className="w-3.5 h-3.5 text-amber-400" />,
      description: 'Candidate probability distribution and confusion matrix',
    },
    {
      title: 'Executive Dashboard',
      timestamp: 53,
      icon: <LayoutDashboard className="w-3.5 h-3.5 text-indigo-400" />,
      description: 'Live SOC metrics, active sessions, and stage distribution charts',
    },
    {
      title: 'Empirical Verification',
      timestamp: 69,
      icon: <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />,
      description: 'Markov threat matrix, drift watchtower, and 166 passing pytest tests',
    },
  ];

  const togglePlay = () => {
    if (!videoRef.current) return;
    if (isPlaying) {
      videoRef.current.pause();
    } else {
      videoRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  const jumpTo = (seconds: number) => {
    if (!videoRef.current) return;
    videoRef.current.currentTime = seconds;
    if (!isPlaying) {
      videoRef.current.play();
      setIsPlaying(true);
    }
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
      if (videoRef.current.duration) {
        setDuration(videoRef.current.duration);
      }
    }
  };

  const handleEnded = () => {
    setIsPlaying(false);
  };

  return (
    <section id="demo" className="py-20 bg-[#060913] border-t border-slate-800/80 relative overflow-hidden">
      {/* Decorative background glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[400px] bg-cyan-900/10 rounded-full blur-[120px] pointer-events-none" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="text-center max-w-3xl mx-auto mb-12 space-y-3">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-950/60 border border-cyan-800/60 text-xs font-mono text-cyan-400 font-semibold">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Interactive Animated Tour · 92s Walkthrough · 1080p 30fps</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            How It Works: End-to-End Demonstration
          </h2>
          <p className="text-slate-400 text-sm sm:text-base leading-relaxed">
            Watch a comprehensive demonstration of real-time honeypot telemetry ingestion, feature canonicalization, calibrated machine learning intent classification, SOC dashboard visualization, and automated test execution.
          </p>
        </div>

        {/* Video Player Container */}
        <div className="max-w-5xl mx-auto">
          <div className="relative rounded-2xl overflow-hidden bg-[#090e1c] border border-slate-800 shadow-2xl shadow-cyan-950/30 group">
            <video
              ref={videoRef}
              src="/assets/demo_walkthrough.mp4"
              poster="/assets/demo_poster.png"
              preload="metadata"
              playsInline
              onTimeUpdate={handleTimeUpdate}
              onEnded={handleEnded}
              onPlay={() => setIsPlaying(true)}
              onPause={() => setIsPlaying(false)}
              className="w-full h-auto aspect-video object-cover cursor-pointer"
              onClick={togglePlay}
            />

            {/* Play/Pause Overlay Button (shown on hover or when paused) */}
            {!isPlaying && (
              <div
                onClick={togglePlay}
                className="absolute inset-0 bg-black/40 backdrop-blur-[2px] flex items-center justify-center cursor-pointer transition-all hover:bg-black/30"
              >
                <div className="w-20 h-20 rounded-full bg-cyan-500/90 hover:bg-cyan-400 text-black flex items-center justify-center shadow-lg shadow-cyan-500/50 transition-transform transform hover:scale-110">
                  <Play className="w-8 h-8 fill-black translate-x-0.5" />
                </div>
              </div>
            )}

            {/* In-Video Bar Controls */}
            <div className="p-4 bg-[#090e1c] border-t border-slate-800 flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <button
                  onClick={togglePlay}
                  className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white transition-colors"
                  title={isPlaying ? 'Pause' : 'Play'}
                >
                  {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 fill-white" />}
                </button>
                <button
                  onClick={() => jumpTo(0)}
                  className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                  title="Restart"
                >
                  <RotateCcw className="w-4 h-4" />
                </button>
                <div className="text-xs font-mono text-slate-400">
                  <span className="text-cyan-400 font-bold">{Math.floor(currentTime)}s</span> / {Math.floor(duration)}s
                </div>
              </div>

              <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
                <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span>1080p HD · Recorded from Live System</span>
              </div>
            </div>
          </div>

          {/* Interactive Chapter Quick-Jumps */}
          <div className="mt-6 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {chapters.map((ch, idx) => {
              const active = currentTime >= ch.timestamp && (idx === chapters.length - 1 || currentTime < chapters[idx + 1].timestamp);
              return (
                <button
                  key={ch.title}
                  onClick={() => jumpTo(ch.timestamp)}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    active
                      ? 'bg-cyan-950/40 border-cyan-500/60 shadow-sm shadow-cyan-500/20'
                      : 'bg-[#090e1c] border-slate-800/80 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center gap-1.5 mb-1">
                    {ch.icon}
                    <span className="text-xs font-bold text-white tracking-tight">{ch.title}</span>
                  </div>
                  <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">
                    {ch.description}
                  </p>
                </button>
              );
            })}
          </div>

          {/* What You Will Learn Card */}
          <div className="mt-8 p-5 rounded-xl bg-[#090e1c] border border-slate-800/90 grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-slate-300">
            <div className="space-y-1">
              <span className="font-bold text-white block uppercase tracking-wider text-[11px]">1. Real Ingestion Telemetry</span>
              <p className="text-slate-400 leading-relaxed">
                Demonstrates how Cowrie honeypot SSH commands (e.g. <code className="text-cyan-300">cat /etc/shadow</code>) are captured, stripped of noise wrappers, and normalized.
              </p>
            </div>
            <div className="space-y-1">
              <span className="font-bold text-white block uppercase tracking-wider text-[11px]">2. Calibrated Intent Profiling</span>
              <p className="text-slate-400 leading-relaxed">
                Exhibits how LinearSVC with sigmoid probability calibration predicts the intent class with 99.8% confidence in 11.8ms without executing attacker code.
              </p>
            </div>
            <div className="space-y-1">
              <span className="font-bold text-white block uppercase tracking-wider text-[11px]">3. SOC Analytics & Defense</span>
              <p className="text-slate-400 leading-relaxed">
                Walks through the executive dashboard, MITRE ATT&CK technique mapping, Markov progression forecasting, and hermetic pytest verification.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
