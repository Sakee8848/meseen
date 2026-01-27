import React, { useEffect, useState } from 'react';
import { CheckCircle, AlertCircle, RefreshCw, Wrench, Database, ArrowRight, Check } from 'lucide-react';
import { KnowledgeCorrectionModal } from './KnowledgeCorrectionModal';

interface LogItem {
  id: string;
  timestamp: string;
  status: "pending" | "rejected" | "imported"; 
  domain: string;
  query: string;          
  ground_truth: string;   
  ai_prediction: string;  
  confidence: number;
}

export const KnowledgeInbox: React.FC = () => {
  const [logs, setLogs] = useState<LogItem[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedTerm, setSelectedTerm] = useState("");

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/knowledge/logs");
      const data = await res.json();
      if (Array.isArray(data)) {
        setLogs(data);
      }
    } catch (err) {
      console.error("Failed to fetch logs", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  const handleCorrection = (term: string) => {
    setSelectedTerm(term);
    setIsModalOpen(true);
  };

  const handleDirectImport = async (log: LogItem) => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/taxonomy/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          category: "劳动关系与合规", 
          service: log.ai_prediction  
        })
      });

      const result = await res.json();
      if (result.status === "success" || result.status === "skipped") {
        // 1. 本地状态更新：让按钮立刻变灰
        setLogs(prevLogs => 
          prevLogs.map(item => 
            item.id === log.id ? { ...item, status: 'imported' } : item
          )
        );

        // 2. 发射信号弹：告诉星图“该刷新了！”
        window.dispatchEvent(new Event('taxonomyUpdated'));
        
        // alert(`✅ 成功入库知识节点：[${log.ai_prediction}]`);
      }
    } catch (err) {
      alert("入库失败，请检查后端连接");
    }
  };

  return (
    <>
      <div className="w-full max-w-6xl mx-auto p-6 bg-white rounded-xl shadow-sm border border-gray-100">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
            📥 ETL 数据清洗流水线 (Data Pipeline)
            <span className="text-xs font-normal text-gray-500 bg-gray-100 px-2 py-1 rounded-full border border-gray-200">
              待处理: {logs.filter(l => l.status === 'pending').length}
            </span>
          </h2>
          <button 
            onClick={fetchLogs}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            title="刷新列表"
          >
            <RefreshCw size={20} className={loading ? "animate-spin text-blue-500" : "text-gray-500"} />
          </button>
        </div>

        <div className="space-y-3">
          {logs.length === 0 ? (
            <div className="text-center py-12 bg-gray-50 rounded-lg border border-dashed border-gray-200">
              <p className="text-gray-400 text-sm">暂无待清洗数据</p>
            </div>
          ) : (
            logs.map((log) => (
              <div 
                key={log.id} 
                className={`group p-4 rounded-lg border-l-4 transition-all hover:shadow-md bg-white border border-gray-100 ${
                  log.status === 'rejected' ? 'border-l-red-500' : 
                  log.status === 'imported' ? 'border-l-gray-300 opacity-60' : // 已入库变灰
                  'border-l-emerald-500' 
                }`}
              >
                <div className="flex justify-between items-center gap-4">
                  <div className="mt-1">
                    {log.status === 'rejected' ? <AlertCircle className="text-red-500" size={20} /> : 
                     log.status === 'imported' ? <CheckCircle className="text-gray-400" size={20} /> :
                     <CheckCircle className="text-emerald-500" size={20} />}
                  </div>

                  <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">RAW QUERY (User)</span>
                      </div>
                      <p className="text-sm text-gray-800 font-medium">"{log.query}"</p>
                    </div>

                    <div className="relative pl-6 border-l border-gray-100">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[10px] font-bold text-blue-500 uppercase tracking-wider">AI PREDICTION</span>
                        <span className="text-[10px] bg-blue-50 text-blue-600 px-1.5 rounded">
                          {log.confidence}% 置信度
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-bold text-gray-900">{log.ai_prediction}</p>
                        {log.ground_truth && log.ground_truth !== "未分类" && (
                            <>
                                <ArrowRight size={14} className="text-gray-300" />
                                <span className="text-xs text-gray-400">{log.ground_truth}</span>
                            </>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-col gap-2 min-w-[100px]">
                    {log.status === 'pending' ? (
                      <button 
                        onClick={() => handleDirectImport(log)}
                        className="flex items-center justify-center gap-2 px-3 py-2 bg-emerald-600 text-white text-xs font-bold rounded hover:bg-emerald-700 transition-colors shadow-sm active:scale-95"
                      >
                        <Database size={14} />
                        确认入库
                      </button>
                    ) : log.status === 'imported' ? (
                      <button disabled className="flex items-center justify-center gap-2 px-3 py-2 bg-gray-100 text-gray-400 text-xs font-bold rounded cursor-not-allowed">
                        <Check size={14} />
                        已入库
                      </button>
                    ) : (
                      <button 
                        onClick={() => handleCorrection(log.ai_prediction)}
                        className="flex items-center justify-center gap-2 px-3 py-2 bg-white border border-gray-200 text-gray-600 text-xs font-medium rounded hover:bg-gray-50 transition-colors"
                      >
                        <Wrench size={14} />
                        人工修正
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      <KnowledgeCorrectionModal 
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        initialTerm={selectedTerm}
        onSuccess={() => {
            fetchLogs();
            window.dispatchEvent(new Event('taxonomyUpdated')); // 修正后也刷新星图
        }}
      />
    </>
  );
};