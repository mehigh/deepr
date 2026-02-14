import React, { useState } from 'react';
import { streamCouncil, uploadFiles } from '../api';
import NodeTree from './NodeTree';
import { Trash2, Plus, X, Paperclip } from 'lucide-react';
import AttachmentList from './AttachmentList';
import { useModels } from '../hooks';
import { ModelSelect } from './ModelSelector';



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
  const { models, loading, error } = useModels();
  const [prompt, setPrompt] = useState('');
  const [roles, setRoles] = useState(DEFAULT_ROLES);
  const [isRunning, setIsRunning] = useState(false);
  const [nodes, setNodes] = useState([]);
  const [status, setStatus] = useState('');
  const [maxIterations, setMaxIterations] = useState(3);
  const [attachments, setAttachments] = useState([]);
  const [uploading, setUploading] = useState(false);


  const [submittedAttachments, setSubmittedAttachments] = useState([]);

  const defaultRoles = () => {
    return [
      {
        id: 1,
        name: "Lead Researcher",
        model: models.find(m => m.id === "anthropic/claude-opus-4.5") ? "anthropic/claude-opus-4.5" : models[0].id,
        perspective: "Primary analysis and synthesis",
        instructions: "Conduct thorough research analysis, identify key findings and patterns."
      },
      {
        id: 2,
        name: "Critical Reviewer",
        model: models.find(m => m.id === "openai/gpt-5.2") ? "openai/gpt-5.2" : models[0].id,
        perspective: "Identify gaps and weaknesses",
        instructions: "Critically evaluate the research, identify methodological issues and limitations.",
        locked: true
      },
      {
        id: 3,
        name: "Domain Expert",
        model: models.find(m => m.id === "google/gemini-3-pro-preview") ? "google/gemini-3-pro-preview" : models[0].id,
        perspective: "Deep domain knowledge",
        instructions: "Provide specialized expertise and context from the relevant field."
      }
    ]
  };

  const addRole = () => {
    setRoles([...roles, {
      id: Date.now(),
      name: "New Role",
      model: models.find(m => m.id === "openai/gpt-4o") ? "openai/gpt-4o" : models[0].id,
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

  const handleFileSelect = async (e) => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;

    setUploading(true);
    try {
      const uploadedFiles = await uploadFiles(files);
      setAttachments(prev => [...prev, ...uploadedFiles]);
    } catch (error) {
      console.error("Upload failed:", error);
      setStatus('Error uploading files: ' + error.message);
    } finally {
      setUploading(false);
      // Reset input
      e.target.value = '';
    }
  };

  const removeAttachment = (id) => {
    setAttachments(prev => prev.filter(a => a.id !== id));
  };

  const handleStart = () => {
    if (!prompt) return;
    setIsRunning(true);
    setNodes([]);
    setStatus('Initializing DxO Panel...');
    setSubmittedAttachments([]);

    // Pass the roles config to the backend
    const rolesPayload = roles.map(r => ({
      name: r.name,
      model: r.model,
      instructions: r.instructions
    }));

    // Use the first role (Lead Researcher) as the primary/chairman model
    const leadModel = roles.length > 0 ? roles[0].model : "openai/gpt-4o";

    const attachmentIds = attachments.map(a => a.id);

    streamCouncil(prompt, [], leadModel, 'dxo', (event) => {
      if (event.type === 'status') {
        setStatus(event.message);
      } else if (event.type === 'node') {
        setNodes(prev => [...prev, event.node]);

        // If this is the root node, extract its attachments to confirm they are saved
        if (event.node.type === 'root' && event.node.attachments) {
          setSubmittedAttachments(event.node.attachments);
        }
      } else if (event.type === 'done') {
        setStatus('done');
        setIsRunning(false);
      } else if (event.type === 'error') {
        setStatus('Error: ' + event.message);
        setIsRunning(false);
      }
    }, rolesPayload, maxIterations, attachmentIds);
  };

  return (
    <div className="max-w-6xl mx-auto">
      {!isRunning && nodes.length === 0 ? (
        <div className="animate-fade-in space-y-8">
          {error && error.isMissingKey && (
            <div className="max-w-4xl mx-auto mt-0 mb-8 p-6 bg-slate-900 border border-slate-700 rounded-lg text-center">
              <div className="text-yellow-500 text-3xl mb-2">⚠️</div>
              <h2 className="text-xl font-bold text-white mb-2">OpenRouter API Key Required</h2>
              <p className="text-slate-400 mb-4">
                DxO requires an OpenRouter API Key to function.
              </p>
              <a
                href="/settings"
                className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg transition"
              >
                Configure API Key
              </a>
            </div>
          )}

          {error && !error.isMissingKey && (
            <div className="p-4 mb-6 text-center text-red-400 bg-red-900/20 border border-red-900 rounded-lg">
              Error loading models: {error.message}
            </div>
          )}

          <div>
            <h2 className="text-2xl font-bold mb-4">DxO Request</h2>
            <div className="relative mb-4">
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Describe the problem or system you want the DxO panel to analyze..."
                className="w-full h-32 bg-slate-800 border border-slate-700 rounded-lg p-4 pb-12 text-white focus:ring-2 focus:ring-purple-500 focus:outline-none resize-none"
              />
              <div className="absolute bottom-4 left-4">
                <input
                  type="file"
                  id="dxo-file-upload"
                  multiple
                  onChange={handleFileSelect}
                  className="hidden"
                  disabled={uploading}
                />
                <label
                  htmlFor="dxo-file-upload"
                  className={`cursor-pointer flex items-center p-2 bg-slate-700 hover:bg-slate-600 rounded-full text-slate-300 hover:text-white transition-colors ${uploading ? 'opacity-50 cursor-not-allowed' : ''}`}
                  title="Attach files"
                >
                  <Paperclip size={18} />
                  {uploading && <span className="ml-2 text-xs">Uploading...</span>}
                </label>
              </div>
            </div>

            <AttachmentList
              attachments={attachments}
              onRemove={removeAttachment}
              uploading={uploading}
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
                      <ModelSelect
                        models={models}
                        value={role.model}
                        onChange={(val) => updateRole(role.id, 'model', val)}
                        className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-sm focus:border-purple-500 focus:outline-none appearance-none"
                      />
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
            disabled={!prompt || error}
            className="w-full bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-bold py-4 rounded-lg shadow-lg transform transition active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Start Diagnostic Orchestration
          </button>
        </div>
      ) : (
        <div className="animate-fade-in">
          <div className="mb-6 flex items-center justify-between">
            <h2 className="text-2xl font-bold text-slate-200">{prompt}</h2>
            <button onClick={() => {
              setIsRunning(false);
              setNodes([]);
              setSubmittedAttachments([]);
              setAttachments([]);
              setPrompt('');
            }} className="text-sm text-slate-500 hover:text-white">New Session</button>
          </div>

          <div className="mb-6">
            <AttachmentList attachments={submittedAttachments} />
          </div>

          <NodeTree nodes={nodes} status={status} />
        </div>
      )}
    </div>
  );
};

export default DxO;
