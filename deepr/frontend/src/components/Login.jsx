import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login } from '../api';

const Login = () => {
  const [email, setEmail] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      await login(email || 'test@example.com');
      navigate('/');
    } catch (err) {
      alert('Login failed');
    }
  };

  return (
    <div className="h-screen flex items-center justify-center bg-slate-900">
      <div className="bg-slate-800 p-8 rounded-lg shadow-lg w-96">
        <h1 className="text-2xl font-bold text-white mb-6 text-center">DeepR Login</h1>
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-slate-400 mb-1">Email (Dev Mode)</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="test@example.com"
              className="w-full bg-slate-700 text-white rounded p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            type="submit"
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded transition"
          >
            Login / Create Account
          </button>
        </form>
      </div>
    </div>
  );
};

export default Login;
