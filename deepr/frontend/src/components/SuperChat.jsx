import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { streamSuperChat, getConversation, uploadFiles } from '../api';
import NodeTree from './NodeTree';
import AttachmentList from './AttachmentList';
import { ModelGrid, ModelSelect } from './ModelSelector';
import { useModels } from '../hooks';
import { Send, User, MessageSquare, Paperclip } from 'lucide-react';

const SuperChat = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const { models, loading: modelsLoading, error: modelsError } = useModels();

    const [nodes, setNodes] = useState([]);
    const [prompt, setPrompt] = useState('');
    const [selectedModels, setSelectedModels] = useState(['openai/gpt-4o', 'google/gemini-2.5-flash']);
    const [chairman, setChairman] = useState('openai/gpt-4o');
    const [isProcessing, setIsProcessing] = useState(false);
    const [status, setStatus] = useState('');
    const [attachments, setAttachments] = useState([]);
    const [uploading, setUploading] = useState(false);
    const bottomRef = useRef(null);

    const scrollToBottom = () => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [nodes, status]);

    // Load existing
    useEffect(() => {
        if (id) {
            getConversation(id).then(data => {
                setNodes(data.nodes);
                // Infer models
                const researchNodes = data.nodes.filter(n => n.type === 'research');
                const uniqueModels = [...new Set(researchNodes.map(n => n.model_name))];
                if (uniqueModels.length > 0) setSelectedModels(uniqueModels);

                const synthesisNodes = data.nodes.filter(n => n.type === 'synthesis');
                if (synthesisNodes.length > 0) {
                    setChairman(synthesisNodes[synthesisNodes.length - 1].model_name);
                }
            }).catch(err => console.error("Failed to load conversation", err));
        } else {
            // Reset if navigating to new
            if (nodes.length > 0) setNodes([]);
            setSelectedModels(['openai/gpt-4o', 'google/gemini-2.5-flash']);
            setChairman('openai/gpt-4o');
        }
    }, [id]);

    const toggleModel = (modelId) => {
        setSelectedModels(prev =>
            prev.includes(modelId) ? prev.filter(m => m !== modelId) : [...prev, modelId]
        );
    };

    const handleFileSelect = async (e) => {
        const files = Array.from(e.target.files);
        if (files.length === 0) return;

        setUploading(true);
        try {
            const uploadedItems = await uploadFiles(files);
            setAttachments(prev => [...prev, ...uploadedItems]);
        } catch (error) {
            console.error('Upload failed:', error);
            setStatus('Error uploading files: ' + error.message);
        } finally {
            setUploading(false);
            e.target.value = '';
        }
    };

    const removeAttachment = (id) => {
        setAttachments(prev => prev.filter(a => a.id !== id));
    };

    const handleSend = () => {
        if (!prompt || isProcessing) return;

        setIsProcessing(true);
        setStatus('Initializing...');
        const currentPrompt = prompt;
        const currentAttachments = [...attachments];
        const attachmentIds = currentAttachments.map(a => a.id);

        setPrompt('');
        setAttachments([]);

        streamSuperChat(currentPrompt, id, selectedModels, chairman, (event) => {
            if (event.type === 'start') {
                if (!id) {
                    navigate(`/super-chat/${event.conversation_id}`, { replace: true });
                }
            } else if (event.type === 'status') {
                setStatus(event.message);
            } else if (event.type === 'node') {
                setNodes(prev => {
                    // Avoid duplicates
                    if (prev.find(n => n.id === event.node.id)) return prev;
                    return [...prev, event.node];
                });
            } else if (event.type === 'done') {
                setStatus('');
                setIsProcessing(false);
            } else if (event.type === 'error') {
                setStatus('Error: ' + event.message);
                setIsProcessing(false);
                setPrompt(currentPrompt);
            }
        }, attachmentIds);
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    // Group nodes into turns
    const turns = [];
    const rootNodes = nodes.filter(n => n.type === 'root').sort((a, b) => a.id - b.id);

    rootNodes.forEach(root => {
        const children = nodes.filter(n => n.parent_id === root.id);
        turns.push({
            root: root,
            children: children
        });
    });

    // If new session (no turns), show setup
    if (!id && turns.length === 0) {
        if (modelsLoading) return <div className="p-8 text-center text-slate-400">Loading models...</div>;


        // Handle missing key error
        if (modelsError && modelsError.isMissingKey) {
            return (
                <div className="max-w-4xl mx-auto mt-20 p-8 bg-slate-900 border border-slate-700 rounded-lg text-center animate-fade-in">
                    <div className="text-yellow-500 text-5xl mb-4">⚠️</div>
                    <h2 className="text-2xl font-bold text-white mb-2">OpenRouter API Key Required</h2>
                    <p className="text-slate-400 mb-6">
                        To start a SuperChat session, you need to configure your OpenRouter API Key.
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

        if (modelsError) return <div className="p-8 text-center text-red-400">Error loading models: {modelsError.message}</div>;

        return (
            <div className="max-w-5xl mx-auto space-y-8 animate-fade-in pb-20">
                <div>
                    <h2 className="text-2xl font-bold mb-4">SuperChat</h2>
                    <p className="text-slate-400 mb-4">Start a collaborative session with the Council. Select your team below.</p>
                </div>

                <div>
                    <div className="flex justify-between items-end mb-4">
                        <h2 className="text-xl font-bold">Council Members</h2>
                        <span className="text-sm text-slate-400">Select 2+ models</span>
                    </div>
                    <ModelGrid models={models} selectedModels={selectedModels} onToggle={toggleModel} />
                </div>

                <div>
                    <h2 className="text-xl font-bold mb-4">Chairman Model</h2>
                    <ModelSelect models={models} value={chairman} onChange={setChairman} />
                </div>

                <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
                    <textarea
                        value={prompt}
                        onChange={(e) => setPrompt(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Enter your initial prompt..."
                        className="w-full h-32 bg-transparent text-white focus:outline-none resize-none"
                    />
                    <div className="flex justify-between items-center mt-2">
                        <div className="flex items-center">
                            <input
                                type="file"
                                id="file-upload-super"
                                multiple
                                onChange={handleFileSelect}
                                className="hidden"
                                disabled={uploading}
                            />
                            <label
                                htmlFor="file-upload-super"
                                className={`cursor-pointer flex items-center text-slate-400 hover:text-white transition ${uploading ? 'opacity-50' : ''}`}
                                title="Attach files"
                            >
                                <Paperclip size={20} />
                                {uploading && <span className="ml-2 text-xs">Uploading...</span>}
                            </label>

                            <div className="ml-4">
                                <AttachmentList attachments={attachments} onRemove={removeAttachment} uploading={uploading} />
                            </div>
                        </div>
                        <button
                            onClick={handleSend}
                            disabled={!prompt || selectedModels.length === 0 || uploading}
                            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-bold disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2 shadow-lg transition"
                        >
                            <Send size={16} />
                            <span>Start Session</span>
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    // Active Chat View
    return (
        <div className="max-w-5xl mx-auto flex flex-col h-[calc(100vh-2rem)]">
            <div className="flex-1 overflow-y-auto space-y-8 pb-32">
                {/* Header / Config Summary */}
                <div className="border-b border-slate-800 pb-4 mb-8">
                    <h2 className="text-xl font-bold text-white flex items-center">
                        <MessageSquare className="mr-2" size={24} />
                        SuperChat Session
                    </h2>
                    <div className="flex flex-wrap gap-2 mt-2">
                        {selectedModels.map(m => (
                            <span key={m} className="text-xs bg-slate-800 text-slate-400 px-2 py-1 rounded">{m}</span>
                        ))}
                        <span className="text-xs bg-blue-900/30 text-blue-400 px-2 py-1 rounded border border-blue-900">Chairman: {chairman}</span>
                    </div>
                </div>

                {turns.map(turn => (
                    <div key={turn.root.id} className="animate-fade-in">
                        {/* User Message */}
                        <div className="flex justify-end mb-4">
                            <div className="bg-blue-600 text-white p-4 rounded-2xl rounded-tr-none max-w-2xl shadow-lg">
                                <div className="text-xs text-blue-200 mb-1 flex items-center">
                                    <User size={12} className="mr-1" />
                                    You
                                </div>
                                <div className="whitespace-pre-wrap">{turn.root.content}</div>
                                {turn.root.attachments && turn.root.attachments.length > 0 && (
                                    <div className="mt-3 pt-3 border-t border-blue-500/30">
                                        <AttachmentList attachments={turn.root.attachments} />
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Council Response (NodeTree) */}
                        <div className="pl-4 border-l-2 border-slate-800 ml-4">
                            <NodeTree nodes={turn.children} status={turn === turns[turns.length - 1] ? status : 'done'} />
                        </div>
                    </div>
                ))}

                <div ref={bottomRef} />
            </div>

            {/* Input Area */}
            <div className="fixed bottom-6 left-64 right-6 mx-auto max-w-5xl bg-slate-900/95 backdrop-blur-sm border border-slate-700 rounded-xl p-2 shadow-2xl z-10">
                {attachments.length > 0 && (
                    <div className="px-3 py-2 border-b border-slate-800 mb-2">
                        <AttachmentList attachments={attachments} onRemove={removeAttachment} uploading={uploading} />
                    </div>
                )}
                <div className="flex items-end">
                    <div className="p-3">
                        <input
                            type="file"
                            id="file-upload-chat"
                            multiple
                            onChange={handleFileSelect}
                            className="hidden"
                            disabled={uploading || isProcessing}
                        />
                        <label
                            htmlFor="file-upload-chat"
                            className={`cursor-pointer flex items-center text-slate-400 hover:text-white transition ${uploading || isProcessing ? 'opacity-50 cursor-not-allowed' : ''}`}
                            title="Attach files"
                        >
                            <Paperclip size={20} />
                        </label>
                    </div>
                    <textarea
                        value={prompt}
                        onChange={(e) => setPrompt(e.target.value)}
                        onKeyDown={handleKeyDown}
                        disabled={isProcessing}
                        placeholder={isProcessing ? "Council is deliberating..." : "Type a message to continue..."}
                        className="flex-1 bg-transparent text-white p-3 focus:outline-none resize-none max-h-32 disabled:text-slate-500"
                        rows={1}
                    />
                    <button
                        onClick={handleSend}
                        disabled={(!prompt && attachments.length === 0) || isProcessing || uploading}
                        className="p-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition"
                    >
                        <Send size={20} />
                    </button>
                </div>
            </div>
        </div>
    );
};

export default SuperChat;
