"use client"

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Check, X, ArrowRight, Save, AlertCircle, Loader2, RefreshCcw, Target } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { toast } from "sonner"

interface NodeData {
  id: string
  context: string
  question: string
  ai_rationale: string
  confidence: number
  next_nodes: string[]
}

export default function ExpertWorkbench() {
  const [queue, setQueue] = useState<NodeData[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [direction, setDirection] = useState<'left' | 'right' | null>(null)

  // 编辑相关状态
  const [isEditing, setIsEditing] = useState(false)
  const [editValue, setEditValue] = useState("")

  // 任务相关状态
  const [taskContext, setTaskContext] = useState("通用保险咨询")
  const [isUpdatingTask, setIsUpdatingTask] = useState(false)

  const [isLoading, setIsLoading] = useState(true)

  // 1. 设置任务目标
  const updateTask = async () => {
    if (!taskContext.trim()) return
    setIsUpdatingTask(true)
    try {
      await fetch('http://127.0.0.1:8000/api/set_task', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ context: taskContext })
      })
      toast.success("任务目标已锁定", { description: `AI 将专注于：${taskContext}` })
      fetchQueue()
    } catch (e) {
      toast.error("任务设置失败")
    } finally {
      setIsUpdatingTask(false)
    }
  }

  // 2. 获取题目
  const fetchQueue = async () => {
    setIsLoading(true)
    try {
      const res = await fetch('http://127.0.0.1:8000/api/queue')
      if (!res.ok) throw new Error('API连接失败')
      const data = await res.json()
      setQueue(data)
      setCurrentIndex(0)
    } catch (error) {
      toast.error("连接失败", { description: "请检查后端是否运行" })
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => { fetchQueue() }, [])

  const currentCard = queue[currentIndex]

  // --- 键盘监听逻辑 ---
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // 如果当前焦点在输入框或文本域中，不触发快捷键
      const target = e.target as HTMLElement
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
        // 允许在任务输入框按回车直接锁定
        if (e.key === 'Enter' && target.tagName === 'INPUT') {
          updateTask()
        }
        return
      }

      if (!currentCard) return

      if (e.key === 'ArrowRight') handleSwipe('right')
      if (e.key === 'ArrowLeft') handleSwipe('left')
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [currentIndex, isEditing, currentCard, taskContext])

  // --- 核心逻辑升级：智能判断接口 ---
  const handleSwipe = async (dir: 'left' | 'right') => {
    // 1. 如果是左滑，且还没进入编辑模式，则进入编辑模式
    if (dir === 'left' && !isEditing) {
      setIsEditing(true)
      setEditValue(currentCard.question)
      return
    }

    setDirection(dir)

    // 2. 构造最终数据
    const finalData = {
      ...currentCard,
      question: isEditing ? editValue : currentCard.question
    }

    // 3. 决定发送给哪个接口
    let endpoint = ''
    if (dir === 'right') {
      // 右滑确认 -> 批准
      endpoint = `http://127.0.0.1:8000/api/approve/${currentCard.id}`
    } else if (isEditing) {
      // 编辑模式下点击保存 -> 修正 (这是最重要的修复！)
      endpoint = `http://127.0.0.1:8000/api/correct/${currentCard.id}`
    } else {
      // 其他情况（虽然目前 UI 逻辑只要左滑就进编辑，但保留此分支做兜底） -> 驳回
      endpoint = `http://127.0.0.1:8000/api/reject/${currentCard.id}`
    }

    try {
      fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(finalData)
      })
    } catch (e) { console.error(e) }

    setTimeout(() => {
      // 4. 根据不同操作显示不同提示
      if (dir === 'right') {
        toast.success("已存档 💾", { description: "知识点已写入" })
      } else if (isEditing) {
        toast.success("修正已录入 💎", { description: "AI 已将您的修改视为黄金法则！" })
      } else {
        toast.info("已驳回 🗑️", { description: "负面样本已记录" })
      }

      if (currentIndex < queue.length) {
        setDirection(null)
        setIsEditing(false)
        setCurrentIndex(prev => prev + 1)
      }
    }, 200)
  }

  // --- UI 组件提取 ---
  const renderTaskBar = () => (
    <div className="bg-slate-900 p-4 text-white shadow-lg z-20">
      <div className="max-w-lg mx-auto flex items-center gap-2">
        <Target className="w-5 h-5 text-blue-400 shrink-0" />
        <span className="text-sm font-bold whitespace-nowrap hidden sm:inline">当前任务:</span>
        <Input
          className="bg-slate-800 border-slate-700 text-white h-9 focus-visible:ring-blue-500"
          value={taskContext}
          onChange={(e) => setTaskContext(e.target.value)}
          placeholder="输入领域，例如：人力资源咨询"
        />
        <Button
          size="sm"
          variant="secondary"
          onClick={updateTask}
          disabled={isUpdatingTask}
          className="shrink-0"
        >
          {isUpdatingTask ? <Loader2 className="w-4 h-4 animate-spin" /> : "锁定"}
        </Button>
      </div>
    </div>
  )

  if (isLoading) {
    return (
      <div className="flex h-screen flex-col bg-slate-50">
        {renderTaskBar()}
        <div className="flex-1 flex items-center justify-center flex-col gap-4">
          <Loader2 className="h-10 w-10 animate-spin text-slate-400" />
          <p className="text-slate-500 text-sm">GLM-4 正在针对【{taskContext}】构建策略...</p>
        </div>
      </div>
    )
  }

  if (!currentCard) {
    return (
      <div className="flex flex-col h-screen bg-slate-50">
        {renderTaskBar()}
        <div className="flex-1 flex flex-col items-center justify-center p-6 text-center space-y-6">
          <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} className="w-24 h-24 bg-green-100 rounded-full flex items-center justify-center">
            <Check className="w-12 h-12 text-green-600" />
          </motion.div>
          <div>
            <h2 className="text-3xl font-bold text-slate-800">本轮训练完成</h2>
            <p className="text-slate-500 mt-2">已成功提取关于【{taskContext}】的隐性知识。</p>
          </div>
          <Button onClick={fetchQueue} size="lg" className="w-full max-w-xs gap-2">
            <RefreshCcw className="w-4 h-4" /> 继续训练此领域
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-screen max-w-lg mx-auto bg-white border-x shadow-2xl overflow-hidden font-sans">
      {renderTaskBar()}

      <div className="p-4 bg-white z-10 flex justify-between items-center border-b">
        <span className="font-bold text-slate-800">训练进度</span>
        <Badge variant="outline">{currentIndex + 1} / {queue.length}</Badge>
      </div>

      <div className="flex-1 relative flex items-center justify-center p-4 bg-slate-50/50">
        <AnimatePresence>
          <motion.div
            key={currentCard.id}
            initial={{ scale: 0.95, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, x: 0, rotate: 0, y: 0 }}
            exit={{ x: direction === 'right' ? 500 : -500, opacity: 0 }}
            transition={{ type: "spring", stiffness: 300, damping: 20 }}
            className="w-full absolute inset-x-4 max-w-[calc(100%-2rem)] mx-auto"
            style={{ top: '5%' }}
          >
            <Card className="h-[60vh] flex flex-col shadow-xl border-slate-200">
              <CardHeader className="border-b bg-white pb-4">
                <div className="flex justify-between items-start mb-3">
                  <Badge className="bg-blue-50 text-blue-700 hover:bg-blue-100 border-blue-200">
                    {currentCard.context}
                  </Badge>
                  <div className="flex items-center text-xs font-medium text-slate-400">
                    <AlertCircle className="w-3 h-3 mr-1" /> 置信度: {Math.floor(currentCard.confidence * 100)}%
                  </div>
                </div>
                <CardTitle className="text-xl leading-snug text-slate-800">
                  {isEditing ? "请修正 AI 的提问：" : `AI 建议提问：\n"${currentCard.question}"`}
                </CardTitle>
              </CardHeader>

              <CardContent className="flex-1 overflow-y-auto pt-6 space-y-5 bg-white">
                {isEditing ? (
                  <Textarea
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    className="h-40 text-lg border-blue-200 focus:border-blue-500 bg-blue-50/20 p-4 resize-none"
                    autoFocus
                  />
                ) : (
                  <>
                    <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                      <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">AI 逻辑解释</p>
                      <p className="text-sm text-slate-600 leading-relaxed">{currentCard.ai_rationale}</p>
                    </div>
                    <div className="space-y-2">
                      {currentCard.next_nodes.map((node, idx) => (
                        <div key={idx} className="flex items-center text-sm text-slate-700 bg-slate-50 border p-3 rounded-lg">
                          <ArrowRight className="w-4 h-4 mr-2 text-slate-400" /> {node}
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </AnimatePresence>
      </div>

      <div className="p-4 bg-white border-t z-10 grid grid-cols-2 gap-4 pb-8">
        {isEditing ? (
          <>
            <Button variant="outline" onClick={() => setIsEditing(false)}>取消</Button>
            <Button className="bg-blue-600 hover:bg-blue-700" onClick={() => handleSwipe('left')}>
              <Save className="w-4 h-4 mr-2" /> 保存修正
            </Button>
          </>
        ) : (
          <>
            <Button variant="outline" className="h-14 border-red-100 text-red-600" onClick={() => handleSwipe('left')}>
              <X className="w-5 h-5 mr-2" /> 修改 (←)
            </Button>
            <Button className="h-14 bg-slate-900" onClick={() => handleSwipe('right')}>
              <Check className="w-5 h-5 mr-2" /> 确认 (→)
            </Button>
          </>
        )}
      </div>
    </div>
  )
}