import React from 'react';
import { Construction } from 'lucide-react';

const ComingSoon = ({ title, description }) => {
  return (
    <div className="flex flex-col items-center justify-center h-full text-slate-400 space-y-4 animate-fade-in">
      <div className="w-16 h-16 bg-slate-800 rounded-full flex items-center justify-center mb-4">
        <Construction size={32} className="text-blue-500" />
      </div>
      <h2 className="text-3xl font-bold text-slate-200">{title}</h2>
      <p className="text-slate-500 max-w-md text-center">
        {description || "This feature is currently under development. Check back soon for updates!"}
      </p>
    </div>
  );
};

export default ComingSoon;



