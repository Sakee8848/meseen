import React, { useEffect, useState } from 'react';
import { CheckCircle, AlertCircle, RefreshCw, Database, Clock, Filter, X, User, Bot, MessageSquare, ChevronDown, ChevronUp } from 'lucide-react';

interface DialogueStep {
  step: number;
  role: string;
  content: string;
}

interface LogItem {
  id: string;
  timestamp: string;
  status: "pending" | "rejected" | "imported";
  domain: string;
  query: string;
  ground_truth?: string;
  ai_prediction: string;
  confidence: number;
  category?: string;
  persona?: string;
  tone?: string;
  // 🆕 V6.0 新增
  dialogue_path?: DialogueStep[];
  total_turns?: number;
  diagnosis_correct?: boolean;
  key_questions?: string[];
}

// --- 对话详情弹窗组件 ---
const DialogueModal = ({ log, onClose }: { log: LogItem; onClose: () => void }) => {
  if (!log) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full mx-4 max-h-[80vh] flex flex-col overflow-hidden">
        {/* 头部 */}
        <div className="flex justify-between items-center px-5 py-4 border-b border-gray-100 bg-gradient-to-r from-blue-50 to-purple-50">
          <div>
            <h3 className="font-bold text-gray-800 flex items-center gap-2">
              <MessageSquare size={18} className="text-blue-500" />
              AI 互博对话详情
            </h3>
            <p className="text-xs text-gray-500 mt-1">
              {log.total_turns ? `共 ${log.total_turns} 轮对话` : '对话记录'}
              {log.diagnosis_correct !== undefined && (
                <span className={`ml-2 px-1.5 py-0.5 rounded text-[10px] ${log.diagnosis_correct ? 'bg-green-100 text-green-600' : 'bg-orange-100 text-orange-600'}`}>
                  {log.diagnosis_correct ? '✓ 诊断正确' : '⚠ 需人工审核'}
                </span>
              )}
            </p>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-full transition-colors">
            <X size={18} className="text-gray-500" />
          </button>
        </div>

        {/* 对话内容区域 */}
        <div className="flex-1 overflow-y-auto p-5 space-y-3 bg-gray-50">
          {log.dialogue_path && log.dialogue_path.length > 0 ? (
            log.dialogue_path.map((step, idx) => (
              <div
                key={idx}
                className={`flex gap-3 ${step.role === 'ai' ? '' : 'flex-row-reverse'}`}
              >
                {/* 头像 */}
                <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${step.role === 'ai' ? 'bg-blue-100 text-blue-600' : 'bg-purple-100 text-purple-600'
                  }`}>
                  {step.role === 'ai' ? <Bot size={16} /> : <User size={16} />}
                </div>

                {/* 消息气泡 */}
                <div className={`flex-1 max-w-[80%] ${step.role === 'ai' ? '' : 'text-right'}`}>
                  <div className="text-[10px] text-gray-400 mb-1">
                    {step.role === 'ai' ? '🤖 AI 专家' : '👤 小白客户'} · Step {step.step}
                  </div>
                  <div className={`inline-block px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${step.role === 'ai'
                    ? 'bg-white text-gray-700 border border-gray-200 rounded-tl-md'
                    : 'bg-blue-500 text-white rounded-tr-md'
                    }`}>
                    {step.content}
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-10 text-gray-400">
              <MessageSquare size={40} className="mx-auto mb-3 opacity-30" />
              <p className="text-sm">此记录暂无对话详情</p>
              <p className="text-xs mt-1">运行批量挖矿后将生成完整对话路径</p>
            </div>
          )}
        </div>

        {/* 底部信息 */}
        <div className="px-5 py-3 border-t border-gray-100 bg-white">
          <div className="flex flex-wrap gap-2 text-xs text-gray-500">
            <span className="bg-gray-100 px-2 py-1 rounded">
              🎯 诊断结果: <strong className="text-blue-600">{log.ai_prediction}</strong>
            </span>
            {log.ground_truth && log.ground_truth !== log.ai_prediction && (
              <span className="bg-orange-50 px-2 py-1 rounded text-orange-600">
                📋 真实答案: {log.ground_truth}
              </span>
            )}
            {log.persona && (
              <span className="bg-purple-50 px-2 py-1 rounded">
                👤 角色: {log.persona}
              </span>
            )}
            {log.key_questions && log.key_questions.length > 0 && (
              <span className="bg-green-50 px-2 py-1 rounded text-green-600">
                🔑 关键追问: {log.key_questions.length} 个
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export const KnowledgeInbox: React.FC = () => {
  const [logs, setLogs] = useState<LogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAll, setShowAll] = useState(false);
  const [selectedLog, setSelectedLog] = useState<LogItem | null>(null);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/etl/inbox`);
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
    const interval = setInterval(fetchLogs, 5000);
    return () => clearInterval(interval);
  }, []);

  const pendingCount = logs.filter(l => l.status === 'pending').length;
  const importedCount = logs.filter(l => l.status === 'imported').length;
  const displayLogs = showAll ? logs : logs.slice(0, 10);

  const formatTime = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return timestamp;
    }
  };

  // 判断是否有对话详情
  const hasDialogue = (log: LogItem) => log.dialogue_path && log.dialogue_path.length > 0;

  return (
    <div className="w-full max-w-6xl mx-auto p-4 bg-white rounded-xl shadow-sm border border-gray-100">
      {/* 头部 */}
      <div className="flex justify-between items-center mb-3">
        <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
          📥 ETL 数据清洗流水线 (Data Pipeline)
          <span className="text-xs font-normal text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full border border-gray-200">
            待处理: {pendingCount}
          </span>
          {importedCount > 0 && (
            <span className="text-xs font-normal text-green-600 bg-green-50 px-2 py-0.5 rounded-full border border-green-200">
              已入库: {importedCount}
            </span>
          )}
        </h2>
        <div className="flex gap-2 items-center">
          <span className="text-xs text-gray-400">
            自动入库模式
          </span>
          <button
            onClick={fetchLogs}
            className="p-1.5 hover:bg-gray-100 rounded-full transition-colors"
            title="刷新列表"
          >
            <RefreshCw size={16} className={loading ? "animate-spin text-blue-500" : "text-gray-500"} />
          </button>
        </div>
      </div>

      {/* 说明文字 */}
      <div className="text-xs text-gray-500 mb-3 flex items-center gap-2">
        <Database size={12} />
        <span>批量挖矿的知识点已<strong className="text-green-600">自动入库</strong>至知识星图。<strong className="text-blue-500">点击条目</strong>可查看完整对话路径</span>
      </div>

      {/* 列表区域 */}
      <div className="max-h-[320px] overflow-y-auto custom-scrollbar border border-gray-100 rounded-lg">
        {logs.length === 0 ? (
          <div className="text-center py-8 bg-gray-50">
            <p className="text-gray-400 text-sm">暂无数据记录</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-50">
            {displayLogs.map((log) => (
              <div
                key={log.id}
                onClick={() => setSelectedLog(log)}
                className={`flex items-center gap-3 px-3 py-2.5 hover:bg-blue-50 transition-colors cursor-pointer ${log.status === 'imported' ? 'opacity-60' : ''
                  }`}
              >
                {/* 状态图标 */}
                <div className="flex-shrink-0">
                  {log.status === 'rejected' ? (
                    <AlertCircle className="text-red-500" size={16} />
                  ) : log.status === 'imported' ? (
                    <CheckCircle className="text-gray-400" size={16} />
                  ) : (
                    <CheckCircle className="text-emerald-500" size={16} />
                  )}
                </div>

                {/* 用户查询 */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-700 truncate" title={log.query}>
                    "{log.query}"
                  </p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-[10px] text-gray-400 flex items-center gap-1">
                      <Clock size={10} />
                      {formatTime(log.timestamp)}
                    </span>
                    {log.persona && (
                      <span className="text-[10px] text-purple-500 bg-purple-50 px-1 rounded">
                        {log.persona}
                      </span>
                    )}
                    {/* 🆕 显示对话轮次 */}
                    {log.total_turns && (
                      <span className="text-[10px] text-blue-500 bg-blue-50 px-1 rounded flex items-center gap-0.5">
                        <MessageSquare size={8} />
                        {log.total_turns}轮
                      </span>
                    )}
                  </div>
                </div>

                {/* AI 预测 */}
                <div className="flex-shrink-0 text-right">
                  <span className="text-xs font-medium text-blue-600 bg-blue-50 px-2 py-1 rounded">
                    {log.ai_prediction}
                  </span>
                  {log.diagnosis_correct !== undefined && (
                    <div className={`text-[10px] mt-0.5 ${log.diagnosis_correct ? 'text-green-500' : 'text-orange-500'}`}>
                      {log.diagnosis_correct ? '✓ 诊断正确' : '⚠ 待审核'}
                    </div>
                  )}
                </div>

                {/* 对话指示器 */}
                <div className="flex-shrink-0 w-6">
                  {hasDialogue(log) && (
                    <ChevronDown size={14} className="text-gray-400" />
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 底部：显示更多 */}
      {logs.length > 10 && (
        <div className="mt-2 text-center">
          <button
            onClick={() => setShowAll(!showAll)}
            className="text-xs text-blue-500 hover:text-blue-700 transition-colors"
          >
            {showAll ? `收起列表` : `显示全部 ${logs.length} 条记录`}
          </button>
        </div>
      )}

      {/* 数据质量说明 */}
      <div className="mt-3 p-2 bg-gray-50 rounded-lg text-[10px] text-gray-500">
        <div className="flex items-center gap-1 font-medium text-gray-600 mb-1">
          <Filter size={10} />
          数据入库质量保证
        </div>
        <ul className="list-disc list-inside space-y-0.5 ml-1">
          <li>✅ <strong>内容去重</strong>：相同 query + ai_prediction 组合只入库一次</li>
          <li>✅ <strong>价值权重</strong>：依据 confidence 分数自动排序</li>
          <li>✅ <strong>溯源追踪</strong>：所有记录保留 persona、tone、dialogue_path</li>
        </ul>
      </div>

      {/* 对话详情弹窗 */}
      {selectedLog && (
        <DialogueModal
          log={selectedLog}
          onClose={() => setSelectedLog(null)}
        />
      )}
    </div>
  );
};

export default KnowledgeInbox;