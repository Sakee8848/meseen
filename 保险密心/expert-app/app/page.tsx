"use client";

// 👇 1. 旧组件（通常是 export default），请去掉花括号 {}
import SimulationMonitor from "../components/SimulationMonitor";
import KnowledgeGalaxy from "../components/KnowledgeGalaxy";

// 👇 2. 新组件（我们写的是 export const），必须保留花括号 {}
import { KnowledgeInbox } from "../components/KnowledgeInbox";
import { BatchControlPanel } from "../components/BatchControlPanel";

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50 p-8 flex flex-col gap-8">
      <div className="max-w-6xl mx-auto w-full space-y-8">

        {/* 顶部标题 */}
        <header className="flex justify-between items-end border-b pb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Meseeing 密心</h1>
            <p className="text-gray-500">Expert Knowledge Injection System V1.1</p>
          </div>
        </header>

        {/* ETL数据归类 */}
        <section>
          <KnowledgeInbox />
        </section>

        {/* 聊天和星图区域 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[600px]">
          <div className="lg:col-span-1 h-full bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <SimulationMonitor />
          </div>
          <div className="lg:col-span-2 h-full bg-black rounded-xl shadow-sm border border-gray-800 overflow-hidden relative">
            <div className="absolute top-4 left-4 z-10 bg-black/50 text-white text-xs px-2 py-1 rounded backdrop-blur-sm border border-white/20">
              知识星图 (Knowledge Graph)
            </div>
            <KnowledgeGalaxy />
          </div>
        </div>

        {/* 批量 AI 互博引擎 */}
        <section>
          <BatchControlPanel />
        </section>

      </div>
    </main>
  );
}