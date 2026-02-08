import React, { useState, useEffect } from 'react';
import { getSettings, updateSettings, checkAuth } from '../api';

const SettingsPage = () => {
  const [apiKey, setApiKey] = useState('');
  const [hasKey, setHasKey] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [userEmail, setUserEmail] = useState('');

  useEffect(() => {
    getSettings().then(data => setHasKey(data.has_api_key));
    checkAuth().then(data => setUserEmail(data.email));
  }, []);

  const handleSave = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await updateSettings(apiKey);
      setHasKey(true);
      setMessage('API Key saved successfully!');
      setApiKey('');
    } catch (err) {
      setMessage('Error saving key.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto mt-10">
      <h2 className="text-3xl font-bold mb-6">Settings</h2>

      {userEmail && (
        <p className="text-slate-400 mb-6">
          <span className="text-slate-500">Logged in as:</span> {userEmail}
        </p>
      )}

      <div className="bg-slate-900 p-6 rounded-lg border border-slate-800">
        <h3 className="text-xl font-semibold mb-4">OpenRouter Configuration</h3>
        <p className="text-slate-400 mb-4">
          Provide your OpenRouter API Key to enable the Council models.
          Your key is encrypted before storage.
        </p>

        <div className="flex items-center mb-6">
          <div className={`w-3 h-3 rounded-full mr-2 ${hasKey ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span className="text-sm text-slate-300">
            Status: {hasKey ? 'Key Configured' : 'Key Missing'}
          </span>
        </div>

        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label htmlFor="apiKey" className="block text-slate-300 mb-1">API Key</label>
            <input
              id="apiKey"
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="sk-or-..."
              className="w-full bg-slate-800 border border-slate-700 rounded p-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <button
            type="submit"
            disabled={loading || !apiKey}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-bold py-2 px-4 rounded transition"
          >
            {loading ? 'Saving...' : 'Save Configuration'}
          </button>

          {message && <p className="text-sm mt-2 text-green-400">{message}</p>}
        </form>
      </div>
    </div>
  );
};

export default SettingsPage;
