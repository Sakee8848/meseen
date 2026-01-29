'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { Play, Pause, Square, RefreshCw, Zap, CheckCircle, XCircle, Loader2 } from 'lucide-react';

interface BatchStatus {
    state: 'idle' | 'running' | 'paused' | 'cancelled' | 'completed' | 'unavailable';
    current_task: number;
    total_tasks: number;
    progress: string;
    progress_percent: number;
    elapsed_seconds: number;
    success_count: number;
    error_count: number;
    recent_results: Array<{ id: string; query: string; prediction: string }>;
    recent_errors: Array<{ id: string; error: string }>;
}

export const BatchControlPanel: React.FC = () => {
    const [status, setStatus] = useState<BatchStatus | null>(null);
    const [batchSize, setBatchSize] = useState(5);
    const [domain, setDomain] = useState('hr');
    const [loading, setLoading] = useState(false);

    const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

    const fetchStatus = useCallback(async () => {
        try {
            const res = await fetch(`${API_BASE}/api/batch/status`);
            const data = await res.json();
            setStatus(data);
        } catch (err) {
            console.error('Failed to fetch batch status', err);
        }
    }, [API_BASE]);

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 2000);
        return () => clearInterval(interval);
    }, [fetchStatus]);

    const handleStart = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE}/api/batch/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ batch_size: batchSize, domain })
            });
            const result = await res.json();
            if (result.status === 'started') {
                fetchStatus();
            } else {
                alert(`启动失败: ${result.message || '未知错误'}`);
            }
        } catch (err) {
            alert('无法连接服务器');
        }
        setLoading(false);
    };

    const handlePause = async () => {
        await fetch(`${API_BASE}/api/batch/pause`, { method: 'POST' });
        fetchStatus();
    };

    const handleResume = async () => {
        await fetch(`${API_BASE}/api/batch/resume`, { method: 'POST' });
        fetchStatus();
    };

    const handleCancel = async () => {
        if (!confirm('确定要取消当前批量任务吗？')) return;
        await fetch(`${API_BASE}/api/batch/cancel`, { method: 'POST' });
        fetchStatus();
    };

    const getStateColor = (state: string) => {
        switch (state) {
            case 'running': return 'text-green-500';
            case 'paused': return 'text-yellow-500';
            case 'completed': return 'text-blue-500';
            case 'cancelled': return 'text-red-500';
            default: return 'text-gray-500';
        }
    };

    const getStateText = (state: string) => {
        switch (state) {
            case 'idle': return '空闲';
            case 'running': return '运行中';
            case 'paused': return '已暂停';
            case 'completed': return '已完成';
            case 'cancelled': return '已取消';
            case 'unavailable': return '不可用';
            default: return state;
        }
    };

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    return (
        <div className="w-full max-w-6xl mx-auto p-6 bg-gradient-to-br from-indigo-900 via-purple-900 to-slate-900 rounded-2xl shadow-xl border border-purple-500/30">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                        <Zap className="text-yellow-400" size={28} />
                        批量 AI 互博引擎
                    </h2>
                    <p className="text-purple-300 text-sm mt-1">一键运行多轮仿真，自动提取专家知识点</p>
                </div>

                <button
                    onClick={fetchStatus}
                    className="p-2 hover:bg-white/10 rounded-full transition-colors"
                    title="刷新状态"
                >
                    <RefreshCw size={20} className="text-purple-300" />
                </button>
            </div>

            {/* 状态显示 */}
            {status && (
                <div className="mb-6 p-4 bg-black/30 rounded-xl border border-purple-500/20">
                    <div className="flex justify-between items-center">
                        <div className="flex items-center gap-4">
                            <span className={`text-lg font-bold ${getStateColor(status.state)}`}>
                                ● {getStateText(status.state)}
                            </span>
                            {status.state === 'running' && (
                                <Loader2 className="animate-spin text-green-400" size={20} />
                            )}
                        </div>

                        {status.elapsed_seconds > 0 && (
                            <span className="text-gray-400 text-sm">
                                ⏱️ {formatTime(status.elapsed_seconds)}
                            </span>
                        )}
                    </div>

                    {/* 进度条 */}
                    {status.total_tasks > 0 && (
                        <div className="mt-4">
                            <div className="flex justify-between text-sm text-gray-400 mb-1">
                                <span>进度: {status.progress}</span>
                                <span>{status.progress_percent}%</span>
                            </div>
                            <div className="w-full h-3 bg-gray-700 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-gradient-to-r from-green-500 to-emerald-400 transition-all duration-500"
                                    style={{ width: `${status.progress_percent}%` }}
                                />
                            </div>
                        </div>
                    )}

                    {/* 统计 */}
                    <div className="flex gap-6 mt-4">
                        <div className="flex items-center gap-2">
                            <CheckCircle className="text-green-400" size={18} />
                            <span className="text-green-400 font-medium">{status.success_count} 成功</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <XCircle className="text-red-400" size={18} />
                            <span className="text-red-400 font-medium">{status.error_count} 失败</span>
                        </div>
                    </div>
                </div>
            )}

            {/* 控制面板 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* 配置区 */}
                <div className="p-4 bg-white/5 rounded-xl border border-white/10">
                    <h3 className="text-white font-medium mb-4">⚙️ 任务配置</h3>

                    <div className="space-y-4">
                        <div>
                            <label className="text-gray-400 text-sm block mb-1">批量数量</label>
                            <input
                                type="number"
                                min={1}
                                max={50}
                                value={batchSize}
                                onChange={(e) => setBatchSize(parseInt(e.target.value) || 5)}
                                className="w-full px-3 py-2 bg-black/30 border border-purple-500/30 rounded-lg text-white focus:outline-none focus:border-purple-400"
                                disabled={status?.state === 'running'}
                            />
                        </div>

                        <div>
                            <label className="text-gray-400 text-sm block mb-1">领域</label>
                            <select
                                value={domain}
                                onChange={(e) => setDomain(e.target.value)}
                                className="w-full px-3 py-2 bg-black/30 border border-purple-500/30 rounded-lg text-white focus:outline-none focus:border-purple-400"
                                disabled={status?.state === 'running'}
                            >
                                <option value="hr">人力资源 (HR)</option>
                                <option value="insurance">保险服务</option>
                            </select>
                        </div>
                    </div>
                </div>

                {/* 控制按钮区 */}
                <div className="p-4 bg-white/5 rounded-xl border border-white/10">
                    <h3 className="text-white font-medium mb-4">🎮 操作控制</h3>

                    <div className="grid grid-cols-2 gap-3">
                        {/* 启动按钮 */}
                        <button
                            onClick={handleStart}
                            disabled={loading || status?.state === 'running'}
                            className={`flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition-all ${status?.state === 'running'
                                ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                                : 'bg-gradient-to-r from-green-500 to-emerald-600 text-white hover:from-green-600 hover:to-emerald-700 shadow-lg shadow-green-500/25'
                                }`}
                        >
                            {loading ? <Loader2 className="animate-spin" size={18} /> : <Play size={18} />}
                            启动挖矿
                        </button>

                        {/* 暂停/恢复按钮 */}
                        {status?.state === 'paused' ? (
                            <button
                                onClick={handleResume}
                                className="flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-yellow-500 to-orange-500 text-white rounded-lg font-medium hover:from-yellow-600 hover:to-orange-600 transition-all shadow-lg shadow-yellow-500/25"
                            >
                                <Play size={18} />
                                继续
                            </button>
                        ) : (
                            <button
                                onClick={handlePause}
                                disabled={status?.state !== 'running'}
                                className={`flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition-all ${status?.state !== 'running'
                                    ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                                    : 'bg-gradient-to-r from-yellow-500 to-orange-500 text-white hover:from-yellow-600 hover:to-orange-600 shadow-lg shadow-yellow-500/25'
                                    }`}
                            >
                                <Pause size={18} />
                                暂停
                            </button>
                        )}

                        {/* 取消按钮 */}
                        <button
                            onClick={handleCancel}
                            disabled={status?.state !== 'running' && status?.state !== 'paused'}
                            className={`col-span-2 flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition-all ${status?.state !== 'running' && status?.state !== 'paused'
                                ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                                : 'bg-gradient-to-r from-red-500 to-rose-600 text-white hover:from-red-600 hover:to-rose-700 shadow-lg shadow-red-500/25'
                                }`}
                        >
                            <Square size={18} />
                            取消任务
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default BatchControlPanel;
