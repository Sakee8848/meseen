import React, { useState, useEffect } from 'react';
import { X, Save, Plus, Settings, Trash2, Edit2, Check, ArrowLeft } from 'lucide-react';

interface TaxonomyCategory {
  name: string;
  services: string[];
}

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialTerm: string;
  onSuccess: () => void;
}

export const KnowledgeCorrectionModal: React.FC<ModalProps> = ({ 
  isOpen, onClose, initialTerm, onSuccess 
}) => {
  const [categories, setCategories] = useState<TaxonomyCategory[]>([]);
  const [selectedCategory, setSelectedCategory] = useState("");
  const [expertTerm, setExpertTerm] = useState(initialTerm);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // 模式控制: false = 注入模式, true = 管理模式
  const [manageMode, setManageMode] = useState(false);
  const [newCategoryName, setNewCategoryName] = useState(""); // 用于新建
  
  // 管理模式下的状态
  const [editingCatName, setEditingCatName] = useState<string | null>(null); // 正在改谁的名字
  const [editInputValue, setEditInputValue] = useState(""); // 改成什么

  // 拉取数据
  const fetchCategories = () => {
    fetch("http://127.0.0.1:8000/api/taxonomy")
      .then(res => res.json())
      .then(data => {
        if (data.taxonomy) {
          setCategories(data.taxonomy);
          // 如果当前选中的分类被删了，重置选中项
          if (selectedCategory && !data.taxonomy.find((c: any) => c.name === selectedCategory)) {
            setSelectedCategory(data.taxonomy[0]?.name || "");
          } else if (!selectedCategory && data.taxonomy.length > 0) {
            setSelectedCategory(data.taxonomy[0].name);
          }
        }
      });
  };

  useEffect(() => {
    if (isOpen) {
      setExpertTerm(initialTerm);
      fetchCategories();
    }
  }, [isOpen, initialTerm]);

  // 提交注入 (Add Service)
  const handleInject = async () => {
    setIsSubmitting(true);
    if (!selectedCategory || !expertTerm) return;

    try {
      const res = await fetch("http://127.0.0.1:8000/api/taxonomy/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ category: selectedCategory, service: expertTerm })
      });
      const result = await res.json();
      if (result.status === "success" || result.status === "skipped") {
        alert(`✅ 成功！已注入知识库！`);
        onSuccess();
        onClose();
      }
    } catch (err) { alert("网络错误"); } 
    finally { setIsSubmitting(false); }
  };

  // 创建新分类
  const handleCreateCategory = async () => {
    if (!newCategoryName.trim()) return;
    // 复用 add 接口，只是 service 留空或者先不加，但我们的后端 add 接口需要 service。
    // 这里我们直接用 rename 接口的逻辑不太对。
    // 变通方法：直接调用 add 接口，把当前 expertTerm 加进去，自动就创建分类了。
    // 所以这里其实是 UI 逻辑：把新名字填进 selectedCategory，然后让用户点“确认入库”
    setSelectedCategory(newCategoryName);
    setNewCategoryName(""); 
    // 这里为了体验，我们不立刻提交后端，而是选中它，让用户继续点下面的大按钮确认。
  };

  // 删除分类
  const handleDeleteCategory = async (name: string) => {
    if (!confirm(`⚠️ 危险操作\n确定要删除分类“${name}”吗？\n该分类下的所有服务都将丢失！`)) return;
    
    try {
      await fetch("http://127.0.0.1:8000/api/taxonomy/category", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ category_name: name })
      });
      fetchCategories(); // 刷新列表
    } catch (e) { alert("删除失败"); }
  };

  // 重命名分类
  const handleRenameCategory = async (oldName: string) => {
    if (!editInputValue.trim() || editInputValue === oldName) {
      setEditingCatName(null);
      return;
    }
    try {
      const res = await fetch("http://127.0.0.1:8000/api/taxonomy/category", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ old_name: oldName, new_name: editInputValue })
      });
      const data = await res.json();
      if (data.status === "error") alert(data.message);
      else fetchCategories();
    } catch (e) { alert("重命名失败"); }
    finally { setEditingCatName(null); }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden border border-gray-100 flex flex-col max-h-[85vh]">
        
        {/* Header */}
        <div className="bg-blue-600 px-6 py-4 flex justify-between items-center flex-shrink-0">
          <div className="flex items-center gap-2 text-white">
            {manageMode && (
              <button onClick={() => setManageMode(false)} className="hover:bg-blue-700 p-1 rounded-full mr-1 transition-colors">
                <ArrowLeft size={18} />
              </button>
            )}
            <h3 className="font-bold text-lg">
              {manageMode ? "⚙️ 分类管理 (Category Mgr)" : "🧠 知识注入 (Injection)"}
            </h3>
          </div>
          <button onClick={onClose} className="text-white/80 hover:text-white transition-colors">
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-6 overflow-y-auto flex-1">
          
          {/* =========== 模式 A: 管理模式 (CRUD) =========== */}
          {manageMode ? (
            <div className="space-y-3">
              <p className="text-sm text-gray-500 mb-2">在此管理知识图谱的分类架构。</p>
              {categories.map(cat => (
                <div key={cat.name} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200 group hover:border-blue-300 transition-all">
                  
                  {/* 编辑状态 vs 展示状态 */}
                  {editingCatName === cat.name ? (
                    <div className="flex flex-1 gap-2">
                      <input 
                        className="flex-1 px-2 py-1 text-sm border rounded"
                        value={editInputValue}
                        autoFocus
                        onChange={e => setEditInputValue(e.target.value)}
                      />
                      <button onClick={() => handleRenameCategory(cat.name)} className="text-green-600 p-1"><Check size={16}/></button>
                      <button onClick={() => setEditingCatName(null)} className="text-gray-400 p-1"><X size={16}/></button>
                    </div>
                  ) : (
                    <>
                      <div className="flex-1 font-medium text-gray-700 truncate mr-2" title={cat.name}>
                        {cat.name} <span className="text-xs text-gray-400 font-normal">({cat.services.length})</span>
                      </div>
                      <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button 
                          onClick={() => { setEditingCatName(cat.name); setEditInputValue(cat.name); }}
                          className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded"
                          title="重命名"
                        >
                          <Edit2 size={14} />
                        </button>
                        <button 
                          onClick={() => handleDeleteCategory(cat.name)}
                          className="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded"
                          title="删除"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </>
                  )}
                </div>
              ))}
            </div>
          ) : (
            /* =========== 模式 B: 注入模式 (Default) =========== */
            <>
              {/* Input 1: 专家术语 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  标准化专家术语 (Expert Term)
                </label>
                <input 
                  type="text" 
                  value={expertTerm}
                  onChange={(e) => setExpertTerm(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>

              {/* Input 2: 归属大类 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1 flex justify-between">
                  <span>归属服务大类 (Category)</span>
                  <button 
                    onClick={() => setManageMode(true)}
                    className="text-xs text-blue-600 hover:underline flex items-center gap-1"
                  >
                    <Settings size={12} /> 管理分类
                  </button>
                </label>
                
                <div className="flex gap-2 items-center w-full">
                  <div className="flex-1 min-w-0">
                    <select 
                      value={selectedCategory}
                      onChange={(e) => setSelectedCategory(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-blue-500 outline-none truncate"
                    >
                      {categories.map((cat) => (
                        <option key={cat.name} value={cat.name}>{cat.name}</option>
                      ))}
                      {/* 如果列表为空，或者用户想新建 */}
                      <option value="__NEW__">+ 新建分类...</option>
                    </select>
                  </div>
                </div>

                {/* 如果选中了“新建分类”，显示输入框 */}
                {selectedCategory === "__NEW__" && (
                   <div className="mt-2 flex gap-2 animate-in fade-in slide-in-from-top-2">
                     <input 
                       placeholder="输入新分类名称..."
                       className="flex-1 px-3 py-2 border border-blue-300 bg-blue-50 rounded-lg text-sm outline-none"
                       value={newCategoryName}
                       onChange={e => setNewCategoryName(e.target.value)}
                     />
                     <button 
                        onClick={() => {
                           if(newCategoryName) {
                             setSelectedCategory(newCategoryName); 
                             // 这里我们只是在UI上把它变成了选中状态，真正创建是在提交时
                             // 为了兼容select逻辑，我们可能需要临时把新名字加到 categories 列表里，
                             // 或者简单处理：一旦有 newCategoryName，就视为新分类
                           }
                        }}
                        className="px-3 py-1 bg-blue-600 text-white text-xs rounded-lg"
                     >
                       确定
                     </button>
                   </div>
                )}
              </div>
            </>
          )}

        </div>

        {/* Footer */}
        {!manageMode && (
          <div className="bg-gray-50 px-6 py-4 flex justify-end gap-3 border-t flex-shrink-0">
            <button onClick={onClose} className="px-4 py-2 text-gray-600 hover:bg-gray-200 rounded-lg">取消</button>
            <button 
              onClick={handleInject}
              disabled={isSubmitting}
              className="px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 shadow-sm flex items-center gap-2"
            >
              {isSubmitting ? "正在注入..." : <><Save size={18} /> 确认入库</>}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};