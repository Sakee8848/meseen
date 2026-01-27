import React, { useState, useRef, useEffect } from 'react';
import { Play, SkipForward, AlertCircle, Terminal, RefreshCw, CheckCircle } from 'lucide-react';

interface Mission {
  novice_intent: string;
  display_intent?: string; 
  expert_term: string;
  category: string;
}

interface LogEntry {
  step: number;
  role: string;
  content: string;
  raw_state?: boolean; // 👈 更新类型定义：后端V4.4返回的是 boolean
}

const SimulationMonitor = () => {
  // 核心状态
  const [isSimulating, setIsSimulating] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false); // 👈 新增：标记流程是否彻底结束
  const [mission, setMission] = useState<Mission | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  
  const sessionIdRef = useRef<string>(""); 
  const logEndRef = useRef<HTMLDivElement>(null);

  // 自动滚动
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  // 1. 点击“开始/重置”
  const handleStart = async () => {
    const newSessionId = Date.now().toString();
    sessionIdRef.current = newSessionId;

    setLoading(true);
    setLogs([]); 
    setMission(null);
    setIsSimulating(false);
    setIsCompleted(false); // 👈 重置完成状态

    try {
      const res = await fetch("http://127.0.0.1:8000/api/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ domain: "hr" })
      });
      
      const data = await res.json();
      
      if (sessionIdRef.current === newSessionId) {
        if (data.status === "started") {
          setIsSimulating(true);
          setMission(data.mission);
          console.log("仿真已启动 (Session):", newSessionId);
        } else {
          alert("启动失败: " + JSON.stringify(data));
        }
      }
    } catch (err) {
      console.error(err);
      alert("无法连接后端");
    } finally {
      if (sessionIdRef.current === newSessionId) {
        setLoading(false);
      }
    }
  };

  // 2. 点击“下一步”
  const handleNext = async () => {
    if (!isSimulating || isCompleted) return; // 如果已完成，禁止点击
    const currentSessionId = sessionIdRef.current; 

    setLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/next", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      
      const data = await res.json();
      
      if (sessionIdRef.current === currentSessionId) {
        // 渲染日志
        setLogs(prev => [...prev, data]);

        // 🚦 核心修复：检测布尔值信号
        // 后端 V4.4 确保返回的是 boolean 类型的 true
        if (data.raw_state === true) {
          setIsCompleted(true); // 👈 锁定状态，变绿灯
          setIsSimulating(false); // 停止仿真逻辑
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      if (sessionIdRef.current === currentSessionId) {
        setLoading(false);
      }
    }
  };

  return (
    <div className="flex flex-col h-full bg-white relative">
      {/* 顶部控制栏 */}
      <div className="p-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
        <div>
          <h2 className="font-bold text-gray-800 flex items-center gap-2">
            密心 (Mixin) 专家逆向工程台
          </h2>
          <p className="text-xs text-gray-500">盲测模式: Human Resources</p>
        </div>
        
        <div className="flex gap-2">
          {/* 开始按钮 */}
          <button
            onClick={handleStart}
            disabled={loading}
            className="flex flex-col items-center justify-center w-16 h-16 bg-black text-white rounded-lg hover:bg-gray-800 transition-all active:scale-95 disabled:opacity-50"
          >
            {loading && !isSimulating ? <RefreshCw size={20} className="animate-spin" /> : <Play size={20} />}
            <span className="text-[10px] mt-1 font-medium">重置/开始</span>
          </button>

          {/* 下一步按钮 (变色龙版) */}
          <button
            onClick={handleNext}
            disabled={(!isSimulating && !isCompleted) || loading || isCompleted} 
            className={`flex flex-col items-center justify-center w-16 h-16 rounded-lg transition-all active:scale-95 disabled:opacity-80 ${
              isCompleted
                ? "bg-green-600 text-white shadow-lg shadow-green-200 cursor-default" // ✅ 完成状态：绿色
                : isSimulating
                  ? "bg-blue-600 text-white hover:bg-blue-700 shadow-lg shadow-blue-200" // ▶️ 进行中：蓝色
                  : "bg-gray-100 text-gray-400 cursor-not-allowed" // ⏹️ 未开始：灰色
            }`}
          >
            {/* 图标切换逻辑 */}
            {isCompleted ? <CheckCircle size={20} /> : <SkipForward size={20} />}
            
            <span className="text-[10px] mt-1 font-medium">
              {isCompleted ? "已完成" : "下一步"}
            </span>
          </button>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* 左侧：绝密任务卡 */}
        <div className="w-1/3 bg-[#FFFBEB] p-4 border-r border-yellow-100 overflow-y-auto">
          <h3 className="text-[#92400E] font-bold text-xs tracking-widest mb-4 flex items-center gap-1">
             TOP SECRET MISSION
          </h3>
          
          {mission ? (
            <div className="space-y-4 animate-in slide-in-from-left duration-500">
              <div>
                <div className="text-[10px] text-yellow-600 uppercase mb-1">小白用户意图 (User Intent)</div>
                <div className="font-serif text-lg text-gray-900 leading-snug">
                  "{mission.display_intent || mission.novice_intent}"
                </div>
              </div>
              
              <div className="p-3 bg-white/50 rounded border border-yellow-200/50">
                <div className="text-[10px] text-gray-400 uppercase mb-1">标准答案 (Target Term)</div>
                <div className="font-mono text-sm font-bold text-gray-700">{mission.expert_term}</div>
              </div>
            </div>
          ) : (
            <div className="text-yellow-700/30 text-sm italic mt-10">等待任务分配...</div>
          )}
        </div>

        {/* 右侧：思考日志流 */}
        <div className="w-2/3 bg-white p-4 overflow-y-auto font-mono text-sm relative">
          
          {!mission && !loading && (
            <div className="absolute inset-0 bg-white/90 z-10 flex flex-col items-center justify-center text-gray-400">
              <AlertCircle size={48} className="mb-2 opacity-20" />
              <p>请点击左上角的“开始”按钮</p>
            </div>
          )}

          <div className="space-y-6 pb-10">
            {logs.map((log, index) => (
              <div key={index} className="animate-in fade-in slide-in-from-bottom-2 duration-300">
                <div className="flex items-center gap-2 mb-1 text-xs text-gray-400">
                  <Terminal size={12} />
                  <span>STEP {log.step === -1 ? "END" : log.step}</span>
                  <span className={`uppercase px-1 rounded text-[10px] ${
                    log.role === 'human' ? 'bg-yellow-100 text-yellow-800' : 'bg-gray-100'
                  }`}>{log.role}</span>
                </div>
                <div className={`p-3 rounded-lg border leading-relaxed whitespace-pre-wrap ${
                  log.role === 'ai' ? 'bg-blue-50 border-blue-100 text-blue-900' : 
                  log.role === 'tool' ? 'bg-gray-50 border-gray-200 text-gray-600' :
                  log.role === 'human' ? 'bg-yellow-50 border-yellow-100 text-gray-800' :
                  log.role === 'system' ? 'bg-green-50 border-green-200 text-green-800 font-bold' : // 系统结束语高亮
                  'bg-white border-gray-100 text-gray-800'
                }`}>
                  {log.content}
                </div>
              </div>
            ))}
            <div ref={logEndRef} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default SimulationMonitor;