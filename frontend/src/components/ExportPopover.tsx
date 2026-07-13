import React, { useState } from 'react';
import { Download, CheckCircle2, RefreshCw, Video } from 'lucide-react';
import { VideoProject } from '../types';

export default function ExportPopover({ currentProject }: { currentProject: VideoProject }) {
  const [isOpen, setIsOpen] = useState(false);
  const [formats, setFormats] = useState<string[]>(['SRT']);
  const [videoStyle, setVideoStyle] = useState<string | null>(null);
  const [isExporting, setIsExporting] = useState(false);

  const toggleFormat = (fmt: string) => {
    setFormats(prev => prev.includes(fmt) ? prev.filter(f => f !== fmt) : [...prev, fmt]);
  };

  const handleExport = () => {
    setIsExporting(true);
    setTimeout(() => {
      setIsExporting(false);
      setIsOpen(false);
      const parts = [];
      if (formats.length) parts.push(`Text formats: ${formats.join(', ')}`);
      if (videoStyle) parts.push(`Captioned Video (${videoStyle})`);
      alert(`Exported ${currentProject.name}\n${parts.join('\n')}`);
    }, 1500);
  };

  const TONE_LABELS = [
    { id: 'none', label: 'None', color: 'text-slate-500', activeBg: 'bg-slate-50 border-slate-500 text-slate-500' },
    { id: 'formal', label: 'Formal', color: 'text-blue-500', activeBg: 'bg-blue-50 border-blue-500 text-blue-500' },
    { id: 'sarcastic', label: 'Sarcastic', color: 'text-purple-500', activeBg: 'bg-purple-50 border-purple-500 text-purple-500' },
    { id: 'humorousTech', label: 'Humorous (Tech)', color: 'text-orange-500', activeBg: 'bg-orange-50 border-orange-500 text-orange-500' },
    { id: 'humorousNonTech', label: 'Humorous (Non-Tech)', color: 'text-pink-500', activeBg: 'bg-pink-50 border-pink-500 text-pink-500' },
    { id: 'audio', label: 'Audio Transcript', color: 'text-emerald-500', activeBg: 'bg-emerald-50 border-emerald-500 text-emerald-500' }
  ];

  return (
    <div className="relative">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="bg-[#00D4FF] hover:brightness-110 text-[#0A192F] px-4 py-1.5 rounded-lg font-bold text-sm flex items-center gap-2 shadow-[0_0_8px_rgba(0,212,255,0.2)] transition-all"
      >
        <Download className="w-4 h-4" />
        Export
      </button>

      {isOpen && (
        <div className="absolute right-0 top-full mt-2 w-80 bg-white border border-slate-200 rounded-xl shadow-2xl p-4 z-50">
          <h3 className="text-sm font-bold text-[#122131] mb-3">Export Options</h3>
          
          <div className="flex flex-col gap-2 mb-4">
            <span className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Text Formats</span>
            <div className="grid grid-cols-2 gap-2">
              {['SRT', 'VTT', 'JSON', 'TXT'].map(fmt => {
                const active = formats.includes(fmt);
                return (
                  <button
                    key={fmt}
                    onClick={() => toggleFormat(fmt)}
                    className={`flex items-center gap-2 p-2 rounded border text-xs font-bold transition-all ${
                      active ? 'bg-slate-100 border-[#00D4FF] text-[#00D4FF]' : 'bg-slate-50 border-slate-200 text-slate-500 hover:border-slate-500'
                    }`}
                  >
                    {active ? <CheckCircle2 className="w-3.5 h-3.5" /> : <div className="w-3.5 h-3.5 rounded-full border border-slate-300" />}
                    {fmt}
                  </button>
                )
              })}
            </div>
          </div>

          <div className="flex flex-col gap-2 mb-4">
            <span className="text-xs text-slate-500 font-semibold uppercase tracking-wider flex items-center gap-1.5">
              <Video className="w-3.5 h-3.5" /> Captioned Video
            </span>
            <div className="grid grid-cols-2 gap-2">
              {TONE_LABELS.map(style => {
                const active = videoStyle === style.id;
                return (
                  <button
                    key={style.id}
                    onClick={() => setVideoStyle(active ? null : style.id)}
                    className={`flex items-center gap-2 p-2 rounded border text-[10px] font-bold transition-all text-left leading-tight ${
                      active ? style.activeBg : `bg-slate-50 border-slate-200 hover:border-slate-300 ${style.color}`
                    }`}
                  >
                    {active ? <CheckCircle2 className="w-3.5 h-3.5 shrink-0" /> : <div className="w-3.5 h-3.5 rounded-full border border-slate-300 shrink-0" />}
                    {style.label}
                  </button>
                )
              })}
            </div>
          </div>

          <button
            onClick={handleExport}
            disabled={isExporting || (formats.length === 0 && !videoStyle)}
            className="w-full bg-[#00D4FF] text-[#0A192F] font-bold py-2 rounded-lg flex items-center justify-center gap-2 hover:brightness-110 disabled:opacity-50 transition-all text-sm"
          >
            {isExporting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
            {isExporting ? 'Generating...' : 'Download Files'}
          </button>
        </div>
      )}
    </div>
  );
}
