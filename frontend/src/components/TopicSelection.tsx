import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Code, Database, Globe, Cpu, Layers, Zap, CheckCircle } from 'lucide-react';
import axios from 'axios';

const TopicSelection: React.FC = () => {
  const [selectedTopics, setSelectedTopics] = useState<string[]>([]);
  const [topics, setTopics] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const { user } = useAuth();
  const navigate = useNavigate();

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  useEffect(() => {
    if (!user) {
      navigate('/');
      return;
    }
    fetchTopics();
  }, [user, navigate]);

  const fetchTopics = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/topics`);
      setTopics(response.data.topics);
    } catch (error) {
      console.error('Failed to fetch topics:', error);
    }
  };

  const topicIcons: Record<string, React.ReactNode> = {
    'algorithms': <Cpu className="h-6 w-6" />,
    'data-structures': <Layers className="h-6 w-6" />,
    'javascript': <Code className="h-6 w-6" />,
    'python': <Code className="h-6 w-6" />,
    'react': <Globe className="h-6 w-6" />,
    'databases': <Database className="h-6 w-6" />,
    'system-design': <Layers className="h-6 w-6" />,
    'web-development': <Globe className="h-6 w-6" />,
  };

  const topicLabels: Record<string, string> = {
    'algorithms': 'Algorithms',
    'data-structures': 'Data Structures',
    'javascript': 'JavaScript',
    'python': 'Python',
    'react': 'React',
    'databases': 'Databases',
    'system-design': 'System Design',
    'web-development': 'Web Development',
  };

  const toggleTopic = (topic: string) => {
    setSelectedTopics(prev => 
      prev.includes(topic) 
        ? prev.filter(t => t !== topic)
        : [...prev, topic]
    );
  };

  const startDuel = async () => {
    if (selectedTopics.length === 0) {
      alert('Please select at least one topic');
      return;
    }

    setIsLoading(true);
    // For now, just pick the first selected topic
    const topic = selectedTopics[0];
    navigate('/matchmaking', { state: { topic } });
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Choose Your Battle Topics</h1>
        <p className="text-gray-600">Select one or more topics for your coding duel</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        {topics.map((topic) => (
          <div
            key={topic}
            onClick={() => toggleTopic(topic)}
            className={`card cursor-pointer transition-all duration-200 hover:shadow-md ${
              selectedTopics.includes(topic)
                ? 'ring-2 ring-primary-500 bg-primary-50'
                : 'hover:bg-gray-50'
            }`}
          >
            <div className="flex items-center space-x-3">
              <div className={`p-2 rounded-lg ${
                selectedTopics.includes(topic) 
                  ? 'bg-primary-100 text-primary-600' 
                  : 'bg-gray-100 text-gray-600'
              }`}>
                {topicIcons[topic] || <Code className="h-6 w-6" />}
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900">
                  {topicLabels[topic] || topic}
                </h3>
                <p className="text-sm text-gray-500">
                  Test your knowledge
                </p>
              </div>
              {selectedTopics.includes(topic) && (
                <CheckCircle className="h-5 w-5 text-primary-600" />
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="text-center">
        <div className="mb-4">
          <p className="text-sm text-gray-600">
            {selectedTopics.length === 0 
              ? 'Select topics to start dueling'
              : `${selectedTopics.length} topic${selectedTopics.length > 1 ? 's' : ''} selected`
            }
          </p>
        </div>
        
        <button
          onClick={startDuel}
          disabled={selectedTopics.length === 0 || isLoading}
          className="btn-primary px-8 py-3 text-lg font-semibold disabled:opacity-50 flex items-center space-x-2 mx-auto"
        >
          <Zap className="h-5 w-5" />
          <span>{isLoading ? 'Starting...' : 'Start Duel'}</span>
        </button>
      </div>

      {selectedTopics.length > 0 && (
        <div className="mt-8 card bg-blue-50 border-blue-200">
          <h3 className="font-semibold text-blue-900 mb-2">Selected Topics:</h3>
          <div className="flex flex-wrap gap-2">
            {selectedTopics.map((topic) => (
              <span
                key={topic}
                className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium"
              >
                {topicLabels[topic] || topic}
              </span>
            ))}
          </div>
          <p className="text-sm text-blue-700 mt-2">
            Questions will be randomly selected from these topics during your duel.
          </p>
        </div>
      )}
    </div>
  );
};

export default TopicSelection;
