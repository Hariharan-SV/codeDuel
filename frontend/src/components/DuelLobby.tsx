import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation, useParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useSocket } from '../contexts/SocketContext';
import { Users, Clock, Zap } from 'lucide-react';

const DuelLobby: React.FC = () => {
  const [countdown, setCountdown] = useState<number | null>(null);
  const [isReady, setIsReady] = useState(false);
  const { user } = useAuth();
  const { on, off } = useSocket();
  const navigate = useNavigate();
  const location = useLocation();
  const { duelId } = useParams();

  const { opponent, topic } = location.state || {};

  useEffect(() => {
    if (!user || !duelId || !opponent) {
      navigate('/topics');
      return;
    }

    // Set up socket listeners
    on('pregame_countdown', handlePregameCountdown);
    on('question_start', handleDuelStart);
    on('error', handleError);

    return () => {
      off('pregame_countdown', handlePregameCountdown);
      off('question_start', handleDuelStart);
      off('error', handleError);
    };
  }, [user, duelId, opponent]);

  const handlePregameCountdown = (data: any) => {
    const startsAt = new Date(data.startsAt);
    const now = new Date();
    const timeLeft = Math.max(0, Math.ceil((startsAt.getTime() - now.getTime()) / 1000));
    
    setCountdown(timeLeft);
    
    const timer = setInterval(() => {
      setCountdown(prev => {
        if (prev === null || prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  };

  const handleDuelStart = (data: any) => {
    navigate(`/duel/${duelId}`, { 
      state: { 
        duelId: data.duelId,
        opponent,
        topic 
      } 
    });
  };

  const handleError = (error: any) => {
    console.error('Lobby error:', error);
    alert(`Error: ${error.message}`);
    navigate('/topics');
  };

  const handleReady = () => {
    setIsReady(true);
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="card text-center space-y-6">
        <div className="space-y-4">
          <h1 className="text-3xl font-bold text-gray-900">Duel Lobby</h1>
          <p className="text-gray-600">
            Topic: <span className="font-semibold capitalize">{topic?.replace('-', ' ')}</span>
          </p>
        </div>

        <div className="grid grid-cols-2 gap-6">
          <div className="space-y-3">
            <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto">
              <Users className="h-8 w-8 text-primary-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">{user?.username}</h3>
              <p className="text-sm text-gray-500">You</p>
              <div className="mt-2">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  isReady ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {isReady ? 'Ready' : 'Getting Ready...'}
                </span>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <div className="w-16 h-16 bg-secondary-100 rounded-full flex items-center justify-center mx-auto">
              <Users className="h-8 w-8 text-secondary-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">{opponent?.username}</h3>
              <p className="text-sm text-gray-500">Opponent</p>
              <div className="mt-2">
                <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  Ready
                </span>
              </div>
            </div>
          </div>
        </div>

        {countdown !== null && countdown > 0 && (
          <div className="space-y-4">
            <div className="text-6xl font-bold text-primary-600 animate-pulse">
              {countdown}
            </div>
            <p className="text-lg text-gray-600">Duel starting in...</p>
          </div>
        )}

        {countdown === 0 && (
          <div className="space-y-4">
            <Zap className="h-16 w-16 text-yellow-500 mx-auto animate-bounce" />
            <p className="text-xl font-semibold text-gray-900">Starting Duel!</p>
          </div>
        )}

        {countdown === null && !isReady && (
          <div className="space-y-4">
            <button
              onClick={handleReady}
              className="btn-primary px-8 py-3 text-lg font-semibold"
            >
              I'm Ready!
            </button>
            <p className="text-sm text-gray-500">
              Click when you're ready to start the duel
            </p>
          </div>
        )}

        <div className="card bg-blue-50 border-blue-200 text-left">
          <h3 className="font-semibold text-blue-900 mb-3 flex items-center">
            <Clock className="h-5 w-5 mr-2" />
            Duel Rules
          </h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• 10 multiple-choice questions</li>
            <li>• 9 seconds per question</li>
            <li>• +10 points for correct answers</li>
            <li>• +1 bonus point per second remaining</li>
            <li>• Highest total score wins</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default DuelLobby;
