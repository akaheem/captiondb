import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, SkipBack, SkipForward, Subtitles, Settings, Maximize, Minimize, Video, ChevronDown, Edit3, Copy, Volume2, VolumeX, Check } from 'lucide-react';
import { VideoProject, Scene } from '../types';

interface MainWorkspaceProps {
  currentProject: VideoProject;
  setCurrentProject: (proj: VideoProject) => void;
  currentScene: Scene;
  setCurrentScene: (scene: Scene) => void;
  projects: VideoProject[];
  setProjects: React.Dispatch<React.SetStateAction<VideoProject[]>>;
}

export default function MainWorkspace({ currentProject, setCurrentProject, currentScene, setCurrentScene, projects, setProjects }: MainWorkspaceProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [videoTime, setVideoTime] = useState(0);
  const [showToneDropdown, setShowToneDropdown] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const playerContainerRef = useRef<HTMLDivElement>(null);

  const [editText, setEditText] = useState('');
  const [isEditingCaption, setIsEditingCaption] = useState(false);
  const [copied, setCopied] = useState(false);

  // Sync edit text when scene or tone changes
  useEffect(() => {
    setEditText(currentScene.captions[currentScene.captions.selectedTone]);
    setIsEditingCaption(false);
  }, [currentScene.id, currentScene.captions.selectedTone]);

  // Video playback simulation
  const progressTimerRef = useRef<NodeJS.Timeout | null>(null);
  useEffect(() => {
    if (isPlaying) {
      progressTimerRef.current = setInterval(() => {
        setVideoTime((prev) => {
          if (prev >= currentProject.durationSeconds) {
            setIsPlaying(false);
            return 0;
          }
          return prev + 1;
        });
      }, 1000);
    } else if (progressTimerRef.current) {
      clearInterval(progressTimerRef.current);
    }
    return () => clearInterval(progressTimerRef.current!);
  }, [isPlaying, currentProject.durationSeconds]);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      playerContainerRef.current?.requestFullscreen().catch(err => {
        console.error(`Error attempting to enable full-screen mode: ${err.message} (${err.name})`);
      });
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  // Sync scene based on time
  useEffect(() => {
    const matchingScene = currentProject.scenes.find(
      (s) => videoTime >= s.secondsStart && videoTime <= s.secondsEnd
    );
    if (matchingScene && matchingScene.id !== currentScene.id) {
      setCurrentScene(matchingScene);
    }
  }, [videoTime, currentProject, currentScene, setCurrentScene]);

  // Update scene when project changes
  useEffect(() => {
    setVideoTime(0);
    if (currentProject.scenes.length > 0) {
      setCurrentScene(currentProject.scenes[0]);
    }
  }, [currentProject]);

  const handleToneChange = (tone: 'formal' | 'sarcastic' | 'humorousTech' | 'humorousNonTech') => {
    const updatedProjects = projects.map(p => {
      if (p.id !== currentProject.id) return p;
      return {
        ...p,
        scenes: p.scenes.map(s => s.id === currentScene.id ? { ...s, captions: { ...s.captions, selectedTone: tone } } : s)
      };
    });
    setProjects(updatedProjects);
    setCurrentScene({
      ...currentScene,
      captions: { ...currentScene.captions, selectedTone: tone }
    });
    setShowToneDropdown(false);
  };

  const handleSaveCaption = () => {
    const updatedProjects = projects.map(p => {
      if (p.id !== currentProject.id) return p;
      return {
        ...p,
        scenes: p.scenes.map(s => {
          if (s.id !== currentScene.id) return s;
          return {
            ...s,
            captions: { ...s.captions, [s.captions.selectedTone]: editText }
          };
        })
      };
    });
    setProjects(updatedProjects);
    setCurrentScene({
      ...currentScene,
      captions: { ...currentScene.captions, [currentScene.captions.selectedTone]: editText }
    });
    setIsEditingCaption(false);
  };

  const formatTime = (secs: number) => {
    const h = Math.floor(secs / 3600);
    const m = Math.floor((secs % 3600) / 60);
    const s = secs % 60;
    const pad = (num: number) => String(num).padStart(2, '0');
    return `${pad(h)}:${pad(m)}:${pad(s)}`;
  };

  const TONE_LABELS = {
    formal: 'Formal',
    sarcastic: 'Sarcastic',
    humorousTech: 'Humorous (Tech)',
    humorousNonTech: 'Humorous (Non-Tech)',
    audio: 'Audio Transcript',
    none: 'None'
  };

  const TONE_COLORS = {
    formal: 'text-blue-500 bg-blue-500/10 border-blue-500/20',
    sarcastic: 'text-purple-500 bg-purple-500/10 border-purple-500/20',
    humorousTech: 'text-orange-500 bg-orange-500/10 border-orange-500/20',
    humorousNonTech: 'text-pink-500 bg-pink-500/10 border-pink-500/20',
    audio: 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20',
    none: 'text-slate-500 bg-slate-500/10 border-slate-500/20'
  };

  const TONE_TEXT_COLORS = {
    formal: 'text-blue-500',
    sarcastic: 'text-purple-500',
    humorousTech: 'text-orange-500',
    humorousNonTech: 'text-pink-500',
    audio: 'text-emerald-500',
    none: 'text-slate-500'
  };

  return (
    <div className="flex-1 flex flex-col p-6 gap-6 max-w-6xl mx-auto w-full">
      {/* Video Player */}
      <div 
        ref={playerContainerRef}
        className="w-full bg-white border border-slate-200 rounded-xl overflow-hidden shadow-2xl flex flex-col relative"
      >
        <div 
          onClick={() => setIsPlaying(!isPlaying)}
          className="relative w-full aspect-video bg-black cursor-pointer overflow-hidden flex items-center justify-center"
        >
          <img src={currentProject.thumbnail} alt="Video" className="absolute inset-0 w-full h-full object-cover opacity-80" />
          
          {currentScene.captions.selectedTone !== 'none' && (
            <div className="absolute bottom-12 left-1/2 -translate-x-1/2 bg-black/80 text-white px-4 py-2 rounded text-base md:text-lg border border-slate-200 text-center shadow-lg pointer-events-none max-w-[80%] backdrop-blur-sm">
              "{currentScene.captions[currentScene.captions.selectedTone]}"
            </div>
          )}

          {!isPlaying && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/20 backdrop-blur-[1px]">
              <div className="w-16 h-16 rounded-full bg-[#00D4FF]/20 border border-[#00D4FF]/50 flex items-center justify-center shadow-[0_0_20px_rgba(0,212,255,0.3)]">
                <Play className="w-8 h-8 text-[#00D4FF] fill-[#00D4FF] ml-1" />
              </div>
            </div>
          )}
        </div>

        {/* Player Controls */}
        <div className="p-3 bg-slate-50 border-t border-slate-200 flex flex-col gap-2">
          {/* Scrubber */}
          <div 
            className="w-full h-1.5 bg-slate-200 rounded-full cursor-pointer relative"
            onClick={(e) => {
              const rect = e.currentTarget.getBoundingClientRect();
              const pct = (e.clientX - rect.left) / rect.width;
              setVideoTime(Math.floor(pct * currentProject.durationSeconds));
            }}
          >
            <div 
              className="absolute top-0 left-0 h-full bg-[#00D4FF] rounded-full shadow-[0_0_8px_rgba(0,212,255,0.8)]"
              style={{ width: `${(videoTime / currentProject.durationSeconds) * 100}%` }}
            />
          </div>

          {/* Controls Bar */}
          <div className="flex items-center justify-between text-[#122131] mt-1">
            <div className="flex items-center gap-4">
              <button onClick={() => setIsPlaying(!isPlaying)} className="hover:text-[#00D4FF]">
                {isPlaying ? <Pause className="w-5 h-5 fill-current" /> : <Play className="w-5 h-5 fill-current" />}
              </button>
              <button onClick={() => setVideoTime(Math.max(0, videoTime - 10))} className="hover:text-[#00D4FF]">
                <SkipBack className="w-4 h-4" />
              </button>
              <button onClick={() => setVideoTime(Math.min(currentProject.durationSeconds, videoTime + 10))} className="hover:text-[#00D4FF]">
                <SkipForward className="w-4 h-4" />
              </button>
              <span className="text-xs font-mono text-[#00D4FF] ml-2">
                {formatTime(videoTime)} <span className="text-slate-500">/ {formatTime(currentProject.durationSeconds)}</span>
              </span>
            </div>

            <div className="flex items-center gap-4 relative">
              {/* Tone Selector near Settings */}
              <div className="relative">
                <button 
                  onClick={() => setShowToneDropdown(!showToneDropdown)}
                  className={`flex items-center gap-1.5 text-xs font-bold bg-white border hover:border-slate-300 px-2.5 py-1.5 rounded transition-all ${TONE_TEXT_COLORS[currentScene.captions.selectedTone]} border-slate-200`}
                >
                  <Subtitles className="w-4 h-4" />
                  {TONE_LABELS[currentScene.captions.selectedTone]}
                  <ChevronDown className="w-3 h-3" />
                </button>
                {showToneDropdown && (
                  <div className="absolute bottom-full right-0 mb-2 w-48 bg-white border border-slate-200 rounded-lg shadow-xl overflow-hidden z-50">
                    {(Object.keys(TONE_LABELS) as Array<keyof typeof TONE_LABELS>).map(tone => (
                      <button
                        key={tone}
                        onClick={() => handleToneChange(tone as keyof typeof TONE_LABELS)}
                        className={`w-full text-left px-4 py-2 text-xs font-semibold hover:bg-slate-100 transition-colors ${
                          currentScene.captions.selectedTone === tone ? `bg-slate-50 ${TONE_TEXT_COLORS[tone]}` : TONE_TEXT_COLORS[tone]
                        }`}
                      >
                        {TONE_LABELS[tone as keyof typeof TONE_LABELS]}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <button onClick={() => setIsMuted(!isMuted)} className="hover:text-[#00D4FF]">
                {isMuted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
              </button>
              <button onClick={toggleFullscreen} className="hover:text-[#00D4FF]">
                {isFullscreen ? <Minimize className="w-5 h-5" /> : <Maximize className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Caption Editor & Scene Strip Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Caption Editor (col-span-2) */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 p-5 flex flex-col h-48 relative shadow-md">
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-sm font-bold text-[#122131] flex items-center gap-2">
              <Subtitles className="w-4 h-4 text-[#00D4FF]" />
              Caption Editor
            </h3>
            <div className="flex items-center gap-2">
              <span className={`text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded border ${TONE_COLORS[currentScene.captions.selectedTone]}`}>
                {TONE_LABELS[currentScene.captions.selectedTone]}
              </span>
              {!isEditingCaption && (
                <button 
                  onClick={() => {
                    navigator.clipboard.writeText(editText);
                    setCopied(true);
                    setTimeout(() => setCopied(false), 2000);
                  }}
                  className="text-slate-500 hover:text-[#00D4FF] p-1 transition-colors relative"
                >
                  {copied && <span className="absolute -top-6 left-1/2 -translate-x-1/2 bg-black text-emerald-400 text-[10px] px-1.5 py-0.5 rounded">Copied!</span>}
                  <Copy className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>

          {isEditingCaption ? (
            <div className="flex flex-col h-full gap-2">
              <textarea
                value={editText}
                onChange={(e) => setEditText(e.target.value)}
                className="w-full flex-1 bg-slate-50 border border-[#00D4FF]/50 focus:border-[#00D4FF] rounded-lg p-3 text-sm text-[#122131] placeholder:text-slate-500 resize-none outline-none"
              />
              <div className="flex justify-end gap-2">
                <button onClick={() => { setIsEditingCaption(false); setEditText(currentScene.captions[currentScene.captions.selectedTone]); }} className="px-3 py-1.5 text-xs text-slate-500 hover:text-[#122131]">Cancel</button>
                <button onClick={handleSaveCaption} className="px-3 py-1.5 bg-[#00D4FF] text-[#0F172A] text-xs font-bold rounded hover:brightness-110">Save</button>
              </div>
            </div>
          ) : (
            <div 
              onClick={() => setIsEditingCaption(true)}
              className="w-full flex-1 bg-slate-50 border border-slate-200 hover:border-[#00D4FF]/50 rounded-lg p-3 text-sm text-[#122131] cursor-text group transition-colors relative"
            >
              <div className="absolute inset-0 bg-transparent" />
              {editText}
              <Edit3 className="w-4 h-4 text-slate-500 absolute bottom-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
          )}
        </div>

        {/* Scene Strip (col-span-1) */}
        <div className="lg:col-span-1 bg-white rounded-xl border border-slate-200 p-4 flex flex-col h-48 shadow-md">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-1.5">
            <Video className="w-3.5 h-3.5" /> Scenes
          </h3>
          <div className="flex-1 overflow-y-auto flex flex-col gap-2 scrollbar-thin scrollbar-thumb-slate-700 pr-1">
            {currentProject.scenes.map((scene) => (
              <div
                key={scene.id}
                draggable
                onDragStart={(e) => {
                  e.dataTransfer.setData('sceneId', scene.id);
                  e.dataTransfer.setData('projectId', currentProject.id);
                }}
                onClick={() => {
                  setVideoTime(scene.secondsStart);
                  setCurrentScene(scene);
                }}
                className={`flex gap-2 p-1.5 rounded-lg cursor-pointer border transition-all ${
                  currentScene.id === scene.id ? 'bg-slate-100 border-[#00D4FF]/50' : 'bg-slate-50 border-transparent hover:border-slate-300'
                }`}
              >
                <img src={scene.thumbnail} alt="scene" className="w-16 h-10 object-cover rounded bg-black shrink-0" />
                <div className="flex flex-col justify-center overflow-hidden">
                  <span className={`text-xs font-semibold truncate ${currentScene.id === scene.id ? 'text-[#00D4FF]' : 'text-[#122131]'}`}>{scene.title}</span>
                  <span className="text-[10px] text-slate-500 font-mono">{scene.timeStart} - {scene.timeEnd}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
