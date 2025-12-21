import React, { useState } from 'react';
import { streamCouncil } from '../api';
import NodeTree from './NodeTree';
import { Send, Zap } from 'lucide-react';

const MODELS = [
  // Future/Requested
  { id: "openai/gpt-5.2", name: "GPT-5.2", desc: "OpenAI Flagship" },
  { id: "anthropic/claude-4.5-opus", name: "Claude 4.5 Opus", desc: "Anthropic Flagship" },
  { id: "google/gemini-3-pro-preview", name: "Gemini 3 Pro", desc: "Google Flagship" },
  // Real/Prior
  { id: "openai/gpt-4o", name: "GPT-4o", desc: "Prior Flagship" },
  { id: "anthropic/claude-3-opus", name: "Claude 3 Opus", desc: "Prior Flagship" },
  { id: "google/gemini-2.5-flash", name: "Gemini 2.5 Flash", desc: "Prior Flagship" },
  // Others
  { id: "meta-llama/llama-3-70b-instruct", name: "Llama 3 70B", desc: "Meta Flagship" },
  { id: "deepseek/deepseek-v3.2", name: "DeepSeek v3.2", desc: "Deepseek Flagship" },
  { id: "x-ai/grok-4", name: "Grok 4", desc: "xAI Flagship" },
  { id: "openai/gpt-3.5-turbo", name: "GPT-3.5 Turbo", desc: "Fast & Efficient" },
  { id: "anthropic/claude-3-haiku", name: "Claude 3 Haiku", desc: "Speed Optimized" },
];

const Council = () => {
  const [prompt, setPrompt] = useState('');
  const [selectedModels, setSelectedModels] = useState(['openai/gpt-4o', 'anthropic/claude-3-opus']);
  const [chairman, setChairman] = useState('openai/gpt-4o');
  const [method, setMethod] = useState('dag'); // dag or ensemble
  const [isResearching, setIsResearching] = useState(false);
  const [nodes, setNodes] = useState([]);
  const [status, setStatus] = useState('');

  const toggleModel = (id) => {
    setSelectedModels(prev =>
      prev.includes(id) ? prev.filter(m => m !== id) : [...prev, id]
    );
  };

  const handleStart = () => {
    if (!prompt) return;
    setIsResearching(true);
    setNodes([]);
    setStatus('Initializing...');

    // Add User Node locally for visuals (though backend does it too)
    // setNodes([{ type: 'root', content: prompt, id: 'root' }]);

    streamCouncil(prompt, selectedModels, chairman, method, (event) => {
      if (event.type === 'status') {
        setStatus(event.message);
      } else if (event.type === 'node') {
        setNodes(prev => [...prev, event.node]);
      } else if (event.type === 'done') {
        setStatus('done');
        setIsResearching(false);
      } else if (event.type === 'error') {
        setStatus('Error: ' + event.message);
        setIsResearching(false);
      }
    });
  };

  return (
    <div className="max-w-5xl mx-auto">
      {/* Input Section */}
      {!isResearching && nodes.length === 0 ? (
        <div className="space-y-8 animate-fade-in">
          <div>
            <h2 className="text-2xl font-bold mb-4">Research Prompt</h2>
            <div className="relative mb-4">
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Enter your research question or topic..."
                className="w-full h-32 bg-slate-800 border border-slate-700 rounded-lg p-4 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none resize-none"
              />
              <div className="absolute bottom-4 right-4 flex space-x-2">
                <button className="text-xs bg-slate-700 hover:bg-slate-600 px-2 py-1 rounded text-slate-300">Web Frameworks</button>
                <button className="text-xs bg-slate-700 hover:bg-slate-600 px-2 py-1 rounded text-slate-300">API Security</button>
              </div>
            </div>

            {/* Method Selection */}
            <div className="flex space-x-6">
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="radio"
                  name="method"
                  value="dag"
                  checked={method === 'dag'}
                  onChange={() => setMethod('dag')}
                  className="form-radio text-blue-600 bg-slate-800 border-slate-700 focus:ring-blue-500"
                />
                <span>AI Council (DAG)</span>
              </label>
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="radio"
                  name="method"
                  value="ensemble"
                  checked={method === 'ensemble'}
                  onChange={() => setMethod('ensemble')}
                  className="form-radio text-blue-600 bg-slate-800 border-slate-700 focus:ring-blue-500"
                />
                <span>Ensemble</span>
              </label>
            </div>
          </div>

          <div>
            <div className="flex justify-between items-end mb-4">
              <h2 className="text-xl font-bold">Council Members</h2>
              <span className="text-sm text-slate-400">Select 2+ models for best results</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {MODELS.map(model => (
                <div
                  key={model.id}
                  onClick={() => toggleModel(model.id)}
                  className={`cursor-pointer p-4 rounded-lg border flex items-start space-x-3 transition ${selectedModels.includes(model.id)
                      ? 'bg-blue-900/20 border-blue-500'
                      : 'bg-slate-900 border-slate-800 hover:border-slate-700'
                    }`}
                >
                  <div className={`w-5 h-5 rounded border flex items-center justify-center mt-1 ${selectedModels.includes(model.id) ? 'bg-blue-600 border-blue-600' : 'border-slate-600'
                    }`}>
                    {selectedModels.includes(model.id) && <Zap size={12} className="text-white" />}
                  </div>
                  <div>
                    <div className="font-semibold text-sm">{model.name}</div>
                    <div className="text-xs text-slate-500">{model.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div>
            <h2 className="text-xl font-bold mb-4">Chairman Model</h2>
            <select
              value={chairman}
              onChange={(e) => setChairman(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-lg p-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {MODELS.map(model => (
                <option key={model.id} value={model.id}>{model.name} ({model.desc})</option>
              ))}
            </select>
          </div>

          <button
            onClick={handleStart}
            disabled={!prompt || selectedModels.length === 0}
            className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-bold py-4 rounded-lg shadow-lg transform transition active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Start Research
          </button>
        </div>
      ) : (
        <div className="animate-fade-in">
          <div className="mb-6 flex items-center justify-between">
            <h2 className="text-2xl font-bold text-slate-200">{prompt}</h2>
            <button onClick={() => { setIsResearching(false); setNodes([]); }} className="text-sm text-slate-500 hover:text-white">New Research</button>
          </div>

          <NodeTree nodes={nodes} status={status} />
        </div>
      )}
    </div>
  );
};

export default Council;
