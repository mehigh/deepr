import { useState, useEffect } from 'react';
import { fetchModels } from './api';

export const useModels = () => {
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchModels()
      .then(data => {
        setModels(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch models", err);
        // Check if error is due to missing API key (400 Bad Request with specific message)
        const isMissingKey = err.response && err.response.status === 400 &&
          (err.response.data?.detail?.includes('API Key') ||
            err.response.data?.detail?.includes('configure'));

        if (isMissingKey) {
          err.isMissingKey = true;
        }
        setError(err);
        setLoading(false);
      });
  }, []);

  return { models, loading, error };
};
