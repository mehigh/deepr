import React from 'react';
import { NavLink } from 'react-router-dom';
import { MessageSquare, Settings, Clock, Users, Globe, Zap } from 'lucide-react';

const Sidebar = () => {
  return (
    <div className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col">
      <div className="p-6 flex items-center space-x-3">
        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center font-bold text-white">D</div>
        <span className="text-xl font-bold text-white">DeepR</span>
      </div>

      <nav className="flex-1 px-4 space-y-2">
        <NavItem to="/" icon={<Users size={20} />} label="Council" />
        <NavItem to="/dxo" icon={<Zap size={20} />} label="DxO" />
        <NavItem to="/history" icon={<Clock size={20} />} label="History" />
        <div className="pt-4 pb-2 text-xs font-semibold text-slate-500 uppercase">Tools</div>
        <NavItem to="/super-chat" icon={<MessageSquare size={20} />} label="Super Chat" />
        <NavItem to="/frontier" icon={<Globe size={20} />} label="Frontier" />
      </nav>

      <div className="p-4 border-t border-slate-800">
        <NavItem to="/settings" icon={<Settings size={20} />} label="Settings" />
      </div>
    </div>
  );
};

const NavItem = ({ to, icon, label }) => (
  <NavLink
    to={to}
    className={({ isActive }) =>
      `flex items-center space-x-3 px-3 py-2 rounded-lg transition ${
        isActive ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-white'
      }`
    }
  >
    {icon}
    <span>{label}</span>
  </NavLink>
);

export default Sidebar;
