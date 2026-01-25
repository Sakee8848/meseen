"use client";

import React, { useState, useCallback } from 'react';
import ReactFlow, { 
  Background, 
  Controls, 
  useNodesState, 
  useEdgesState, 
  MarkerType 
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Play, FastForward, CheckCircle, AlertCircle } from 'lucide-react';

// API 地址
const API_BASE = "http://127.0.0.1:8000/api";

export default function SimulationMonitor() {
  const [loading, setLoading] = useState(false);
  const [secretMission, setSecretMission] = useState<string>("");
  const [turnCount, setTurnCount] = useState(0);
  const [isConcluded, setIsConcluded] = useState(false);
  const [logs, setLogs] = useState<any[]>([]);

  // React Flow 状态
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // 1. 启动仿真
  const handleStart = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ domain: "hr" })
      });
      const data = await res.json();
      
      setSecretMission(data.secret_preview);
      setTurnCount(0);
      setIsConcluded(false);
      setLogs([]);
      
      // 重置图表
      setNodes([
        { 
          id: 'start', 
          position: { x: 250, y: 0 }, 
          data: { label: '🚀 开始诊断' }, 
          type: 'input',
          style: { background: '#3b82f6', color: 'white', border: 'none' }
        }
      ]);
      setEdges([]);
      
    } catch (err) {
      console.error(err);
      alert("启动失败，请检查后端是否运行！");
    }
    setLoading(false);
  };

  // 2. 下一步
  const handleNext = async () => {
    if (loading || isConcluded) return;
    setLoading(true);
    
    try {
      const res = await fetch(`${API_BASE}/next`, { method: "POST" });
      const data = await res.json();
      
      if (data.status === "Finished") {
        setIsConcluded(true);
        setLoading(false);
        return;
      }

      setTurnCount(data.turn);
      setIsConcluded(data.concluded);
      
      // 处理对话数据
      const exchange = data.latest_exchange || [];
      const expertMsg = exchange.find((m:any) => m.role === 'expert')?.content || "Thinking...";
      const noviceMsg = exchange.find((m:any) => m.role === 'novice')?.content || "(Silently agrees)";

      setLogs(prev => [...prev, ...exchange]);

      // --- 动态画图逻辑 ---
      const newY = (data.turn) * 150; // 每一轮往下移一点
      const nodeId = `turn-${data.turn}`;
      
      // 添加专家节点 (问题)
      const newNode = {
        id: nodeId,
        position: { x: 250, y: newY },
        data: { label: expertMsg.length > 20 ? expertMsg.substring(0, 20) + '...' : expertMsg },
        style: { 
            background: data.concluded ? '#10b981' : '#fff', 
            border: data.concluded ? '2px solid #10b981' : '1px solid #777',
            width: 200,
            fontSize: 12
        }
      };

      setNodes((nds) => nds.concat(newNode));

      // 添加连线 (小白的回答作为线上的标签)
      const lastNodeId = data.turn === 1 ? 'start' : `turn-${data.turn - 1}`;
      const newEdge = {
        id: `e-${lastNodeId}-${nodeId}`,
        source: lastNodeId,
        target: nodeId,
        label: noviceMsg.length > 15 ? noviceMsg.substring(0, 15) + '...' : noviceMsg,
        markerEnd: { type: MarkerType.ArrowClosed },
        style: { stroke: '#888' },
        labelStyle: { fill: '#888', fontSize: 10 }
      };

      setEdges((eds) => eds.concat(newEdge));
      // ------------------

    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  return (
    <div className="flex h-screen w-full flex-col bg-gray-50">
      {/* 顶部栏 */}
      <div className="flex items-center justify-between bg-white px-6 py-4 shadow-sm border-b">
        <div>
          <h1 className="text-xl font-bold text-gray-800">密心 (Mixin) 专家逆向工程台</h1>
          <p className="text-sm text-gray-500">盲测模式: Human Resources</p>
        </div>
        <div className="flex gap-3">
            <button 
                onClick={handleStart}
                className="flex items-center gap-2 bg-black text-white px-4 py-2 rounded-md hover:bg-gray-800 transition"
            >
                <Play size={16} /> 重置/开始
            </button>
            <button 
                onClick={handleNext}
                disabled={loading || isConcluded}
                className={`flex items-center gap-2 px-4 py-2 rounded-md transition ${isConcluded ? 'bg-green-100 text-green-700' : 'bg-blue-600 text-white hover:bg-blue-700'} disabled:opacity-50`}
            >
                {isConcluded ? <CheckCircle size={16}/> : <FastForward size={16}/>}
                {isConcluded ? "已完成" : "下一步"}
            </button>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* 左侧：情报面板 */}
        <div className="w-1/3 bg-white border-r flex flex-col">
            <div className="p-4 bg-yellow-50 border-b border-yellow-100">
                <h3 className="text-xs font-bold text-yellow-800 uppercase mb-1">Top Secret Mission</h3>
                {secretMission ? (
                    <p className="text-sm text-gray-800 font-medium">🕵️ 真实意图: {secretMission}</p>
                ) : (
                    <p className="text-sm text-gray-400 italic">等待任务分配...</p>
                )}
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {logs.map((log, i) => (
                    <div key={i} className={`flex ${log.role === 'expert' ? 'justify-start' : 'justify-end'}`}>
                        <div className={`max-w-[85%] rounded-lg p-3 text-sm ${
                            log.role === 'expert' 
                            ? 'bg-gray-100 text-gray-800 rounded-tl-none' 
                            : 'bg-blue-50 text-blue-900 rounded-tr-none'
                        }`}>
                            <span className="block text-xs font-bold mb-1 opacity-50">
                                {log.role === 'expert' ? '🤖 AI Expert' : '👤 Novice User'}
                            </span>
                            {log.content}
                        </div>
                    </div>
                ))}
            </div>
        </div>

        {/* 右侧：React Flow 画布 */}
        <div className="flex-1 bg-gray-50 relative">
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                fitView
            >
                <Background />
                <Controls />
            </ReactFlow>
            
            {!secretMission && (
                <div className="absolute inset-0 flex items-center justify-center bg-white/50 backdrop-blur-sm z-10">
                    <div className="text-center text-gray-400">
                        <AlertCircle className="mx-auto mb-2" size={48}/>
                        <p>请点击左上角的“开始”按钮</p>
                    </div>
                </div>
            )}
        </div>
      </div>
    </div>
  );
}