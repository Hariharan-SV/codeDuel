import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation, useParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useSocket } from '../contexts/SocketContext';
import { Clock, Zap, CheckCircle, XCircle } from 'lucide-react';

interface Question {
  prompt: string;
  options: string[];
}

const DuelScreen: React.FC = () => {
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [timeLeft, setTimeLeft] = useState(9);
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [hasAnswered, setHasAnswered] = useState(false);
  const [scores, setScores] = useState({ player1: 0, player2: 0 });
  const [showResult, setShowResult] = useState(false);
  const [lastResult, setLastResult] = useState<any>(null);
  const [isWaitingForNext, setIsWaitingForNext] = useState(false);

  const { user } = useAuth();
  const { socket, emit, on, off, isConnected } = useSocket();
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
    on('question_start', handleQuestionStart);
    on('question_end', handleQuestionEnd);
    on('duel_end', handleDuelEnd);
    on('answer_submitted', handleAnswerSubmitted);
    on('duel_reconnected', handleDuelReconnected);
    on('error', handleError);

    return () => {
      off('question_start', handleQuestionStart);
      off('question_end', handleQuestionEnd);
      off('duel_end', handleDuelEnd);
      off('answer_submitted', handleAnswerSubmitted);
      off('duel_reconnected', handleDuelReconnected);
      off('error', handleError);
    };
  }, [user, duelId, opponent]);

  const handleQuestionStart = (data: any) => {
    console.log('🎯 Question received:', data);
    
    // Clear any existing timer
    if (window.questionTimer) {
      clearTimeout(window.questionTimer);
    }
    
    setCurrentQuestion(data.question);
    setQuestionIndex(data.questionIndex);
    setSelectedAnswer(null);
    setHasAnswered(false);
    setShowResult(false);
    setIsWaitingForNext(false);
    
    // Parse the server's UTC time
    const parseServerTime = (serverTime: string) => {
      // Ensure the time is treated as UTC
      return new Date(serverTime.endsWith('Z') ? serverTime : `${serverTime}Z`);
    };
  
    // Start countdown
    if (data.deadline) {
      const deadline = parseServerTime(data.deadline);
      console.log('⏰ Server deadline (UTC):', deadline.toISOString());
      console.log('⏰ Current time (local):', new Date().toISOString());
      
      const updateTimer = () => {
        const now = new Date();
        const remainingMs = deadline.getTime() - now.getTime();
        const remainingSeconds = Math.max(0, Math.ceil(remainingMs / 1000));
        
        setTimeLeft(remainingSeconds);
        
        if (remainingMs > 100) {
          window.questionTimer = setTimeout(updateTimer, 100);
        } else {
          // Time's up, but only submit if we haven't already answered
          if (!hasAnswered) {
            console.log('⏰ Time is up! Attempting to submit answer...');
            // Add a small delay to ensure the UI updates
            setTimeout(() => {
              submitAnswer(-1).catch(error => {
                console.error('Failed to submit answer on timeout:', error);
                // If we can't submit, just mark as answered to prevent further attempts
                setHasAnswered(true);
                setTimeLeft(0);
              });
            }, 100);
          }
        }
      };
      
      // Start the timer
      updateTimer();
    } else {
      // Fallback to timeLimit if no deadline is provided
      const timeLimit = data.timeLimit || 9;
      console.log('⏰ Using fallback time limit:', timeLimit, 'seconds');
      setTimeLeft(timeLimit);
      
      let startTime = Date.now();
      const endTime = startTime + (timeLimit * 1000);
      
      const updateFallbackTimer = () => {
        const now = Date.now();
        const remainingMs = endTime - now;
        const remainingSeconds = Math.max(0, Math.ceil(remainingMs / 1000));
        
        setTimeLeft(remainingSeconds);
        
        if (remainingMs > 0) {
          window.questionTimer = setTimeout(updateFallbackTimer, 100);
        } else {
          // Time's up, submit an answer if not already answered
          if (!hasAnswered) {
            console.log('⏰ Time is up! Submitting answer...');
            submitAnswer(-1); // -1 indicates no answer was selected
          }
        }
      };
      
      updateFallbackTimer();
    }
  };

  const handleQuestionEnd = (data: any) => {
    setShowResult(true);
    setScores(data.scores);
    setIsWaitingForNext(true);
    
    // Show correct answer and explanation
    setTimeout(() => {
      if (data.questionIndex < 9) { // More questions coming
        setIsWaitingForNext(false);
      }
    }, 3000);
  };

  const handleDuelEnd = (data: any) => {
    navigate(`/results/${duelId}`, {
      state: {
        duelId: data.duelId,
        winnerId: data.winnerId,
        finalScores: data.finalScores,
        duration: data.duration,
        opponent,
        topic
      }
    });
  };

  const handleAnswerSubmitted = (data: any) => {
    setLastResult(data.result);
  };

  const handleDuelReconnected = (data: any) => {
    console.log('🔄 Duel reconnected:', data);
    setScores(data.scores);
    setQuestionIndex(data.currentQuestion || 0);
  };

  const handleError = (error: any) => {
    console.error('Duel error:', error);
    alert(`Error: ${error.message}`);
  };

  const submitAnswer = (optionIndex: number) => {
    console.log('🖱️ User clicked option:', optionIndex);
    
    if (hasAnswered || timeLeft <= 0) {
      console.log('❌ Cannot submit - already answered or time up');
      return;
    }
    
    if (!isConnected || !socket) {
      console.error('❌ Cannot submit - socket not connected');
      return;
    }
    
    const answerData = {
      duelId: duelId!,
      questionIndex,
      selectedIndex: optionIndex,
      clientTs: Date.now()
    };
    
    console.log('📤 Attempting to emit answer:', answerData);
    
    try {
      // Log socket connection status and ID
      console.log('🔌 Socket status:', {
        connected: socket.connected,
        id: socket.id,
        active: (socket as any).active,
        disconnected: socket.disconnected
      });
      
      // Use socket.emit directly with an acknowledgment
      socket.emit('answer', answerData, (response: any) => {
        console.log('✅ Server acknowledged answer:', response);
      });
      
      console.log('📡 Answer emitted, waiting for server acknowledgment...');
      
      setSelectedAnswer(optionIndex);
      setHasAnswered(true);
    } catch (error) {
      console.error('❌ Error emitting answer:', error);
      // Optionally show error to user
    }
  };

  const getOptionClassName = (index: number) => {
    let baseClass = "w-full p-4 text-left rounded-lg border-2 transition-all duration-200 ";
    
    if (!hasAnswered && !showResult) {
      baseClass += "border-gray-200 hover:border-primary-300 hover:bg-primary-50 cursor-pointer";
    } else if (selectedAnswer === index) {
      baseClass += "border-primary-500 bg-primary-100";
    } else {
      baseClass += "border-gray-200 bg-gray-50 cursor-not-allowed";
    }
    
    return baseClass;
  };

  if (!currentQuestion) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="card text-center">
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-gray-200 rounded w-3/4 mx-auto"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2 mx-auto"></div>
          </div>
          <p className="mt-4 text-gray-600">Waiting for first question...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        {/* Add this near the top of your component, maybe next to the question number */}
        <div className="flex items-center justify-between mb-4">
          <span className="text-sm font-medium text-gray-700">
            Question {questionIndex + 1}/10
          </span>
          <div className="flex items-center space-x-1">
            <Clock className="w-4 h-4 text-gray-500" />
            <span className="text-sm font-medium text-gray-700">
              {timeLeft}s left
            </span>
          </div>
        </div>
        
        <div className="flex items-center space-x-6">
          <div className="text-sm">
            <span className="font-medium">{user?.username}</span>
            <span className="ml-2 text-primary-600">{scores.player1}</span>
          </div>
          <div className="text-2xl font-bold text-gray-400">VS</div>
          <div className="text-sm">
            <span className="font-medium">{opponent?.username}</span>
            <span className="ml-2 text-primary-600">{scores.player2}</span>
          </div>
        </div>
      </div>

      {/* Timer */}
      <div className="card mb-6">
        <div className="flex items-center justify-center space-x-4">
          <Clock className={`h-6 w-6 ${timeLeft <= 3 ? 'text-red-500' : 'text-primary-600'}`} />
          <div className={`text-3xl font-bold ${timeLeft <= 3 ? 'text-red-500 animate-pulse' : 'text-primary-600'}`}>
            {timeLeft}s
          </div>
          <div className="w-32 bg-gray-200 rounded-full h-2">
            <div 
              className={`h-2 rounded-full transition-all duration-1000 ${
                timeLeft <= 3 ? 'bg-red-500' : 'bg-primary-600'
              }`}
              style={{ width: `${(timeLeft / 9) * 100}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Question */}
      <div className="card mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">
          {currentQuestion.prompt}
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {currentQuestion.options.map((option, index) => (
            <button
              key={index}
              onClick={() => submitAnswer(index)}
              disabled={hasAnswered || timeLeft <= 0}
              className={getOptionClassName(index)}
            >
              <div className="flex items-center space-x-3">
                <div className="w-6 h-6 rounded-full border-2 border-gray-300 flex items-center justify-center text-sm font-medium">
                  {String.fromCharCode(65 + index)}
                </div>
                <span className="flex-1">{option}</span>
                {selectedAnswer === index && hasAnswered && (
                  <div className="text-primary-600">
                    <CheckCircle className="h-5 w-5" />
                  </div>
                )}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Answer Result */}
      {lastResult && hasAnswered && (
        <div className="card mb-6">
          <div className={`flex items-center space-x-3 ${
            lastResult.correct ? 'text-green-600' : 'text-red-600'
          }`}>
            {lastResult.correct ? (
              <CheckCircle className="h-6 w-6" />
            ) : (
              <XCircle className="h-6 w-6" />
            )}
            <div>
              <p className="font-semibold">
                {lastResult.correct ? 'Correct!' : 'Incorrect'}
              </p>
              {lastResult.correct && (
                <p className="text-sm">
                  +{lastResult.points_earned} points ({lastResult.time_taken.toFixed(1)}s)
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Waiting for next question */}
      {isWaitingForNext && (
        <div className="card text-center">
          <div className="flex items-center justify-center space-x-2 text-gray-600">
            <Zap className="h-5 w-5 animate-pulse" />
            <span>Preparing next question...</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default DuelScreen;
