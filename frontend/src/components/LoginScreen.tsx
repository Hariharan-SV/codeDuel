import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import { Zap, Users, Clock, Trophy } from 'lucide-react';

const LoginScreen: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const { login, user } = useAuth();
  const { showError, showSuccess } = useToast();
  const navigate = useNavigate();

  React.useEffect(() => {
    if (user) {
      navigate('/topics');
    }
  }, [user, navigate]);

  const handleGuestLogin = async () => {
    try {
      setIsLoading(true);
      await login();
      showSuccess('Welcome to CodeDuel!', 'You have successfully logged in as a guest.');
      navigate('/topics');
    } catch (error) {
      console.error('Login failed:', error);
      showError('Login Failed', 'Unable to create guest account. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="flex justify-center">
            <Zap className="h-16 w-16 text-primary-600" />
          </div>
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
            Welcome to CodeDuel
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Real-time programming quiz battles
          </p>
        </div>

        <div className="card space-y-6">
          <div className="grid grid-cols-2 gap-4 text-center">
            <div className="space-y-2">
              <Users className="h-8 w-8 text-primary-600 mx-auto" />
              <p className="text-sm font-medium">1v1 Duels</p>
            </div>
            <div className="space-y-2">
              <Clock className="h-8 w-8 text-primary-600 mx-auto" />
              <p className="text-sm font-medium">90 Seconds</p>
            </div>
            <div className="space-y-2">
              <Trophy className="h-8 w-8 text-primary-600 mx-auto" />
              <p className="text-sm font-medium">10 Questions</p>
            </div>
            <div className="space-y-2">
              <Zap className="h-8 w-8 text-primary-600 mx-auto" />
              <p className="text-sm font-medium">Real-time</p>
            </div>
          </div>

          <div className="space-y-4">
            <button
              onClick={handleGuestLogin}
              disabled={isLoading}
              className="w-full btn-primary py-3 text-lg font-semibold disabled:opacity-50"
            >
              {isLoading ? 'Creating Account...' : 'Start as Guest'}
            </button>
            
            <p className="text-xs text-gray-500 text-center">
              No registration required. Jump right into the action!
            </p>
          </div>
        </div>

        <div className="text-center">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">How it works</h3>
          <div className="space-y-3 text-sm text-gray-600">
            <div className="flex items-center space-x-3">
              <div className="w-6 h-6 bg-primary-600 text-white rounded-full flex items-center justify-center text-xs font-bold">1</div>
              <span>Choose your programming topics</span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-6 h-6 bg-primary-600 text-white rounded-full flex items-center justify-center text-xs font-bold">2</div>
              <span>Get matched with another player</span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-6 h-6 bg-primary-600 text-white rounded-full flex items-center justify-center text-xs font-bold">3</div>
              <span>Answer 10 questions in 90 seconds</span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-6 h-6 bg-primary-600 text-white rounded-full flex items-center justify-center text-xs font-bold">4</div>
              <span>Highest score wins!</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginScreen;
