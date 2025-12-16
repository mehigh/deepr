import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getConversation } from '../api';
import NodeTree from './NodeTree';
import { ArrowLeft } from 'lucide-react';

const HistoryDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [conversation, setConversation] = useState(null);
  const [nodes, setNodes] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getConversation(id).then(data => {
      setConversation(data.conversation);
      setNodes(data.nodes);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, [id]);

  if (loading) return <div className="text-slate-400">Loading...</div>;
  if (!conversation) return <div className="text-red-400">Conversation not found.</div>;

  return (
    <div className="max-w-5xl mx-auto">
      <button 
        onClick={() => navigate('/history')}
        className="flex items-center text-slate-400 hover:text-white mb-6 transition"
      >
        <ArrowLeft size={16} className="mr-1" /> Back to History
      </button>

      <div className="mb-8 border-b border-slate-800 pb-4">
        <h1 className="text-2xl font-bold text-white mb-2">{conversation.title}</h1>
        <div className="flex items-center space-x-2">
            <span className={`text-xs px-2 py-1 rounded ${conversation.method === 'ensemble' ? 'bg-purple-900 text-purple-200' : 'bg-blue-900 text-blue-200'}`}>
                {conversation.method === 'ensemble' ? 'Ensemble' : 'AI Council (DAG)'}
            </span>
            <p className="text-xs text-slate-500">
            Started on {new Date(conversation.created_at).toLocaleString()}
            </p>
        </div>
      </div>

      <NodeTree nodes={nodes} status="done" />
    </div>
  );
};

export default HistoryDetail;
