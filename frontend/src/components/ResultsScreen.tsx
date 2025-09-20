import React from 'react';
import { useNavigate, useLocation, useParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Trophy, RotateCcw, Home, Clock, Target, Zap } from 'lucide-react';

const ResultsScreen: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { duelId } = useParams();

  const { winnerId, finalScores, duration, opponent, topic } = location.state || {};

  const isWinner = winnerId === user?.id;
  const isTie = !winnerId;
  const userScore = user?.id === 'player1' ? finalScores?.player1 : finalScores?.player2;
  const opponentScore = user?.id === 'player1' ? finalScores?.player2 : finalScores?.player1;

  const playAgain = () => {
    navigate('/topics');
  };

  const goHome = () => {
    navigate('/topics');
  };

  if (!finalScores || !opponent) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="card text-center">
          <p className="text-gray-600">Loading results...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="card text-center space-y-6">
        {/* Result Header */}
        <div className="space-y-4">
          <div className="flex justify-center">
            {isWinner ? (
              <Trophy className="h-16 w-16 text-yellow-500" />
            ) : isTie ? (
              <Zap className="h-16 w-16 text-blue-500" />
            ) : (
              <Target className="h-16 w-16 text-gray-400" />
            )}
          </div>
          
          <div>
            <h1 className={`text-3xl font-bold mb-2 ${
              isWinner ? 'text-green-600' : isTie ? 'text-blue-600' : 'text-red-600'
            }`}>
              {isWinner ? 'Victory!' : isTie ? 'Tie Game!' : 'Defeat'}
            </h1>
            <p className="text-gray-600">
              Topic: <span className="font-semibold capitalize">{topic?.replace('-', ' ')}</span>
            </p>
          </div>
        </div>

        {/* Scores */}
        <div className="grid grid-cols-2 gap-6">
          <div className={`p-4 rounded-lg ${
            isWinner ? 'bg-green-50 border-2 border-green-200' : 'bg-gray-50 border-2 border-gray-200'
          }`}>
            <div className="space-y-2">
              <h3 className="font-semibold text-gray-900">{user?.username}</h3>
              <div className="text-3xl font-bold text-primary-600">{userScore}</div>
              <p className="text-sm text-gray-500">Your Score</p>
            </div>
          </div>

          <div className={`p-4 rounded-lg ${
            !isWinner && !isTie ? 'bg-green-50 border-2 border-green-200' : 'bg-gray-50 border-2 border-gray-200'
          }`}>
            <div className="space-y-2">
              <h3 className="font-semibold text-gray-900">{opponent.username}</h3>
              <div className="text-3xl font-bold text-primary-600">{opponentScore}</div>
              <p className="text-sm text-gray-500">Opponent Score</p>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="card bg-blue-50 border-blue-200">
          <h3 className="font-semibold text-blue-900 mb-3 flex items-center justify-center">
            <Clock className="h-5 w-5 mr-2" />
            Duel Statistics
          </h3>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-blue-600">10</div>
              <div className="text-sm text-blue-800">Questions</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-blue-600">
                {duration ? Math.round(duration) : 90}s
              </div>
              <div className="text-sm text-blue-800">Duration</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-blue-600">
                {Math.round(((userScore || 0) / 190) * 100)}%
              </div>
              <div className="text-sm text-blue-800">Accuracy</div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button
            onClick={playAgain}
            className="btn-primary flex items-center space-x-2 px-6 py-3"
          >
            <RotateCcw className="h-5 w-5" />
            <span>Play Again</span>
          </button>
          
          <button
            onClick={goHome}
            className="btn-secondary flex items-center space-x-2 px-6 py-3"
          >
            <Home className="h-5 w-5" />
            <span>Home</span>
          </button>
        </div>

        {/* Motivational Message */}
        <div className="text-sm text-gray-600">
          {isWinner && (
            <p>🎉 Great job! You dominated this duel. Ready for another challenge?</p>
          )}
          {isTie && (
            <p>🤝 Evenly matched! That was a close one. Try again to break the tie!</p>
          )}
          {!isWinner && !isTie && (
            <p>💪 Good effort! Every duel makes you stronger. Ready for a rematch?</p>
          )}
        </div>
      </div>

      {/* Performance Breakdown */}
      <div className="mt-8 card">
        <h3 className="font-semibold text-gray-900 mb-4">Performance Breakdown</h3>
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-gray-600">Questions Attempted</span>
            <span className="font-semibold">10/10</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-600">Average Response Time</span>
            <span className="font-semibold">~{Math.round((duration || 90) / 10 * 10) / 10}s</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-600">Points per Question</span>
            <span className="font-semibold">{Math.round((userScore || 0) / 10 * 10) / 10}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResultsScreen;
