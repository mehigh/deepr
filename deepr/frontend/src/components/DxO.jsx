import React, { useState } from 'react';
import { streamCouncil } from '../api';
import NodeTree from './NodeTree';
import { Trash2, Plus, X } from 'lucide-react';

const MODELS = [
  { id: "openai/gpt-5.2", name: "GPT-5.2", desc: "OpenAI Flagship" },
  { id: "anthropic/claude-opus-4.5", name: "Claude 4.5 Opus", desc: "Anthropic Flagship" },
  { id: "google/gemini-3-pro-preview", name: "Gemini 3 Pro", desc: "Google Flagship" },
  { id: "openai/gpt-4o", name: "GPT-4o", desc: "Prior Flagship" },
  { id: "anthropic/claude-3-opus", name: "Claude 3 Opus", desc: "Prior Flagship" },
  { id: "google/gemini-1.5-pro", name: "Gemini 1.5 Pro", desc: "Prior Flagship" },
  { id: "meta-llama/llama-3-70b-instruct", name: "Llama 3 70B", desc: "Meta Flagship" },
];

const DEFAULT_ROLES = [
  {
    id: 1,
    name: "Lead Researcher",
    model: "anthropic/claude-opus-4.5",
    perspective: "Primary analysis and synthesis",
    instructions: "Conduct thorough research analysis, identify key findings and patterns."
  },
  {
    id: 2,
    name: "Critical Reviewer",
    model: "openai/gpt-5.2",
    perspective: "Identify gaps and weaknesses",
    instructions: "Critically evaluate the research, identify methodological issues and limitations.",
    locked: true
  },
  {
    id: 3,
    name: "Domain Expert",
    model: "google/gemini-3-pro-preview",
    perspective: "Deep domain knowledge",
    instructions: "Provide specialized expertise and context from the relevant field."
  }
];

const DxO = () => {
  const [prompt, setPrompt] = useState('');
  const [roles, setRoles] = useState(DEFAULT_ROLES);
  const [isRunning, setIsRunning] = useState(false);
  const [nodes, setNodes] = useState([]);
  const [status, setStatus] = useState('');
  const [maxIterations, setMaxIterations] = useState(3);

  const addRole = () => {
    setRoles([...roles, {
      id: Date.now(),
      name: "New Role",
      model: "openai/gpt-4o",
      perspective: "Specialized perspective",
      instructions: ""
    }]);
  };

  const updateRole = (id, field, value) => {
    setRoles(roles.map(r => r.id === id ? { ...r, [field]: value } : r));
  };

  const removeRole = (id) => {
    setRoles(roles.filter(r => r.id !== id));
  };

  const handleStart = () => {
    if (!prompt) return;
    setIsRunning(true);
    setNodes([]);
    setStatus('Initializing DxO Panel...');

    // Pass the roles config to the backend
    const rolesPayload = roles.map(r => ({
      name: r.name,
      model: r.model,
      instructions: r.instructions
    }));

    // Use the first role (Lead Researcher) as the primary/chairman model
    const leadModel = roles.length > 0 ? roles[0].model : "openai/gpt-4o";

    streamCouncil(prompt, [], leadModel, 'dxo', (event) => {
      if (event.type === 'status') {
        setStatus(event.message);
      } else if (event.type === 'node') {
        setNodes(prev => [...prev, event.node]);
      } else if (event.type === 'done') {
        setStatus('done');
        setIsRunning(false);
      } else if (event.type === 'error') {
        setStatus('Error: ' + event.message);
        setIsRunning(false);
      }
    }, rolesPayload, maxIterations);
  };

  return (
    <div className="max-w-6xl mx-auto">
      {!isRunning && nodes.length === 0 ? (
        <div className="animate-fade-in space-y-8">
          <div>
            <h2 className="text-2xl font-bold mb-4">DxO Request</h2>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Describe the problem or system you want the DxO panel to analyze..."
              className="w-full h-32 bg-slate-800 border border-slate-700 rounded-lg p-4 text-white focus:ring-2 focus:ring-purple-500 focus:outline-none resize-none"
            />
          </div>

          <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h3 className="text-xl font-bold">Role Assignments</h3>
                <p className="text-slate-400 text-sm">Assign AI models to specialized roles. Each role brings a unique perspective.</p>
              </div>
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2 bg-slate-800 rounded-lg px-3 py-1 border border-slate-700">
                  <span className="text-xs text-slate-400">Max Iterations:</span>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={maxIterations}
                    onChange={(e) => setMaxIterations(parseInt(e.target.value))}
                    className="w-12 bg-transparent text-sm text-center focus:outline-none text-white appearance-none"
                  />
                </div>
                <button
                  onClick={addRole}
                  className="flex items-center px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg border border-slate-700 text-sm transition"
                >
                  <Plus size={16} className="mr-2" /> Add Role
                </button>
              </div>
            </div>

            <div className="space-y-4">
              {roles.map((role) => (
                <div key={role.id} className="bg-slate-950/50 border border-slate-800 rounded-lg p-4">
                  <div className="grid grid-cols-12 gap-4 mb-4">
                    <div className="col-span-3">
                      <label className="block text-xs text-slate-500 mb-1">Role Name</label>
                      <input
                        type="text"
                        value={role.name}
                        disabled={role.locked}
                        onChange={(e) => updateRole(role.id, 'name', e.target.value)}
                        className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-sm focus:border-purple-500 focus:outline-none"
                      />
                    </div>
                    <div className="col-span-4">
                      <label className="block text-xs text-slate-500 mb-1">Assigned Model</label>
                      <select
                        value={role.model}
                        onChange={(e) => updateRole(role.id, 'model', e.target.value)}
                        className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-sm focus:border-purple-500 focus:outline-none appearance-none"
                      >
                        {MODELS.map(m => (
                          <option key={m.id} value={m.id}>{m.name}</option>
                        ))}
                      </select>
                    </div>
                    <div className="col-span-4">
                      <label className="block text-xs text-slate-500 mb-1">Perspective/Focus</label>
                      <input
                        type="text"
                        value={role.perspective}
                        onChange={(e) => updateRole(role.id, 'perspective', e.target.value)}
                        className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-sm focus:border-purple-500 focus:outline-none"
                      />
                    </div>
                    <div className="col-span-1 flex items-end justify-end pb-2">
                      {!role.locked && (
                        <button onClick={() => removeRole(role.id)} className="text-slate-500 hover:text-red-400">
                          <X size={18} />
                        </button>
                      )}
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs text-slate-500 mb-1">Role Instructions (Optional)</label>
                    <textarea
                      value={role.instructions}
                      onChange={(e) => updateRole(role.id, 'instructions', e.target.value)}
                      className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-sm focus:border-purple-500 focus:outline-none resize-none h-16"
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <button
            onClick={handleStart}
            disabled={!prompt}
            className="w-full bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-bold py-4 rounded-lg shadow-lg transform transition active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Start Diagnostic Orchestration
          </button>
        </div>
      ) : (
        <div className="animate-fade-in">
          <div className="mb-6 flex items-center justify-between">
            <h2 className="text-2xl font-bold text-slate-200">{prompt}</h2>
            <button onClick={() => { setIsRunning(false); setNodes([]); }} className="text-sm text-slate-500 hover:text-white">New Session</button>
          </div>

          <NodeTree nodes={nodes} status={status} />
        </div>
      )}
    </div>
  );
};

export default DxO;
