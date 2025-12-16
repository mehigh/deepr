import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getHistory } from '../api';
import { Clock, MessageSquare, ChevronRight } from 'lucide-react';

const History = () => {
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    getHistory().then(data => {
      setConversations(data);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return <div className="text-slate-400">Loading history...</div>;
  }

  return (
    <div className="max-w-4xl mx-auto">
      <h2 className="text-3xl font-bold mb-6 flex items-center">
        <Clock className="mr-3" /> Research History
      </h2>

      {conversations.length === 0 ? (
        <div className="bg-slate-900 p-8 rounded-lg text-center text-slate-500">
          No research sessions found. Start a new one!
        </div>
      ) : (
        <div className="space-y-4">
          {conversations.map(conv => (
            <div 
              key={conv.id}
              onClick={() => navigate(`/history/${conv.id}`)}
              className="bg-slate-900 border border-slate-800 p-4 rounded-lg hover:border-blue-500 cursor-pointer transition flex justify-between items-center group"
            >
              <div>
                <h3 className="font-semibold text-lg text-slate-200 group-hover:text-blue-400 transition">
                  {conv.title || "Untitled Research"}
                </h3>
                <div className="flex items-center text-xs text-slate-500 mt-1 space-x-2">
                   <span className={`px-1.5 py-0.5 rounded ${conv.method === 'ensemble' ? 'bg-purple-900 text-purple-200' : 'bg-blue-900 text-blue-200'}`}>
                      {conv.method === 'ensemble' ? 'Ensemble' : 'DAG'}
                   </span>
                   <span>•</span>
                   <span>{new Date(conv.created_at).toLocaleDateString()}</span>
                   <span>•</span>
                   <span>{new Date(conv.created_at).toLocaleTimeString()}</span>
                </div>
              </div>
              <ChevronRight className="text-slate-600 group-hover:text-white transition" />
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default History;
