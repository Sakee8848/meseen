"use client";
import { useState } from 'react';
import SimulationMonitor from '@/components/SimulationMonitor';
import KnowledgeGalaxy from '@/components/KnowledgeGalaxy';
import { Activity, Map as MapIcon } from 'lucide-react';

export default function Home() {
  const [view, setView] = useState<'monitor' | 'galaxy'>('monitor');

  return (
    <main className="h-screen w-full flex flex-col bg-gray-50 overflow-hidden">
      {/* 顶部导航 */}
      <nav className="bg-black text-white px-6 py-3 flex justify-between items-center shadow-md z-10">
        <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center font-bold text-xl">M</div>
            <h1 className="font-bold text-lg tracking-wide">Meseeing <span className="text-gray-400 font-normal text-sm">| 觅心智能</span></h1>
        </div>
        
        <div className="flex bg-gray-800 rounded-lg p-1 gap-1">
            <button 
                onClick={() => setView('monitor')}
                className={`flex items-center gap-2 px-4 py-1.5 rounded-md text-sm transition ${view === 'monitor' ? 'bg-gray-600 text-white shadow' : 'text-gray-400 hover:text-white'}`}
            >
                <Activity size={14} /> 实时仿真台
            </button>
            <button 
                onClick={() => setView('galaxy')}
                className={`flex items-center gap-2 px-4 py-1.5 rounded-md text-sm transition ${view === 'galaxy' ? 'bg-blue-600 text-white shadow' : 'text-gray-400 hover:text-white'}`}
            >
                <MapIcon size={14} /> 知识星图
            </button>
        </div>
      </nav>

      {/* 内容区域 */}
      <div className="flex-1 overflow-hidden relative">
          {view === 'monitor' ? <SimulationMonitor /> : <KnowledgeGalaxy />}
      </div>
    </main>
  );
}