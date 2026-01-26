import React, { useEffect, useState } from 'react';
import { CheckCircle, AlertCircle, RefreshCw, Wrench } from 'lucide-react';
// 👇 引入手术台组件
import { KnowledgeCorrectionModal } from './KnowledgeCorrectionModal';

interface LogItem {
  id: string;
  timestamp: string;
  novice_intent: string;
  ground_truth_term: string;
  current_ai_response: string;
  status: "PASS" | "REJECT";
  action_required: boolean;
}

export const KnowledgeInbox: React.FC = () => {
  const [logs, setLogs] = useState<LogItem[]>([]);
  const [loading, setLoading] = useState(true);
  
  // 👇 Modal 相关的状态
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

  // 👇 点击“修正入库”时触发
  const handleCorrection = (term: string) => {
    setSelectedTerm(term); // 记住要修哪个词
    setIsModalOpen(true);  // 打开窗口
  };

  return (
    <>
      <div className="w-full max-w-4xl mx-auto p-6 bg-white rounded-xl shadow-sm border border-gray-100">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
            📥 知识收件箱 (Knowledge Inbox)
            <span className="text-sm font-normal text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
              {logs.length} 条记录
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

        <div className="space-y-4">
          {logs.length === 0 ? (
            <div className="text-center py-10 text-gray-400">
              暂无数据，请先运行 ETL 脚本生成报告
            </div>
          ) : (
            logs.map((log) => (
              <div 
                key={log.id} 
                className={`p-4 rounded-lg border-l-4 transition-all hover:shadow-md ${
                  log.status === 'REJECT' 
                    ? 'border-red-500 bg-red-50' 
                    : 'border-green-500 bg-green-50'
                }`}
              >
                <div className="flex justify-between items-start">
                  <div className="mt-1 mr-4">
                    {log.status === 'REJECT' ? (
                      <AlertCircle className="text-red-500" size={24} />
                    ) : (
                      <CheckCircle className="text-green-500" size={24} />
                    )}
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-xs font-bold px-2 py-0.5 rounded text-white ${
                        log.status === 'REJECT' ? 'bg-red-500' : 'bg-green-500'
                      }`}>
                        {log.status}
                      </span>
                      <span className="text-xs text-gray-400">{log.timestamp}</span>
                    </div>
                    
                    <h3 className="font-semibold text-gray-800 mb-2">
                      用户问: "{log.novice_intent}"
                    </h3>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      <div className="bg-white/60 p-2 rounded">
                        <p className="text-xs text-gray-500 mb-1">🎯 标准答案 (Ground Truth)</p>
                        <p className="font-medium text-gray-900">{log.ground_truth_term}</p>
                      </div>
                      <div className="bg-white/60 p-2 rounded">
                        <p className="text-xs text-gray-500 mb-1">🤖 当前 AI 回答</p>
                        <p className="text-gray-700 line-clamp-2" title={log.current_ai_response}>
                          {log.current_ai_response}
                        </p>
                      </div>
                    </div>
                  </div>

                  {log.status === 'REJECT' && (
                    <div className="ml-4 flex flex-col gap-2">
                      <button 
                        // 👇 绑定点击事件
                        onClick={() => handleCorrection(log.ground_truth_term)}
                        className="px-3 py-1.5 bg-blue-600 text-white text-xs font-medium rounded hover:bg-blue-700 transition-colors shadow-sm whitespace-nowrap flex items-center gap-1"
                      >
                        <Wrench size={12} />
                        修正入库
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* 👇 渲染弹窗组件 */}
      <KnowledgeCorrectionModal 
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        initialTerm={selectedTerm}
        onSuccess={() => {
            // 入库成功后，可以在这里做一些刷新操作，比如刷新星图
            console.log("Knowledge Injected!");
        }}
      />
    </>
  );
};