import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useSocket } from '../contexts/SocketContext';
import { Loader2, Users, X } from 'lucide-react';

const MatchmakingScreen: React.FC = () => {
  const [isSearching, setIsSearching] = useState(false);
  const [ticket, setTicket] = useState<any>(null);
  const { user } = useAuth();
  const { socket, emit, on, off } = useSocket();
  const navigate = useNavigate();
  const location = useLocation();
  
  const topic = location.state?.topic;

  useEffect(() => {
    if (!user || !topic) {
      navigate('/topics');
      return;
    }

    // Start matchmaking
    startMatchmaking();

    // Set up socket listeners
    on('queue_joined', handleQueueJoined);
    on('matched', handleMatched);
    on('error', handleError);

    return () => {
      // Clean up listeners
      off('queue_joined', handleQueueJoined);
      off('matched', handleMatched);
      off('error', handleError);
      
      // Cancel matchmaking if still searching
      if (ticket) {
        emit('cancel_queue', { ticketId: ticket.id });
      }
    };
  }, [user, topic]);

  const startMatchmaking = () => {
    if (!user || !socket) return;
    
    setIsSearching(true);
    emit('join_queue', { userId: user.id, topic });
  };

  const handleQueueJoined = (data: any) => {
    setTicket(data.ticket);
  };

  const handleMatched = (data: any) => {
    setIsSearching(false);
    navigate(`/lobby/${data.duelId}`, { 
      state: { 
        duelId: data.duelId, 
        opponent: data.opponent, 
        topic: data.topic 
      } 
    });
  };

  const handleError = (error: any) => {
    console.error('Matchmaking error:', error);
    setIsSearching(false);
    alert(`Error: ${error.message}`);
  };

  const cancelMatchmaking = () => {
    if (ticket) {
      emit('cancel_queue', { ticketId: ticket.id });
    }
    setIsSearching(false);
    navigate('/topics');
  };

  return (
    <div className="max-w-md mx-auto">
      <div className="card text-center space-y-6">
        <div className="space-y-4">
          <div className="flex justify-center">
            {isSearching ? (
              <Loader2 className="h-16 w-16 text-primary-600 animate-spin" />
            ) : (
              <Users className="h-16 w-16 text-gray-400" />
            )}
          </div>
          
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              {isSearching ? 'Finding Opponent...' : 'Matchmaking'}
            </h2>
            <p className="text-gray-600">
              Topic: <span className="font-semibold capitalize">{topic?.replace('-', ' ')}</span>
            </p>
          </div>
        </div>

        {isSearching && (
          <div className="space-y-4">
            <div className="flex justify-center space-x-1">
              <div className="w-2 h-2 bg-primary-600 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-primary-600 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
              <div className="w-2 h-2 bg-primary-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            </div>
            
            <p className="text-sm text-gray-500">
              Looking for another player who wants to duel in {topic?.replace('-', ' ')}...
            </p>
          </div>
        )}

        <div className="pt-4">
          <button
            onClick={cancelMatchmaking}
            className="btn-secondary flex items-center space-x-2 mx-auto"
          >
            <X className="h-4 w-4" />
            <span>Cancel</span>
          </button>
        </div>
      </div>

      <div className="mt-8 card bg-yellow-50 border-yellow-200">
        <h3 className="font-semibold text-yellow-900 mb-2">While you wait...</h3>
        <ul className="text-sm text-yellow-800 space-y-1">
          <li>• Each duel has 10 questions</li>
          <li>• You have 9 seconds per question</li>
          <li>• Faster correct answers earn bonus points</li>
          <li>• Questions are multiple choice</li>
        </ul>
      </div>
    </div>
  );
};

export default MatchmakingScreen;
