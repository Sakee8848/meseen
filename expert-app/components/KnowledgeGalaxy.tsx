"use client";

import React, { useEffect, useState, useCallback } from 'react';
import ReactFlow, { 
  Background, 
  Controls, 
  useNodesState, 
  useEdgesState, 
  Position,
  Node
} from 'reactflow';
import 'reactflow/dist/style.css';
import dagre from 'dagre';
import { Database, Network, GitGraph, X, MessageSquare } from 'lucide-react';

const API_BASE = "http://127.0.0.1:8000/api";

// --- 布局配置 ---
const nodeWidth = 220;
const nodeHeight = 80;

const getLayoutedElements = (nodes: any[], edges: any[], direction = 'TB') => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({ rankdir: direction });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    node.targetPosition = direction === 'LR' ? Position.Left : Position.Top;
    node.sourcePosition = direction === 'LR' ? Position.Right : Position.Bottom;
    node.position = {
      x: nodeWithPosition.x - nodeWidth / 2,
      y: nodeWithPosition.y - nodeHeight / 2,
    };
    return node;
  });

  return { nodes: layoutedNodes, edges };
};

export default function KnowledgeGalaxy() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [stats, setStats] = useState({ cases: 0, services: 0 });
  
  // 🔬 显微镜状态：当前选中的案例详情
  const [selectedCase, setSelectedCase] = useState<any>(null);

  const fetchGraph = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/knowledge`);
      const json = await res.json();
      const records = json.records || [];

      // --- 1. 数据聚合 ---
      const serviceMap = new Map(); 
      
      records.forEach((r: any) => {
        const service = r.expert_diagnosis || "未分类服务";
        const intent = r.secret_intent || "未知用户需求";
        
        if (!serviceMap.has(service)) {
          serviceMap.set(service, []);
        }
        
        // 把完整记录(包含对话历史)存进去，而不仅仅是字符串
        // 只有当意图不重复时才添加 (简单去重)
        const existing = serviceMap.get(service).find((item: any) => item.intent === intent);
        if (!existing) {
            serviceMap.get(service).push({
                intent: intent,
                fullRecord: r // <--- 关键：把整个案宗藏在这里
            });
        }
      });

      setStats({ cases: records.length, services: serviceMap.size });

      // --- 2. 构建节点 ---
      const initialNodes = [];
      const initialEdges = [];

      // Root
      initialNodes.push({
        id: 'root',
        data: { label: '🏢 Human Resources' },
        style: { 
            background: '#0f172a', color: '#fff', fontSize: 16, fontWeight: 'bold', 
            width: 180, borderRadius: '8px', border: 'none', display: 'flex', justifyContent: 'center', alignItems: 'center',
            boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
        }
      });

      let serviceIndex = 0;
      serviceMap.forEach((items, serviceName) => {
        const serviceId = `svc-${serviceIndex}`;
        
        // Service Node
        initialNodes.push({
          id: serviceId,
          data: { label: serviceName },
          style: { 
            background: '#2563eb', color: '#fff', fontSize: 14, fontWeight: '500',
            width: 200, borderRadius: '6px', border: 'none', display: 'flex', justifyContent: 'center', alignItems: 'center',
            boxShadow: '0 4px 6px -1px rgb(37 99 235 / 0.3)'
          }
        });

        initialEdges.push({
          id: `e-root-${serviceId}`,
          source: 'root',
          target: serviceId,
          type: 'smoothstep',
          style: { stroke: '#94a3b8', strokeWidth: 1.5 }
        });

        // Intent Nodes (Leafs)
        items.forEach((item: any, i: number) => {
          const intentId = `intent-${serviceIndex}-${i}`;
          const safeIntent = String(item.intent);
          const labelText = safeIntent.length > 18 ? safeIntent.substring(0, 18) + "..." : safeIntent;

          initialNodes.push({
            id: intentId,
            // 🔬 关键：把历史记录塞进 data 里的 hiddenDetail 字段
            data: { 
                label: `🗣️ ${labelText}`,
                hiddenDetail: item.fullRecord 
            },
            style: { 
                fontSize: 12, background: '#fff', color: '#475569', 
                width: 190, border: '1px solid #e2e8f0', borderRadius: '4px',
                padding: '8px', cursor: 'pointer', // 手型光标，提示可点击
                transition: 'all 0.2s'
            }
          });

          initialEdges.push({
            id: `e-${serviceId}-${intentId}`,
            source: serviceId,
            target: intentId,
            type: 'default',
            style: { stroke: '#cbd5e1' }
          });
        });

        serviceIndex++;
      });
      
      const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(initialNodes, initialEdges, 'TB');
      setNodes(layoutedNodes);
      setEdges(layoutedEdges);

    } catch (err) {
      console.error("图谱生成失败:", err);
    }
  }, [setNodes, setEdges]);

  useEffect(() => {
    fetchGraph();
  }, [fetchGraph]);

  // 🔬 点击事件处理
  const onNodeClick = (_: React.MouseEvent, node: Node) => {
    if (node.data.hiddenDetail) {
        setSelectedCase(node.data.hiddenDetail);
    } else {
        setSelectedCase(null);
    }
  };

  return (
    <div className="h-full w-full flex flex-col relative overflow-hidden">
       {/* 顶部栏 */}
       <div className="bg-white border-b flex justify-between items-center px-6 py-3 shadow-sm z-10">
          <div className="flex items-center gap-2 text-gray-800 font-bold">
             <div className="bg-indigo-100 p-1.5 rounded-md text-indigo-600">
                <GitGraph size={20}/> 
             </div>
             <span>Meseeing 行业知识图谱</span>
          </div>
          <div className="text-xs text-gray-500 flex gap-6">
             <span className="flex items-center gap-1.5"><Database size={14} className="text-gray-400"/> 累计案例: <span className="font-mono font-bold text-gray-800">{stats.cases}</span></span>
             <span className="flex items-center gap-1.5"><Network size={14} className="text-blue-500"/> 已挖掘服务: <span className="font-mono font-bold text-blue-600">{stats.services}</span></span>
          </div>
       </div>

       {/* 画布区域 */}
       <div className="flex-1 bg-slate-50 relative">
          <ReactFlow 
            nodes={nodes} 
            edges={edges} 
            onNodesChange={onNodesChange} 
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick} // <--- 绑定点击事件
            fitView
            attributionPosition="bottom-right"
          >
             <Background color="#94a3b8" gap={25} size={1} />
             <Controls showInteractive={false} />
          </ReactFlow>

          {/* 🔬 侧边显微镜面板 (Slide-over) */}
          <div className={`absolute top-0 right-0 h-full w-96 bg-white shadow-2xl transform transition-transform duration-300 ease-in-out border-l border-gray-200 z-20 flex flex-col ${selectedCase ? 'translate-x-0' : 'translate-x-full'}`}>
            
            {selectedCase && (
                <>
                    {/* Header */}
                    <div className="p-4 border-b bg-gray-50 flex justify-between items-start">
                        <div>
                            <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider mb-1">🔍 显微镜视图</h3>
                            <p className="text-xs text-gray-500">ID: {selectedCase.id}</p>
                        </div>
                        <button onClick={() => setSelectedCase(null)} className="text-gray-400 hover:text-gray-600 transition">
                            <X size={20} />
                        </button>
                    </div>

                    {/* Content */}
                    <div className="flex-1 overflow-y-auto p-4 space-y-6">
                        {/* 1. 原始意图 */}
                        <div className="bg-yellow-50 p-3 rounded-lg border border-yellow-100">
                            <h4 className="text-xs font-bold text-yellow-700 mb-1 flex items-center gap-1">
                                🕵️ 用户真实意图 (Secret)
                            </h4>
                            <p className="text-sm text-gray-800 italic">"{selectedCase.secret_intent}"</p>
                        </div>

                        {/* 2. 对话回放 */}
                        <div>
                            <h4 className="text-xs font-bold text-gray-400 uppercase mb-3 flex items-center gap-1">
                                <MessageSquare size={12}/> 挖掘过程回放
                            </h4>
                            <div className="space-y-4">
                                {selectedCase.dialogue_path.map((step: any, idx: number) => (
                                    <div key={idx} className="relative pl-4 border-l-2 border-gray-200 pb-4 last:border-0 last:pb-0">
                                        <div className="absolute -left-[5px] top-0 w-2.5 h-2.5 rounded-full bg-gray-300"></div>
                                        
                                        {/* 专家问 */}
                                        <div className="mb-2">
                                            <span className="text-[10px] font-bold text-indigo-600 bg-indigo-50 px-1.5 py-0.5 rounded">AI Expert</span>
                                            <p className="text-xs text-gray-700 mt-1 leading-relaxed bg-gray-50 p-2 rounded-md rounded-tl-none">
                                                {step.expert_question}
                                            </p>
                                        </div>

                                        {/* 小白答 */}
                                        <div className="text-right">
                                             <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded">User</span>
                                             <p className="text-xs text-gray-800 mt-1 leading-relaxed bg-blue-50 p-2 rounded-md rounded-tr-none inline-block text-left">
                                                {step.novice_response}
                                            </p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* 3. 最终诊断 */}
                        <div className="bg-indigo-600 text-white p-4 rounded-lg shadow-md mt-4">
                             <h4 className="text-xs font-bold text-indigo-200 uppercase mb-1">✅ 最终确诊服务</h4>
                             <p className="font-bold text-lg">{selectedCase.expert_diagnosis}</p>
                             <p className="text-xs text-indigo-200 mt-2 pt-2 border-t border-indigo-500/30">
                                {selectedCase.final_conclusion}
                             </p>
                        </div>
                    </div>
                </>
            )}
          </div>
       </div>
    </div>
  );
}