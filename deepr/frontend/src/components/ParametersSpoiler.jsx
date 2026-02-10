import React, { useState } from 'react';
import { ChevronRight, ChevronDown, AlertTriangle, DollarSign, } from 'lucide-react';

const ParametersSpoiler = ({ attachmentFilenames, promptSent, actualCost, totalCost, warnings }) => {
    const [isOpen, setIsOpen] = useState(false);

    const hasData = attachmentFilenames || promptSent || (actualCost !== null && actualCost !== undefined) || (totalCost !== null && totalCost !== undefined) || (warnings && warnings.length > 0);

    if (!hasData) {
        return null;
    }

    return (
        <div className="mt-3 border-t border-slate-700 pt-3">
            {/* Warnings section - ALWAYS visible if present */}
            {warnings && warnings.length > 0 && (
                <div className="mb-3 p-3 bg-yellow-900/30 border border-yellow-600/50 rounded">
                    {warnings.map((warning, idx) => (
                        <div key={idx} className="text-sm text-yellow-300 flex items-start">
                            <AlertTriangle size={16} className="mr-2 mt-0.5 flex-shrink-0" />
                            <span>{warning}</span>
                        </div>
                    ))}
                </div>
            )}

            {/* Collapsible parameters section */}
            {(attachmentFilenames || promptSent) && (
                <>
                    <button
                        onClick={() => setIsOpen(!isOpen)}
                        className="flex items-center space-x-2 text-sm text-slate-400 hover:text-slate-300 transition-colors"
                    >
                        {isOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                        <span className="font-medium">Details</span>
                    </button>

                    {isOpen && (
                        <div className="mt-3 p-3 bg-slate-900/50 rounded border border-slate-700 space-y-3 animate-fade-in">

                            {/* Cost display - ALWAYS visible if present */}
                            {(actualCost !== null && actualCost !== undefined) || (totalCost !== null && totalCost !== undefined) ? (
                                <div className="mb-3 p-3 bg-green-900/20 border border-green-600/30 rounded flex flex-col space-y-1">
                                    {actualCost !== null && actualCost !== undefined && (
                                        <div className="flex items-center space-x-2">
                                            <DollarSign size={16} className="text-green-400" />
                                            <div className="text-xs font-semibold text-green-400">Node Cost : </div>
                                            <span className="font-mono text-green-300">${Number(actualCost).toFixed(6)}</span>
                                        </div>
                                    )}

                                    {totalCost !== null && totalCost !== undefined && (
                                        <div className="flex items-center space-x-2 pt-1 mt-1 border-t border-green-600/30">
                                            <DollarSign size={16} className="text-blue-300" />
                                            <div className="text-xs font-semibold text-blue-300">Total Conv. Cost : </div>
                                            <span className="font-mono text-blue-200">${Number(totalCost).toFixed(6)}</span>
                                        </div>
                                    )}
                                </div>
                            ) : null}

                            {attachmentFilenames && (
                                <div>
                                    <div className="text-xs font-semibold text-slate-400 mb-1">Attachments Sent:</div>
                                    <div className="text-sm text-slate-300 font-mono bg-slate-800 p-2 rounded">
                                        {attachmentFilenames}
                                    </div>
                                </div>
                            )}

                            {promptSent && (
                                <div>
                                    <div className="text-xs font-semibold text-slate-400 mb-1">Prompt Sent:</div>
                                    <pre className="text-xs text-slate-300 bg-slate-800 p-3 rounded overflow-x-auto whitespace-pre-wrap break-words max-h-96 overflow-y-auto">
                                        {promptSent}
                                    </pre>
                                </div>
                            )}
                        </div>
                    )}
                </>
            )}
        </div>
    );
};

export default ParametersSpoiler;
