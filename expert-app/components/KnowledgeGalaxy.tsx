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
import { Network, X, User, Bot, Search, FileText } from 'lucide-react';

// --- 类型定义 ---
interface TaxonomyCategory {
  name: string;
  services: string[];
}

interface TaxonomyData {
  taxonomy: TaxonomyCategory[];
}

interface LogItem {
  id: string;
  timestamp: string;
  query: string;
  ai_prediction: string;
  ai_reasoning: string;
  confidence: number;
}

// --- 组件：显微镜弹窗 (增强版) ---
const NodeDetailModal = ({ node, linkedLog, onClose }: { node: any, linkedLog?: LogItem, onClose: () => void }) => {
  if (!node) return null;
  
  const isRoot = node.id === 'root';
  const isCategory = node.data.label.includes('【') || node.id.startsWith('cat-'); 

  return (
    <div className="absolute top-4 right-4 z-50 w-80 bg-black/90 backdrop-blur-md border border-gray-700 rounded-xl text-white shadow-2xl animate-in slide-in-from-right overflow-hidden flex flex-col max-h-[80vh]">
      
      {/* 标题栏 */}
      <div className="flex justify-between items-center p-4 border-b border-gray-800 bg-gray-900/50">
        <h3 className="text-sm font-bold text-blue-400 uppercase tracking-wider flex items-center gap-2">
          <Network size={16} /> 知识节点显微镜
        </h3>
        <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors">
          <X size={18} />
        </button>
      </div>
      
      <div className="p-5 overflow-y-auto custom-scrollbar space-y-6">
        
        {/* 1. 节点基本信息 */}
        <div>
          <div className="text-[10px] text-gray-500 mb-1 uppercase tracking-widest">NODE ENTITY</div>
          <div className="text-xl font-bold text-white leading-tight">
            {node.data.label}
          </div>
          <div className="mt-2 flex gap-2">
            <span className={`text-[10px] px-2 py-1 rounded font-mono ${
              isRoot ? 'bg-blue-900 text-blue-200' : 
              isCategory ? 'bg-purple-900 text-purple-200' : 
              'bg-emerald-900 text-emerald-200'
            }`}>
              {isRoot ? 'ROOT' : isCategory ? 'CATEGORY' : 'SERVICE LEAF'}
            </span>
            <span className="text-[10px] px-2 py-1 rounded bg-gray-800 text-gray-400 font-mono">
              ID: {node.id}
            </span>
          </div>
        </div>

        {/* 2. 溯源档案 (如果有 Log 关联) */}
        {linkedLog ? (
          <div className="space-y-4 pt-4 border-t border-gray-800 animate-in fade-in duration-500">
            <div className="flex items-center gap-2 text-yellow-500 mb-2">
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
            </div>

            {/* AI 诊断 */}
            <div className="bg-blue-900/20 p-3 rounded-lg border border-blue-800/30">
              <div className="flex items-center gap-2 text-blue-400 text-[10px] mb-1 uppercase">
                <Bot size={10} /> AI 诊断思路 ({linkedLog.confidence}%)
              </div>
              <p className="text-xs text-blue-100 leading-relaxed">
                {linkedLog.ai_reasoning}
              </p>
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
                <span className="text-xs">该节点为人工预设，无 AI 对话记录</span>
              </div>
            </div>
          )
        )}

      </div>
    </div>
  );
};

// --- 主组件 ---
const KnowledgeGalaxy = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  
  // 状态：选中的节点 + 关联的日志
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [linkedLog, setLinkedLog] = useState<LogItem | undefined>(undefined);
  
  // 缓存：存储所有的 logs，用于点击时查找
  const [logsCache, setLogsCache] = useState<LogItem[]>([]);

  // 1. 获取所有数据 (Graph + Logs)
  const fetchAllData = useCallback(async () => {
    try {
      // 并行请求：获取星图结构 + 获取日志档案
      const [taxRes, logsRes] = await Promise.all([
        fetch("http://127.0.0.1:8000/api/taxonomy"),
        fetch("http://127.0.0.1:8000/api/knowledge/logs")
      ]);

      const taxData: TaxonomyData = await taxRes.json();
      const logsData: LogItem[] = await logsRes.json();
      
      setLogsCache(logsData); // 存入缓存

      // --- 构建图谱 (保持原逻辑) ---
      const newNodes: Node[] = [];
      const newEdges: Edge[] = [];
      
      newNodes.push({
        id: 'root',
        data: { label: '🏢 Human Resources' },
        position: { x: 400, y: 0 },
        style: { background: '#0f172a', color: '#fff', border: '1px solid #334155', width: 200, borderRadius: '8px', fontWeight: 'bold' },
      });

      let catX = 0;
      taxData.taxonomy.forEach((category, catIndex) => {
        const catId = `cat-${catIndex}`;
        const catNodeX = catIndex * 280;
        const catNodeY = 150;

        newNodes.push({
          id: catId,
          data: { label: category.name },
          position: { x: catNodeX, y: catNodeY },
          style: { background: '#1e40af', color: '#fff', border: 'none', width: 220, fontWeight: '600', borderRadius: '6px', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.5)' },
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
          
          // 💡 高亮逻辑：如果这个服务在 logs 里有记录，给它一点特殊的样式（例如边框变绿）
          const hasLog = logsData.some(l => l.ai_prediction === service);
          
          newNodes.push({
            id: svcId,
            data: { label: service },
            position: { x: catNodeX + 10, y: catNodeY + 100 + (svcIndex * 70) },
            style: { 
              background: '#ffffff', 
              color: '#334155', 
              border: hasLog ? '2px solid #10b981' : '1px solid #e2e8f0', // 有记录的显绿色
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
  }, [setNodes, setEdges]);

  // 2. 监听自动刷新
  useEffect(() => {
    fetchAllData();
    const handleRefresh = () => {
      console.log("⚡️ 收到刷新信号，正在更新星图...");
      fetchAllData();
    };
    window.addEventListener('taxonomyUpdated', handleRefresh);
    return () => window.removeEventListener('taxonomyUpdated', handleRefresh);
  }, [fetchAllData]);

  // 3. 点击事件处理
  const onNodeClick = useCallback((event: any, node: Node) => {
    setSelectedNode(node);
    
    // 🔍 核心逻辑：去 Logs 缓存里找“谁生成了这个节点”
    // 注意：这里简单的用 name 匹配。如果有多个 log 指向同一个服务，这里取最新的一个。
    const match = logsCache.find(log => log.ai_prediction === node.data.label);
    setLinkedLog(match);
    
  }, [logsCache]);

  return (
    <div style={{ height: '100%', width: '100%', background: '#020617' }} className="relative group">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        fitView
      >
        <Background color="#1e293b" gap={24} size={1} />
        <Controls style={{ fill: '#fff', backgroundColor: '#334155', border: 'none' }} />
      </ReactFlow>

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