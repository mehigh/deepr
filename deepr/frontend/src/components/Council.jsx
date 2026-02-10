import React, { useState } from 'react';
import { streamCouncil, uploadFiles } from '../api';
import NodeTree from './NodeTree';
import AttachmentList from './AttachmentList';
import { ModelGrid, ModelSelect } from './ModelSelector';
import { useModels } from '../hooks';
import { Paperclip, X, MessageSquare } from 'lucide-react';
import { API_URL } from '../config';
import ReactMarkdown from 'react-markdown';

const Council = () => {
  const [prompt, setPrompt] = useState('');
  const [selectedModels, setSelectedModels] = useState(['openai/gpt-4o', 'google/gemini-2.5-flash']);
  const [chairman, setChairman] = useState('openai/gpt-4o');
  const [method, setMethod] = useState('dag'); // dag or ensemble
  const [isResearching, setIsResearching] = useState(false);
  const [nodes, setNodes] = useState([]);
  const [status, setStatus] = useState('');
  const [attachments, setAttachments] = useState([]);
  const [submittedAttachments, setSubmittedAttachments] = useState([]); // Attachments after submission
  const [uploading, setUploading] = useState(false);


  const { models, loading, error } = useModels();

  const toggleModel = (id) => {
    setSelectedModels(prev =>
      prev.includes(id) ? prev.filter(m => m !== id) : [...prev, id]
    );
  };

  const handleFileSelect = async (e) => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;

    setUploading(true);
    try {
      const uploaded = await uploadFiles(files);
      setAttachments(prev => [...prev, ...uploaded]);
    } catch (error) {
      console.error('Upload failed:', error);
      setStatus('Error uploading files: ' + error.message);
    } finally {
      setUploading(false);
      // Reset input value to allow selecting same file again
      e.target.value = '';
    }
  };

  const removeAttachment = (id) => {
    setAttachments(prev => prev.filter(a => a.id !== id));
  };

  const handleStart = async () => {
    if (!prompt) return;
    setIsResearching(true);
    setNodes([]);
    setStatus('Initializing...');
    setSubmittedAttachments([]);

    // Extract attachment IDs

    // Extract attachment IDs
    const attachmentIds = attachments.map(att => att.id);

    streamCouncil(prompt, selectedModels, chairman, method, async (event) => {
      if (event.type === 'status') {
        setStatus(event.message);
      } else if (event.type === 'node') {
        setNodes(prev => [...prev, event.node]);

        // If this is the root node, extract its attachments
        if (event.node.type === 'root' && event.node.attachments) {
          setSubmittedAttachments(event.node.attachments);
        }
      } else if (event.type === 'done') {
        setStatus('done');
        setIsResearching(false);
      } else if (event.type === 'error') {
        setStatus('Error: ' + event.message);
        setIsResearching(false);
      }
    }, [], 3, attachmentIds);
  };

  if (loading) return <div className="p-8 text-center text-slate-400">Loading models...</div>;

  if (error) {
    if (error.isMissingKey) {
      return (
        <div className="max-w-4xl mx-auto mt-10 p-8 bg-slate-900 border border-slate-700 rounded-lg text-center animate-fade-in">
          <div className="text-yellow-500 text-5xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-white mb-2">OpenRouter API Key Required</h2>
          <p className="text-slate-400 mb-6">
            To use the Council, you need to configure your OpenRouter API Key.
          </p>
          <a
            href="/settings"
            className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg transition"
          >
            Configure API Key
          </a>
        </div>
      );
    }
    return <div className="p-8 text-center text-red-400">Error loading models: {error.message}</div>;
  }

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
                className="w-full h-32 bg-slate-800 border border-slate-700 rounded-lg p-4 pb-12 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none resize-none"
              />
              <div className="absolute bottom-4 left-4">
                <input
                  type="file"
                  id="file-upload"
                  multiple
                  onChange={handleFileSelect}
                  className="hidden"
                  disabled={uploading}
                />
                <label
                  htmlFor="file-upload"
                  className={`cursor-pointer flex items-center text-slate-400 hover:text-white ${uploading ? 'opacity-50' : ''}`}
                  title="Attach files"
                >
                  <Paperclip size={20} />
                  {uploading && <span className="ml-2 text-xs">Uploading...</span>}
                </label>
              </div>
              <div className="absolute bottom-4 right-4 flex space-x-2">
                {/* 
                <button className="text-xs bg-slate-700 hover:bg-slate-600 px-2 py-1 rounded text-slate-300">Web Frameworks</button>
                <button className="text-xs bg-slate-700 hover:bg-slate-600 px-2 py-1 rounded text-slate-300">API Security</button>
                 */}
              </div>
            </div>

            {/* Attachment previews */}
            <AttachmentList
              attachments={attachments}
              onRemove={removeAttachment}
              uploading={uploading}
            />

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

            <ModelGrid models={models} selectedModels={selectedModels} onToggle={toggleModel} />
          </div>

          <div>
            <h2 className="text-xl font-bold mb-4">Chairman Model</h2>
            <ModelSelect models={models} value={chairman} onChange={setChairman} />
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
          {/* Root Node - User's Original Question */}
          <div className="mb-6 p-4 bg-slate-900 border border-slate-800 rounded-lg">
            <div className="flex items-center space-x-2 mb-2 text-slate-400">
              <MessageSquare size={20} />
              <h3 className="font-semibold">Your Question</h3>
            </div>
            <div className="text-slate-300 prose prose-invert max-w-none">
              <ReactMarkdown>{prompt}</ReactMarkdown>
            </div>
            <AttachmentList attachments={submittedAttachments} />
          </div>

          {/* New Research Button */}
          <div className="mb-6 flex justify-end">
            <button
              onClick={() => {
                setIsResearching(false);
                setNodes([]);
                setSubmittedAttachments([]);
                setAttachments([]);
                setPrompt('');
              }}
              className="text-sm text-slate-500 hover:text-white transition"
            >
              New Research
            </button>
          </div>
          <NodeTree nodes={nodes} status={status} />
        </div>
      )
      }
    </div >
  );
};

export default Council;
