import { useState, useEffect } from 'react';
import { Cpu } from 'lucide-react';
import { VideoProject, Scene } from './types';
import { SAMPLE_PROJECTS } from './data';

import Sidebar from './components/Sidebar';
import MainWorkspace from './components/MainWorkspace';
import ExportPopover from './components/ExportPopover';

export default function App() {
  const [gpuOnline, setGpuOnline] = useState(true);
  const [projects, setProjects] = useState<VideoProject[]>(SAMPLE_PROJECTS);
  
  const [currentProject, setCurrentProject] = useState<VideoProject>(SAMPLE_PROJECTS[0]);
  const [currentScene, setCurrentScene] = useState<Scene>(SAMPLE_PROJECTS[0].scenes[1]);

  useEffect(() => {
    if (currentProject.scenes.length > 0) {
      setCurrentScene(currentProject.scenes[0]);
    }
  }, [currentProject]);

  return (
    <div className="bg-white text-[#122131] h-screen w-full flex overflow-hidden font-sans antialiased selection:bg-[#00D4FF]/20 selection:text-[#122131]">
      <Sidebar 
        projects={projects}
        setProjects={setProjects}
        currentProject={currentProject}
        setCurrentProject={setCurrentProject}
        setCurrentScene={setCurrentScene}
      />

      <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
        {/* Header */}
        <header className="bg-white border-b border-slate-200 shrink-0 h-16 z-30 px-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
             <span className="font-semibold text-[#122131]">{currentProject.name}</span>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-[#1E293B] border border-slate-700/85 rounded-full select-none">
              <span className={`w-2 h-2 rounded-full ${gpuOnline ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`} />
              <span className={`text-[10px] font-bold uppercase tracking-wider ${gpuOnline ? 'text-emerald-400' : 'text-amber-400'}`}>
                GPU {gpuOnline ? 'Online' : 'Offline'}
              </span>
            </div>

            <button
              onClick={() => setGpuOnline(!gpuOnline)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 select-none ${
                gpuOnline 
                  ? 'border border-amber-500/50 text-amber-500 hover:bg-amber-500/10' 
                  : 'bg-[#00D4FF] text-[#0A192F] hover:brightness-110 shadow-[0_0_8px_rgba(0,212,255,0.2)]'
              }`}
            >
              <Cpu className="w-3.5 h-3.5" />
              {gpuOnline ? 'Destroy Instance' : 'Start GPU'}
            </button>

            <ExportPopover currentProject={currentProject} />
          </div>
        </header>

        {/* Main Content Area */}
        <div className="flex-1 overflow-y-auto bg-slate-50">
          <MainWorkspace
            currentProject={currentProject}
            setCurrentProject={setCurrentProject}
            currentScene={currentScene}
            setCurrentScene={setCurrentScene}
            projects={projects}
            setProjects={setProjects}
          />
        </div>
      </div>
    </div>
  );
}

