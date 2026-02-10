import React, { useState, useEffect } from 'react';
import { DollarSign } from 'lucide-react';

const CostSummary = ({ conversationId }) => {
    const [totalCost, setTotalCost] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!conversationId) return;

        fetch(`/api/conversations/${conversationId}/cost`)
            .then(res => res.json())
            .then(data => {
                setTotalCost(data.total_cost);
                setLoading(false);
            })
            .catch(err => {
                console.error('Error fetching cost:', err);
                setLoading(false);
            });
    }, [conversationId]);

    if (loading || totalCost === null || totalCost === 0) return null;

    return (
        <div className="mt-6 p-4 bg-gradient-to-r from-green-900/30 to-blue-900/30 border border-green-500/30 rounded-lg animate-fade-in">
            <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                    <DollarSign size={24} className="text-green-400" />
                    <span className="text-lg font-semibold text-slate-200">Total Cost</span>
                </div>
                <div className="text-2xl font-bold text-green-400 font-mono">
                    ${totalCost.toFixed(4)}
                </div>
            </div>
            <div className="mt-2 text-xs text-slate-400">
                Total cost for all operations in this conversation
            </div>
        </div>
    );
};

export default CostSummary;
