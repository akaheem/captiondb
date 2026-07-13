import React, { useState, useRef, useEffect } from 'react';
import { Plus, Film, SendHorizontal, Bot } from 'lucide-react';
import { VideoProject, Scene, Message } from '../types';

interface SidebarProps {
  projects: VideoProject[];
  setProjects: React.Dispatch<React.SetStateAction<VideoProject[]>>;
  currentProject: VideoProject;
  setCurrentProject: (proj: VideoProject) => void;
  setCurrentScene: (scene: Scene) => void;
}

export default function Sidebar({ projects, setProjects, currentProject, setCurrentProject, setCurrentScene }: SidebarProps) {
  const [chatHistory, setChatHistory] = useState<Message[]>([
    {
      id: 'chat-1',
      sender: 'ai',
      text: 'Insight Engine ready. Ask me about objects, dialogue, or events in your videos.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [selectedQAScenes, setSelectedQAScenes] = useState<string[]>([]);
  const chatBottomRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, isTyping]);

  const handleSendMessage = () => {
    if (!inputMessage.trim()) return;

    const userMsg: Message = {
      id: `chat-msg-${Date.now()}`,
      sender: 'user',
      text: inputMessage,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setChatHistory((prev) => [...prev, userMsg]);
    setInputMessage('');
    setIsTyping(true);

    setTimeout(() => {
      let aiText = `Insight Engine complete for query: "${userMsg.text}". No anomalous events detected in active projects.`;
      
      const aiMsg: Message = {
        id: `chat-msg-ai-${Date.now()}`,
        sender: 'ai',
        text: aiText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setChatHistory((prev) => [...prev, aiMsg]);
      setIsTyping(false);
    }, 1500);
  };

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const sizeMB = Math.round(file.size / (1024 * 1024));
      const sizeStr = sizeMB > 1000 ? `${(sizeMB / 1024).toFixed(1)} GB` : `${sizeMB} MB`;
      
      const newProj: VideoProject = {
        id: `proj-manual-${Date.now()}`,
        name: file.name,
        size: sizeStr,
        duration: '00:05:00',
        durationSeconds: 300,
        status: 'Completed',
        progress: 100,
        fps: '30fps',
        codec: 'H.264',
        resolution: '1080p',
        thumbnail: 'https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?auto=format&fit=crop&q=80&w=800',
        scenes: [
          {
            id: `scene-${Date.now()}`,
            timeStart: '00:00',
            timeEnd: '00:05',
            secondsStart: 0,
            secondsEnd: 5,
            title: 'Uploaded Clip',
            thumbnail: 'https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?auto=format&fit=crop&q=80&w=800',
            transcript: 'New manual upload scene.',
            tags: ['#custom'],
            status: 'Synced',
            captions: {
              formal: 'A newly added video file caption.',
              sarcastic: 'Another video file added for AI caption generation.',
              humorousTech: 'Kinetic image collection ingestion sequence completed.',
              humorousNonTech: 'Your custom video is imported.',
              audio: 'Transcribed audio text.', none: '', selectedTone: 'formal'
            }
          }
        ]
      };

      setProjects((prev) => [...prev, newProj]);
      setCurrentProject(newProj);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white border-r border-slate-200 w-80 shrink-0">
      {/* Brand Header */}
      <div className="flex items-center justify-center px-4 py-4 border-b border-slate-200 shrink-0">
        <img 
          alt="Logo" 
          className="h-[72px] w-[72px] object-contain"
          src="https://lh3.googleusercontent.com/aida-public/AB6AXuAaJrpMJT3kwG8tQXFHzmmD3B9XmFsXIf4U6gfITXo5DVT3yZeowG0LaGXDjijG3ppV4Arl4xBQtpBlYvWGnP54wvVgSVRFavUK-7rJo81D8Qnq2S5kpbxoxDjfe1F0rvvD89SXJhx-oWQovaOl_hvy9bb18YaW9UQ-QfEgZqHE8jXWrYvxWNtM9R598iU7scGLqjTriA_kpGySwgxpZSk91WwkOXbogyjTkEDhyk8dgHlElqLRxBZ__ogYMCHeMXCtsXyk4TkH71ZS"
        />
      </div>

      {/* Assets Section */}
      <div className="flex-1 flex flex-col min-h-0 border-b border-slate-200">
        <div className="p-4 flex justify-between items-center shrink-0">
          <h2 className="text-sm font-bold uppercase tracking-wider text-[#122131]">Assets</h2>
          <button 
            onClick={() => fileInputRef.current?.click()}
            className="text-[#00D4FF] bg-[#00D4FF]/10 hover:bg-[#00D4FF]/20 p-1.5 rounded transition-colors"
            title="Upload Video"
          >
            <Plus className="w-4 h-4" />
          </button>
          <input 
            type="file" 
            ref={fileInputRef} 
            className="hidden" 
            accept="video/*" 
            onChange={handleUpload} 
          />
        </div>
        
        <div className="flex-1 overflow-y-auto px-2 pb-2 scrollbar-thin scrollbar-thumb-slate-200">
          {projects.map(proj => (
            <div 
              key={proj.id}
              onClick={() => setCurrentProject(proj)}
              className={`flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-colors mb-1 ${
                currentProject.id === proj.id ? 'bg-slate-100 border border-[#00D4FF]/30' : 'hover:bg-slate-50 border border-transparent'
              }`}
            >
              <div className="w-12 h-10 bg-black rounded overflow-hidden shrink-0 relative">
                <img src={proj.thumbnail} alt={proj.name} className="w-full h-full object-cover opacity-80" />
                <Film className="w-3 h-3 text-white absolute bottom-1 right-1 opacity-70" />
              </div>
              <div className="flex flex-col overflow-hidden">
                <span className={`text-sm font-semibold truncate ${currentProject.id === proj.id ? 'text-[#00D4FF]' : 'text-[#122131] hover:text-[#00D4FF]'}`}>
                  {proj.name}
                </span>
                <span className="text-[10px] text-slate-500">{proj.duration} • {proj.size}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Q&A Section */}
      <div className="h-1/2 flex flex-col shrink-0 bg-white border-t border-slate-200">
        <div className="p-3 border-b border-slate-200 bg-white flex items-center gap-2 shrink-0">
          <Bot className="w-4 h-4 text-[#00D4FF]" />
          <h2 className="text-xs font-bold text-[#122131]">Q&A Insight Engine</h2>
        </div>
        
        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-3 scrollbar-thin scrollbar-thumb-slate-200">
          {chatHistory.map((msg) => {
            const isUser = msg.sender === 'user';
            return (
              <div key={msg.id} className={`flex flex-col gap-1 ${isUser ? 'items-end' : 'items-start'}`}>
                <div className={`p-2.5 rounded-lg text-xs leading-relaxed max-w-[90%] shadow-sm border ${
                  isUser ? 'bg-[#122131] text-white border-transparent rounded-tr-sm' : 'bg-white text-[#122131] border-slate-200 rounded-tl-sm'
                }`}>
                  {msg.text}
                </div>
              </div>
            );
          })}
          {isTyping && (
            <div className="flex items-center gap-1 bg-white p-2.5 rounded-lg rounded-tl-sm w-fit border border-slate-200 shadow-sm">
              <span className="w-1.5 h-1.5 rounded-full bg-[#00D4FF]/60 animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-1.5 h-1.5 rounded-full bg-[#00D4FF]/60 animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-1.5 h-1.5 rounded-full bg-[#00D4FF]/60 animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          )}
          <div ref={chatBottomRef} />
        </div>

        {/* Chat Input */}
        <div className="p-3 bg-white border-t border-slate-200 shrink-0">
          {/* Selector for Q&A */}
          <div 
            className="mb-2 flex flex-col gap-1.5 p-1 rounded transition-colors"
            onDragOver={(e) => {
              e.preventDefault();
              e.currentTarget.classList.add('bg-slate-100', 'border', 'border-dashed', 'border-[#00D4FF]');
            }}
            onDragLeave={(e) => {
              e.currentTarget.classList.remove('bg-slate-100', 'border', 'border-dashed', 'border-[#00D4FF]');
            }}
            onDrop={(e) => {
              e.preventDefault();
              e.currentTarget.classList.remove('bg-slate-100', 'border', 'border-dashed', 'border-[#00D4FF]');
              const sceneId = e.dataTransfer.getData('sceneId');
              if (sceneId) {
                setSelectedQAScenes(prev => 
                  prev.includes(sceneId) ? prev : [...prev, sceneId]
                );
              }
            }}
          >
            <span className="text-[10px] text-slate-500 font-medium">Ask about (Drop a scene here):</span>
            <div className="flex items-center gap-2 overflow-x-auto scrollbar-none pb-1">
              <button 
                className={`text-[10px] px-2 py-0.5 rounded-full border transition-colors whitespace-nowrap ${!selectedQAScenes.length ? 'bg-[#00D4FF]/10 text-[#00D4FF] border-[#00D4FF]/30' : 'bg-slate-50 text-slate-600 border-slate-200 hover:border-slate-300'}`}
                onClick={() => setSelectedQAScenes([])}
              >
                All Projects
              </button>
              {projects.map(proj => (
                <button
                  key={proj.id}
                  onClick={() => {
                    setSelectedQAScenes(prev => 
                      prev.includes(proj.id) ? prev.filter(id => id !== proj.id) : [...prev, proj.id]
                    )
                  }}
                  className={`text-[10px] px-2 py-0.5 rounded-full border transition-colors whitespace-nowrap ${selectedQAScenes.includes(proj.id) ? 'bg-[#00D4FF]/10 text-[#00D4FF] border-[#00D4FF]/30' : 'bg-slate-50 text-slate-600 border-slate-200 hover:border-slate-300'}`}
                >
                  {proj.name}
                </button>
              ))}
              {currentProject.scenes.map(scene => (
                <button
                  key={scene.id}
                  onClick={() => {
                    setSelectedQAScenes(prev => 
                      prev.includes(scene.id) ? prev.filter(id => id !== scene.id) : [...prev, scene.id]
                    )
                  }}
                  className={`text-[10px] px-2 py-0.5 rounded-full border transition-colors whitespace-nowrap ${selectedQAScenes.includes(scene.id) ? 'bg-[#00D4FF]/10 text-[#00D4FF] border-[#00D4FF]/30' : 'bg-slate-50 text-slate-600 border-slate-200 hover:border-slate-300'}`}
                >
                  {scene.title}
                </button>
              ))}
            </div>
          </div>
          <div className="relative flex items-center">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
              placeholder="Ask about this video..."
              className="w-full bg-white border border-slate-200 rounded-lg py-2 pl-3 pr-10 text-[#122131] placeholder:text-slate-400 text-xs focus:outline-none focus:border-[#00D4FF] focus:bg-white transition-colors"
            />
            <button
              onClick={handleSendMessage}
              disabled={!inputMessage.trim()}
              className="absolute right-1 w-7 h-7 flex items-center justify-center text-[#00D4FF] hover:bg-[#00D4FF]/10 rounded-md disabled:opacity-30 transition-colors"
            >
              <SendHorizontal className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
