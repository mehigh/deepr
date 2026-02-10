import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Bot, Brain, MessageSquare, CheckCircle, GitCommit, Clock } from 'lucide-react';
import AttachmentList from './AttachmentList';
import ParametersSpoiler from './ParametersSpoiler';
import CostSummary from './CostSummary';

const NodeTree = ({ nodes, status }) => {
  // Simple hierarchical view
  // 1. Root (User Prompt)
  // 2. Plan (Coordinator)
  // 3. Research (List of findings)
  // 4. Critique (List of critiques)
  // 5. Synthesis (Final Answer)

  // Group nodes by type
  const root = nodes.find(n => n.type === 'root');
  const plan = nodes.find(n => n.type === 'plan');
  const research = nodes.filter(n => n.type === 'research');
  const critiques = nodes.filter(n => n.type === 'critique');
  const synthesis = nodes.find(n => n.type === 'synthesis');

  // DxO Specific Nodes
  const proposals = nodes.filter(n => n.type === 'proposal' || n.type === 'refinement');
  const testCases = nodes.filter(n => n.type === 'test_cases');
  const verdict = nodes.find(n => n.type === 'verdict');

  // Check if this is a DxO session based on node types
  const isDxO = proposals.length > 0 || testCases.length > 0 || verdict;

  if (isDxO) {
    // Chronological Render for DxO
    const sortedNodes = [...nodes].sort((a, b) => a.id - b.id);

    return (
      <div className="space-y-8 pb-20">
        {sortedNodes.map((node) => {
          if (node.type === 'root') return null; // Skip root/prompt in tree usually

          // Normalize model string (History uses model_name, Stream uses model)
          const modelStr = node.model || node.model_name || 'System';

          // Render based on type
          if (node.type === 'proposal' || node.type === 'refinement') {
            return (
              <div key={node.id} className="animate-fade-in">
                <div className="flex items-center space-x-2 mb-2 text-blue-400">
                  <GitCommit size={20} />
                  <h3 className="font-semibold text-lg">{node.type === 'proposal' ? 'Initial Proposal' : 'Refinement'}</h3>
                  <span className="text-xs bg-slate-800 px-2 py-1 rounded text-slate-400">{modelStr}</span>
                </div>
                <div className="bg-slate-900 border-l-2 border-blue-500 p-4 rounded-r-lg text-slate-300 prose prose-invert max-w-none">
                  <ReactMarkdown>{node.content}</ReactMarkdown>
                  <ParametersSpoiler
                    actualCost={node.actual_cost}
                    attachmentFilenames={node.attachment_filenames}
                    promptSent={node.prompt_sent} />
                </div>
              </div>
            );
          }

          if (node.type === 'critique') {
            // Parse "Role Name (model_id)" format if present
            let roleName = "Peer Critique";
            let modelId = modelStr;

            if (modelStr && modelStr.includes('(')) {
              const parts = modelStr.split('(');
              roleName = parts[0].trim();
              modelId = parts[1].replace(')', '').trim();
            }

            return (
              <div key={node.id} className="animate-fade-in ml-8 border-l-2 border-slate-800 pl-4">
                <div className="flex items-center space-x-2 mb-2 text-orange-400">
                  <MessageSquare size={20} />
                  <h3 className="font-semibold text-lg">{roleName}</h3>
                  <span className="text-xs font-bold text-orange-300 bg-orange-900/30 px-2 py-1 rounded">{modelId}</span>
                </div>
                <div className="bg-slate-900 border border-orange-900/30 p-4 rounded-lg text-sm text-slate-300">
                  <ReactMarkdown>{node.content}</ReactMarkdown>
                  <ParametersSpoiler
                    actualCost={node.actual_cost}
                    attachmentFilenames={node.attachment_filenames}
                    promptSent={node.prompt_sent} />
                </div>
              </div>
            );
          }

          if (node.type === 'test_cases') {
            return (
              <div key={node.id} className="animate-fade-in ml-8 border-l-2 border-slate-800 pl-4">
                <div className="flex items-center space-x-2 mb-2 text-red-400">
                  <Bot size={20} />
                  <h3 className="font-semibold text-lg">QA Test Cases</h3>
                  <span className="text-xs font-bold text-red-300 bg-red-900/30 px-2 py-1 rounded">{modelStr}</span>
                </div>
                <div className="bg-slate-900 border border-red-900/30 p-4 rounded-lg text-sm text-slate-300">
                  <ReactMarkdown>{node.content}</ReactMarkdown>
                  <ParametersSpoiler
                    actualCost={node.actual_cost}
                    attachmentFilenames={node.attachment_filenames}
                    promptSent={node.prompt_sent} />
                </div>
              </div>
            );
          }

          if (node.type === 'verdict') {
            return (
              <div key={node.id} className="animate-fade-in mt-8">
                <div className="flex items-center space-x-2 mb-2 text-green-400">
                  <CheckCircle size={20} />
                  <h3 className="font-semibold text-lg">Final Verdict</h3>
                  <span className="text-xs bg-slate-800 px-2 py-1 rounded text-slate-400">{modelStr}</span>
                </div>
                <div className="bg-gradient-to-br from-slate-900 to-slate-800 border border-green-500/30 p-6 rounded-lg shadow-lg shadow-green-900/10 prose prose-invert max-w-none">
                  <ReactMarkdown>{node.content}</ReactMarkdown>

                  {/* Attachments from ROOT node or current node */}
                  <AttachmentList attachments={root?.attachments || []} />

                  <ParametersSpoiler
                    actualCost={node.actual_cost}
                    totalCost={nodes.reduce((sum, n) => sum + (n.actual_cost || 0), 0)}
                    attachmentFilenames={node.attachment_filenames}
                    promptSent={node.prompt_sent}
                    warnings={node.warnings || []}
                  />
                </div>

                {/* Total Cost Summary */}
                <CostSummary conversationId={node.conversation_id} />
              </div>
            );
          }

          return null;
        })}

        {/* Status Indicator */}
        {status && status !== 'done' && (
          <div className="flex items-center justify-center p-4 text-slate-500 animate-pulse">
            <Clock size={16} className="mr-2" />
            <span>{status}</span>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-20">
      {/* Plan Section */}
      {plan && (
        <div className="animate-fade-in">
          <div className="flex items-center space-x-2 mb-2 text-blue-400">
            <GitCommit size={20} />
            <h3 className="font-semibold text-lg">Research Plan</h3>
            <span className="text-xs bg-slate-800 px-2 py-1 rounded text-slate-400">{plan.model || plan.model_name}</span>
          </div>
          <div className="bg-slate-900 border-l-2 border-blue-500 p-4 rounded-r-lg text-slate-300 prose prose-invert max-w-none">
            <ReactMarkdown>{plan.content}</ReactMarkdown>
            <ParametersSpoiler
              actualCost={plan.actual_cost}
              attachmentFilenames={plan.attachment_filenames}
              promptSent={plan.prompt_sent} />
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
                  <span className="text-xs font-bold text-purple-300 bg-purple-900/30 px-2 py-1 rounded">{node.model || node.model_name}</span>
                </div>
                <div className="text-sm text-slate-300 max-h-60 overflow-y-auto custom-scrollbar">
                  <ReactMarkdown>{node.content}</ReactMarkdown>
                  <ParametersSpoiler
                    actualCost={node.actual_cost}
                    attachmentFilenames={node.attachment_filenames}
                    promptSent={node.prompt_sent} />
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
                  <span className="text-xs font-bold text-orange-300 bg-orange-900/30 px-2 py-1 rounded">Critic: {node.model || node.model_name}</span>
                </div>
                <div className="text-sm text-slate-300 max-h-40 overflow-y-auto custom-scrollbar">
                  <ReactMarkdown>{node.content}</ReactMarkdown>
                  <ParametersSpoiler
                    actualCost={node.actual_cost}
                    attachmentFilenames={node.attachment_filenames}
                    promptSent={node.prompt_sent} />
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
            <span className="text-xs bg-slate-800 px-2 py-1 rounded text-slate-400">{synthesis.model || synthesis.model_name}</span>
          </div>
          <div className="bg-gradient-to-br from-slate-900 to-slate-800 border border-green-500/30 p-6 rounded-lg shadow-lg shadow-green-900/10 prose prose-invert max-w-none">
            <ReactMarkdown>{synthesis.content}</ReactMarkdown>
            <AttachmentList attachments={root?.attachments || []} />
            <ParametersSpoiler
              attachmentFilenames={synthesis.attachment_filenames}
              promptSent={synthesis.prompt_sent}
              actualCost={synthesis.actual_cost}
              totalCost={nodes.reduce((sum, n) => sum + (n.actual_cost || 0), 0)}
              warnings={synthesis.warnings || []}
            />
          </div>

          {/* Total Cost Summary */}
          <CostSummary conversationId={synthesis.conversation_id} />
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
