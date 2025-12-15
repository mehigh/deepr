import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Bot, Brain, MessageSquare, CheckCircle, GitCommit, Clock } from 'lucide-react';

const NodeTree = ({ nodes, status }) => {
  // Simple hierarchical view
  // 1. Root (User Prompt)
  // 2. Plan (Coordinator)
  // 3. Research (List of findings)
  // 4. Critique (List of critiques)
  // 5. Synthesis (Final Answer)
  
  // Group nodes by type
  const root = nodes.find(n => n.type === 'root'); // Not actually streamed back usually, but if we did
  const plan = nodes.find(n => n.type === 'plan');
  const research = nodes.filter(n => n.type === 'research');
  const critiques = nodes.filter(n => n.type === 'critique');
  const synthesis = nodes.find(n => n.type === 'synthesis');

  return (
    <div className="space-y-8 pb-20">
      {/* Plan Section */}
      {plan && (
        <div className="animate-fade-in">
          <div className="flex items-center space-x-2 mb-2 text-blue-400">
            <GitCommit size={20} />
            <h3 className="font-semibold text-lg">Research Plan</h3>
            <span className="text-xs bg-slate-800 px-2 py-1 rounded text-slate-400">{plan.model}</span>
          </div>
          <div className="bg-slate-900 border-l-2 border-blue-500 p-4 rounded-r-lg text-slate-300 prose prose-invert max-w-none">
            <ReactMarkdown>{plan.content}</ReactMarkdown>
          </div>
        </div>
      )}

      {/* Research Section */}
      {research.length > 0 && (
        <div className="animate-fade-in">
          <div className="flex items-center space-x-2 mb-2 text-purple-400">
            <Brain size={20} />
            <h3 className="font-semibold text-lg">Council Research</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {research.map(node => (
              <div key={node.id} className="bg-slate-900 border border-slate-800 p-4 rounded-lg">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-xs font-bold text-purple-300 bg-purple-900/30 px-2 py-1 rounded">{node.model}</span>
                </div>
                <div className="text-sm text-slate-300 max-h-60 overflow-y-auto custom-scrollbar">
                   <ReactMarkdown>{node.content}</ReactMarkdown>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Critique Section */}
      {critiques.length > 0 && (
        <div className="animate-fade-in">
          <div className="flex items-center space-x-2 mb-2 text-orange-400">
            <MessageSquare size={20} />
            <h3 className="font-semibold text-lg">Peer Critique</h3>
          </div>
           <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {critiques.map(node => (
              <div key={node.id} className="bg-slate-900 border border-orange-900/30 p-4 rounded-lg">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-xs font-bold text-orange-300 bg-orange-900/30 px-2 py-1 rounded">Critic: {node.model}</span>
                </div>
                 <div className="text-sm text-slate-300 max-h-40 overflow-y-auto custom-scrollbar">
                   <ReactMarkdown>{node.content}</ReactMarkdown>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Synthesis Section */}
      {synthesis && (
        <div className="animate-fade-in">
           <div className="flex items-center space-x-2 mb-2 text-green-400">
            <CheckCircle size={20} />
            <h3 className="font-semibold text-lg">Final Synthesis</h3>
            <span className="text-xs bg-slate-800 px-2 py-1 rounded text-slate-400">{synthesis.model}</span>
          </div>
          <div className="bg-gradient-to-br from-slate-900 to-slate-800 border border-green-500/30 p-6 rounded-lg shadow-lg shadow-green-900/10 prose prose-invert max-w-none">
            <ReactMarkdown>{synthesis.content}</ReactMarkdown>
          </div>
        </div>
      )}

      {/* Status Indicator */}
      {status && status !== 'done' && (
        <div className="flex items-center justify-center p-4 text-slate-500 animate-pulse">
          <Clock size={16} className="mr-2" />
          <span>{status}</span>
        </div>
      )}
    </div>
  );
};

export default NodeTree;
