import React, { useState } from 'react';
import { Zap, File, FileText, FileImage, FileVideoCamera, FileVolume, ChevronRight, ChevronDown } from 'lucide-react';

const ModelItem = ({ model, isSelected, onToggle }) => {
  const [isOpen, setIsOpen] = useState(false);

  // Pricing values per million tokens  
  const priceIn = (Number(model.pricing.prompt) === -1) ? '?' : (Number(model.pricing.prompt || 0) * 1000000).toFixed(2)
  const priceOut = (Number(model.pricing.completion) === -1) ? '?' : (Number(model.pricing.completion || 0) * 1000000).toFixed(2)
  return (
    <div
      onClick={onToggle}
      className={`cursor-pointer p-4 rounded-lg border flex items-start space-x-3 transition ${isSelected
        ? 'bg-blue-900/20 border-blue-500'
        : 'bg-slate-900 border-slate-800 hover:border-slate-700'
        }`}
    >
      <div className="flex flex-col items-center">
        <div className={`w-5 h-5 rounded border flex items-center justify-center mt-1 ${isSelected ? 'bg-blue-600 border-blue-600' : 'border-slate-600'
          }`}>
          {isSelected && <Zap size={12} className="text-white" />}
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            setIsOpen(!isOpen);
          }}
          className="text-slate-400 hover:text-slate-300 transition-colors mt-2"
        >
          {isOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        </button>
      </div>
      <div className="flex-1">
        <div className="font-semibold text-sm">{model.name}</div>

        {/* Icons and Pricing in one line */}
        <div className="flex items-center mt-1 flex-wrap text-slate-400">
          {model.capabilities.text && <span title="Text"><FileText size={16} className="mr-2 flex-shrink-0" /></span>}
          {model.capabilities.image && <span title="Image"><FileImage size={16} className="mr-2 flex-shrink-0" /></span>}
          {model.capabilities.video && <span title="Video"><FileVideoCamera size={16} className="mr-2 flex-shrink-0" /></span>}
          {model.capabilities.audio && <span title="Audio"><FileVolume size={16} className="mr-2 flex-shrink-0" /></span>}
          {model.capabilities.file && <span title="File"><File size={16} className="mr-2 flex-shrink-0" /></span>}

          <span title="Pricing per million tokens (prompt/completion)" className="text-xs font-mono ml-1">
            (${priceIn}/
            ${priceOut})
          </span>
        </div>



        {isOpen && (
          <div
            className="mt-3 p-3 bg-slate-900/50 rounded border border-slate-700 space-y-3 animate-fade-in"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="text-xs text-slate-300 bg-slate-800/50 p-3 rounded-lg whitespace-pre-wrap break-words leading-relaxed border border-slate-700/50">
              {model.description}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export const ModelGrid = ({ models, selectedModels, onToggle }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {models.map(model => (
        <ModelItem
          key={model.id}
          model={model}
          isSelected={selectedModels.includes(model.id)}
          onToggle={() => onToggle(model.id)}
        />
      ))}
    </div>
  );
};

export const ModelSelect = ({ models, value, onChange, className }) => {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className={className || "w-full bg-slate-900 border border-slate-800 rounded-lg p-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"}
    >
      {models.map(model => {
        // Pricing values per million tokens 
        const priceIn = (Number(model.pricing.prompt) === -1) ? '?' : (Number(model.pricing.prompt || 0) * 1000000).toFixed(2)
        const priceOut = (Number(model.pricing.completion) === -1) ? '?' : (Number(model.pricing.completion || 0) * 1000000).toFixed(2)

        const caps = [];
        if (model.capabilities.image) caps.push("Img");
        if (model.capabilities.video) caps.push("Vid");
        if (model.capabilities.audio) caps.push("Aud");
        if (model.capabilities.file) caps.push("Fil");
        if (model.capabilities.text) caps.push("Txt");

        const capsStr = caps.length > 0 ? `[${caps.join(',')}]` : "";

        return (
          <option key={model.id} value={model.id}>
            {model.name} {capsStr} (${priceIn}/${priceOut})
          </option>
        );
      })}
    </select>
  );
};
