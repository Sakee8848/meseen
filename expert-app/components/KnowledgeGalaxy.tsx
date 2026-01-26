import React, { useEffect, useCallback } from 'react';
import ReactFlow, {
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Edge,
  MarkerType,
  Background,
  Controls,
  MiniMap
} from 'reactflow';
import 'reactflow/dist/style.css';

// 初始根节点
const initialNodes = [
  {
    id: 'root',
    type: 'input',
    data: { label: '🏢 Human Resources' },
    position: { x: 400, y: 50 },
    style: { 
      background: '#111827', 
      color: 'white', 
      border: '1px solid #374151', 
      width: 180, 
      fontWeight: 'bold',
      fontSize: '16px',
      borderRadius: '8px',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
    },
  },
];

export const KnowledgeGalaxy = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // 核心：从后端拉取最新的图谱数据
  const fetchGraphData = useCallback(async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/taxonomy");
      const data = await res.json();
      
      // 适配 V1.1 新结构 (taxonomy)
      if (!data.taxonomy) return;

      const newNodes = [...initialNodes];
      const newEdges = [];
      
      let categoryX = 50;
      const categoryY = 200;
      const serviceY = 400;

      data.taxonomy.forEach((category: any, catIndex: number) => {
        // 1. 创建大类节点
        const catId = `cat-${catIndex}`;
        newNodes.push({
          id: catId,
          data: { label: category.name.split(' ')[0] }, // 只显示中文名，简短点
          position: { x: categoryX, y: categoryY },
          style: { 
            background: '#2563EB', 
            color: 'white', 
            border: 'none',
            borderRadius: '6px',
            width: 150,
            fontSize: '12px'
          },
        });

        // 连接 根 -> 大类
        newEdges.push({
          id: `e-root-${catId}`,
          source: 'root',
          target: catId,
          type: 'smoothstep',
          animated: true,
          style: { stroke: '#4B5563' },
        });

        // 2. 创建服务节点 (修正：现在 services 是字符串数组)
        category.services.forEach((serviceName: string, servIndex: number) => {
          const servId = `serv-${catIndex}-${servIndex}`;
          newNodes.push({
            id: servId,
            data: { label: serviceName },
            position: { x: categoryX, y: serviceY + (servIndex * 60) }, // 垂直排列
            style: { 
              background: '#FFFFFF', 
              color: '#374151', 
              border: '1px solid #E5E7EB',
              fontSize: '10px',
              width: 140,
            },
          });

          // 连接 大类 -> 服务
          newEdges.push({
            id: `e-${catId}-${servId}`,
            source: catId,
            target: servId,
            type: 'default',
            markerEnd: { type: MarkerType.ArrowClosed, color: '#9CA3AF' },
            style: { stroke: '#9CA3AF' },
          });
        });

        // 计算下一个大类的 X 坐标 (拉开间距)
        categoryX += 200;
      });

      setNodes(newNodes);
      setEdges(newEdges);

    } catch (err) {
      console.error("Failed to fetch graph", err);
    }
  }, [setNodes, setEdges]);

  // 组件加载时，拉取一次数据
  useEffect(() => {
    fetchGraphData();
    
    // 设置一个定时器，每 5 秒自动刷新一次，这样你注入新知识后，不用刷新页面就能看到变化！
    const interval = setInterval(fetchGraphData, 5000);
    return () => clearInterval(interval);
  }, [fetchGraphData]);

  const onConnect = useCallback((params: Edge | Connection) => setEdges((eds) => addEdge(params, eds)), [setEdges]);

  return (
    <div style={{ width: '100%', height: '100%' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        fitView
        attributionPosition="bottom-right"
      >
        <Background color="#333" gap={16} />
        <Controls />
        <MiniMap style={{ height: 120 }} zoomable pannable />
      </ReactFlow>
    </div>
  );
};

// 必须使用 default 导出，以匹配 page.tsx 的引用方式
export default KnowledgeGalaxy;