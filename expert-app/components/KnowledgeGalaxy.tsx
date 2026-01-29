import React, { useCallback, useEffect, useState } from 'react';
import ReactFlow, {
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  Node,
  Edge,
  MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Network, X, User, Bot, Search, FileText, MessageSquare, PieChart, Info, RefreshCw } from 'lucide-react';

// --- 类型定义 ---
interface TraceRecord {
  id: string;
  timestamp: string;
  query: string;
  ai_prediction: string;
  confidence: number;
  source: string;
  persona?: string;
  tone?: string;
  // 🆕 V6.0 新增字段
  dialogue_path?: Array<{ step: number; role: string; content: string }>;
  ground_truth?: string;
  diagnosis_correct?: boolean;
  total_turns?: number;
  key_questions?: string[];
  diagnosis_trace?: any[];
}

interface TaxonomyCategory {
  name: string;
  services: string[];
  trace_records?: { [key: string]: TraceRecord[] };
}

interface TaxonomyData {
  taxonomy: TaxonomyCategory[];
}

interface CoverageStats {
  coverage_rate: number;
  covered_count: number;
  estimated_total: number;
  service_node_count: number;
  covered_service_count: number;
  service_coverage_rate: number;
  dimensions: {
    [key: string]: {
      name: string;
      count: number;
      description: string;
    }
  };
  formula: {
    expression: string;
    estimated_total_formula: string;
    note: string;
  };
}

interface LogItem {
  id: string;
  timestamp: string;
  query: string;
  ai_prediction: string;
  ai_reasoning?: string;
  dialogue_path?: Array<{ step: number; role: string; content: string }>;
  confidence: number;
  persona?: string;
  tone?: string;
}

// --- 组件：显微镜弹窗 (简化版 - 移除对话详情) ---
const NodeDetailModal = ({ node, linkedLog, onClose }: { node: any, linkedLog?: LogItem, onClose: () => void }) => {
  if (!node) return null;

  const isRoot = node.id === 'root';
  const isCategory = node.data.label.includes('【') || node.id.startsWith('cat-');
  const hasTrace = !!linkedLog;

  return (
    <div className="absolute top-4 right-4 z-50 w-[360px] bg-black/90 backdrop-blur-md border border-gray-700 rounded-xl text-white shadow-2xl animate-in slide-in-from-right overflow-hidden">

      {/* 标题栏 */}
      <div className="flex justify-between items-center p-4 border-b border-gray-800 bg-gray-900/50">
        <h3 className="text-sm font-bold text-blue-400 uppercase tracking-wider flex items-center gap-2">
          <Network size={16} /> 知识节点显微镜
        </h3>
        <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors">
          <X size={18} />
        </button>
      </div>

      <div className="p-5 space-y-4">

        {/* 1. 节点基本信息 */}
        <div>
          <div className="text-[10px] text-gray-500 mb-1 uppercase tracking-widest">NODE ENTITY</div>
          <div className="text-xl font-bold text-white leading-tight">
            {node.data.label}
          </div>
          <div className="mt-2 flex gap-2 flex-wrap">
            <span className={`text-[10px] px-2 py-1 rounded font-mono ${isRoot ? 'bg-blue-900 text-blue-200' :
              isCategory ? 'bg-purple-900 text-purple-200' :
                'bg-emerald-900 text-emerald-200'
              }`}>
              {isRoot ? 'ROOT' : isCategory ? 'CATEGORY' : 'SERVICE LEAF'}
            </span>
            <span className="text-[10px] px-2 py-1 rounded bg-gray-800 text-gray-400 font-mono">
              ID: {node.id}
            </span>
            {hasTrace && (
              <span className="text-[10px] px-2 py-1 rounded bg-green-900/50 text-green-300 flex items-center gap-1">
                ✨ AI 已生成
              </span>
            )}
          </div>
        </div>

        {/* 2. 溯源档案概览 */}
        {linkedLog ? (
          <div className="space-y-3 pt-4 border-t border-gray-800 animate-in fade-in duration-500">
            <div className="flex items-center gap-2 text-yellow-500">
              <Search size={14} />
              <span className="text-xs font-bold uppercase tracking-wider">溯源档案 (Traceability)</span>
            </div>

            {/* 用户原话 */}
            <div className="bg-gray-800/50 p-3 rounded-lg border border-gray-700">
              <div className="flex items-center gap-2 text-gray-400 text-[10px] mb-1 uppercase">
                <User size={10} /> 原始用户意图
              </div>
              <p className="text-sm text-gray-200 italic leading-relaxed">
                "{linkedLog.query}"
              </p>
              {linkedLog.persona && (
                <div className="mt-2 text-xs text-gray-500">
                  角色: {linkedLog.persona} {linkedLog.tone && `| 语气: ${linkedLog.tone}`}
                </div>
              )}
            </div>

            {/* AI 诊断结论 */}
            <div className="bg-blue-900/20 p-3 rounded-lg border border-blue-800/30">
              <div className="flex items-center gap-2 text-blue-400 text-[10px] mb-1 uppercase">
                <Bot size={10} /> AI 诊断结论
              </div>
              <p className="text-sm text-blue-100 font-medium">
                → {linkedLog.ai_prediction}
              </p>
              <div className="mt-2 text-[10px] text-gray-500">
                置信度: {(linkedLog.confidence * 100).toFixed(0)}%
              </div>
            </div>

            <div className="text-[10px] text-gray-600 text-right">
              生成时间: {linkedLog.timestamp}
            </div>
          </div>
        ) : (
          !isRoot && !isCategory && (
            <div className="pt-4 border-t border-gray-800 text-center">
              <div className="inline-flex flex-col items-center gap-2 text-gray-600">
                <FileText size={24} className="opacity-20" />
                <span className="text-xs">该节点为人工预设</span>
                <span className="text-[10px] text-gray-700">运行批量挖矿后将自动关联溯源档案</span>
              </div>
            </div>
          )
        )}
      </div>
    </div>
  );
};

// --- 覆盖率统计组件 (新版：基于真实世界预估) ---
const CoverageStats = ({ stats, onRefresh }: { stats: CoverageStats | null, onRefresh: () => void }) => {
  const [showTooltip, setShowTooltip] = useState(false);

  if (!stats) {
    return (
      <div className="absolute top-4 left-4 z-40 bg-black/80 backdrop-blur-md border border-gray-700 rounded-lg p-3 text-white text-xs">
        <div className="flex items-center gap-2 text-gray-400">
          <RefreshCw size={14} className="animate-spin" />
          加载覆盖率统计...
        </div>
      </div>
    );
  }

  const coveragePercent = stats.coverage_rate;

  return (
    <div className="absolute top-4 left-4 z-40 bg-black/90 backdrop-blur-md border border-gray-700 rounded-lg p-4 text-white text-xs min-w-[280px]">
      {/* 标题 */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2 text-blue-400 font-medium">
          <PieChart size={14} />
          知识库覆盖统计
        </div>
        <button
          onClick={onRefresh}
          className="p-1 hover:bg-white/10 rounded transition-colors"
          title="刷新统计"
        >
          <RefreshCw size={12} className="text-gray-500 hover:text-white" />
        </button>
      </div>

      {/* 核心覆盖率 */}
      <div className="mb-4 p-3 bg-gradient-to-r from-blue-900/40 to-purple-900/40 rounded-lg border border-blue-500/20">
        <div className="flex justify-between items-center mb-2">
          <span className="text-gray-300">真实世界覆盖率:</span>
          <span className={`font-bold text-xl ${coveragePercent >= 10 ? 'text-green-400' :
            coveragePercent >= 5 ? 'text-yellow-400' :
              'text-orange-400'
            }`}>
            {coveragePercent.toFixed(2)}%
          </span>
        </div>
        <div className="w-full h-2.5 bg-gray-700 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-700 ${coveragePercent >= 10 ? 'bg-gradient-to-r from-green-500 to-emerald-400' :
              coveragePercent >= 5 ? 'bg-gradient-to-r from-yellow-500 to-orange-400' :
                'bg-gradient-to-r from-orange-500 to-red-400'
              }`}
            style={{ width: `${Math.min(coveragePercent * 10, 100)}%` }} // 放大显示 10 倍
          />
        </div>
        <div className="text-[10px] text-gray-500 mt-1 text-right">
          进度条放大 10 倍显示
        </div>
      </div>

      {/* 统计数据 */}
      <div className="space-y-1.5 mb-3">
        <div className="flex justify-between gap-4">
          <span className="text-gray-400">已覆盖知识点:</span>
          <span className="font-mono text-green-400">{stats.covered_count.toLocaleString()}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-gray-400">预估总知识点:</span>
          <span className="font-mono text-yellow-400">{stats.estimated_total.toLocaleString()}</span>
        </div>
        <div className="flex justify-between gap-4 border-t border-gray-700 pt-1.5 mt-2">
          <span className="text-gray-400">服务节点覆盖:</span>
          <span className="font-mono text-blue-400">{stats.covered_service_count}/{stats.service_node_count}</span>
        </div>
      </div>

      {/* 公式说明 (可展开) */}
      <div className="relative">
        <button
          onClick={() => setShowTooltip(!showTooltip)}
          className="flex items-center gap-1 text-[10px] text-gray-500 hover:text-gray-300 transition-colors"
        >
          <Info size={10} />
          <span>查看计算公式</span>
        </button>

        {showTooltip && (
          <div className="absolute top-6 left-0 right-0 bg-gray-900 border border-gray-700 rounded-lg p-3 text-[10px] z-10 shadow-xl">
            <div className="text-gray-300 mb-2">
              <strong className="text-white">📐 覆盖率公式</strong>
            </div>
            <div className="text-gray-400 mb-2">
              {stats.formula?.expression}
            </div>
            <div className="text-gray-500 mb-2 border-t border-gray-700 pt-2">
              <strong>预估总数计算:</strong>
              <br />
              {stats.formula?.estimated_total_formula}
            </div>
            <div className="text-blue-400">
              💡 {stats.formula?.note}
            </div>

            {/* 维度明细 */}
            <div className="mt-2 pt-2 border-t border-gray-700">
              <strong className="text-gray-300">各维度配置:</strong>
              <div className="mt-1 space-y-0.5">
                {stats.dimensions && Object.entries(stats.dimensions).map(([key, dim]) => (
                  <div key={key} className="flex justify-between text-gray-500">
                    <span>{dim.name}:</span>
                    <span className="text-gray-400">{dim.count} 种</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// --- 主组件 ---
const KnowledgeGalaxy = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // 状态
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [linkedLog, setLinkedLog] = useState<LogItem | undefined>(undefined);
  const [logsCache, setLogsCache] = useState<LogItem[]>([]);
  const [taxonomyCache, setTaxonomyCache] = useState<TaxonomyCategory[]>([]);
  const [coverageStats, setCoverageStats] = useState<CoverageStats | null>(null);

  // API 地址
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

  // 获取覆盖率统计
  const fetchCoverage = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/coverage`);
      const data = await res.json();
      setCoverageStats(data);
    } catch (err) {
      console.error("Failed to fetch coverage", err);
    }
  }, [API_BASE]);

  // 获取星图数据
  const fetchAllData = useCallback(async () => {
    try {
      const [taxRes, logsRes] = await Promise.all([
        fetch(`${API_BASE}/api/taxonomy`),
        fetch(`${API_BASE}/api/etl/inbox`)
      ]);

      const taxData: TaxonomyData = await taxRes.json();
      let logsData: LogItem[] = [];
      try {
        logsData = await logsRes.json();
        if (!Array.isArray(logsData)) logsData = [];
      } catch { logsData = []; }

      setLogsCache(logsData);
      setTaxonomyCache(taxData.taxonomy || []);

      // 构建图谱
      const newNodes: Node[] = [];
      const newEdges: Edge[] = [];

      newNodes.push({
        id: 'root',
        data: { label: '🏢 Human Resources' },
        position: { x: 400, y: 0 },
        style: { background: '#0f172a', color: '#fff', border: '1px solid #334155', width: 200, borderRadius: '8px', fontWeight: 'bold' },
      });

      taxData.taxonomy.forEach((category, catIndex) => {
        const catId = `cat-${catIndex}`;
        const catNodeX = catIndex * 280;
        const catNodeY = 150;

        const catRecordCount = category.trace_records
          ? Object.values(category.trace_records).reduce((sum, arr) => sum + arr.length, 0)
          : 0;

        newNodes.push({
          id: catId,
          data: { label: category.name, recordCount: catRecordCount },
          position: { x: catNodeX, y: catNodeY },
          style: {
            background: '#1e40af',
            color: '#fff',
            border: catRecordCount > 0 ? '2px solid #10b981' : 'none',
            width: 220,
            fontWeight: '600',
            borderRadius: '6px',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.5)'
          },
        });

        newEdges.push({
          id: `e-root-${catId}`,
          source: 'root',
          target: catId,
          type: 'smoothstep',
          style: { stroke: '#475569', strokeWidth: 1.5 },
        });

        category.services.forEach((service, svcIndex) => {
          const svcId = `svc-${catIndex}-${svcIndex}`;

          const hasTraceRecord = category.trace_records &&
            Object.keys(category.trace_records).some(key =>
              key.includes(service) || service.includes(key)
            );

          newNodes.push({
            id: svcId,
            data: { label: service },
            position: { x: catNodeX + 10, y: catNodeY + 100 + (svcIndex * 70) },
            style: hasTraceRecord ? {
              // 🆕 AI 生成的节点 - 醒目的金色发光效果
              background: 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)',
              color: '#92400e',
              border: '3px solid #f59e0b',
              width: 200,
              fontSize: '12px',
              fontWeight: '600',
              borderRadius: '8px',
              boxShadow: '0 0 20px rgba(245, 158, 11, 0.6), 0 0 40px rgba(245, 158, 11, 0.3)',
              animation: 'pulse 2s infinite'
            } : {
              // 普通节点
              background: '#ffffff',
              color: '#334155',
              border: '1px solid #e2e8f0',
              width: 200,
              fontSize: '12px',
              borderRadius: '4px'
            },
          });

          newEdges.push({
            id: `e-${catId}-${svcId}`,
            source: catId,
            target: svcId,
            type: 'smoothstep',
            markerEnd: { type: MarkerType.ArrowClosed, color: '#cbd5e1' },
            style: { stroke: '#cbd5e1' },
          });
        });
      });

      setNodes(newNodes);
      setEdges(newEdges);

    } catch (err) {
      console.error("Failed to load data", err);
    }
  }, [setNodes, setEdges, API_BASE]);

  // 初始化和监听刷新
  useEffect(() => {
    fetchAllData();
    fetchCoverage();

    const handleRefresh = () => {
      console.log("⚡️ 收到刷新信号...");
      fetchAllData();
      fetchCoverage();
    };
    window.addEventListener('taxonomyUpdated', handleRefresh);
    return () => window.removeEventListener('taxonomyUpdated', handleRefresh);
  }, [fetchAllData, fetchCoverage]);

  // 点击事件
  const onNodeClick = useCallback((event: any, node: Node) => {
    setSelectedNode(node);

    const serviceName = node.data.label;
    let matchedRecord: LogItem | undefined;

    for (const cat of taxonomyCache) {
      if (cat.trace_records) {
        for (const [key, records] of Object.entries(cat.trace_records)) {
          if (key.includes(serviceName) || serviceName.includes(key)) {
            if (records.length > 0) {
              // 获取最新的记录
              const r = records[records.length - 1];
              matchedRecord = {
                id: r.id,
                timestamp: r.timestamp,
                query: r.query,
                ai_prediction: r.ai_prediction,
                confidence: r.confidence,
                persona: r.persona,
                tone: r.tone,
                // 🆕 V6.0 新增：读取对话路径
                dialogue_path: r.dialogue_path,
                ai_reasoning: r.diagnosis_trace?.[0]?.diagnosis || `基于「${r.ai_prediction}」进行分类匹配`,
              };
              break;
            }
          }
        }
      }
      if (matchedRecord) break;
    }

    if (!matchedRecord) {
      matchedRecord = logsCache.find(log => log.ai_prediction === serviceName);
    }

    setLinkedLog(matchedRecord);
  }, [logsCache, taxonomyCache]);

  return (
    <div style={{ height: '100%', width: '100%', background: '#020617' }} className="relative group">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        fitView
        panOnDrag={true}
        panOnScroll={true}
        zoomOnScroll={true}
        zoomOnPinch={true}
        minZoom={0.3}
        maxZoom={2}
      >
        <Background color="#1e293b" gap={24} size={1} />
        <Controls style={{ fill: '#fff', backgroundColor: '#334155', border: 'none' }} />
      </ReactFlow>

      {/* 覆盖率统计 */}
      <CoverageStats stats={coverageStats} onRefresh={fetchCoverage} />

      {/* 显微镜弹窗 */}
      {selectedNode && (
        <NodeDetailModal
          node={selectedNode}
          linkedLog={linkedLog}
          onClose={() => {
            setSelectedNode(null);
            setLinkedLog(undefined);
          }}
        />
      )}

      {/* 提示文案 */}
      {!selectedNode && (
        <div className="absolute bottom-4 right-4 text-xs text-slate-600 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity">
          点击节点查看溯源档案
        </div>
      )}
    </div>
  );
};

export default KnowledgeGalaxy;