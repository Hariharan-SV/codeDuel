import React, { createContext, useContext, useEffect, useState } from 'react';
import { io, Socket } from 'socket.io-client';
import { useAuth } from './AuthContext';
import { SocketEvents } from '../types';

interface SocketContextType {
  socket: Socket | null;
  isConnected: boolean;
  emit: <K extends keyof SocketEvents>(event: K, data: SocketEvents[K]) => void;
  on: <K extends keyof SocketEvents>(event: K, callback: (data: SocketEvents[K]) => void) => void;
  off: <K extends keyof SocketEvents>(event: K, callback?: (data: SocketEvents[K]) => void) => void;
}

const SocketContext = createContext<SocketContextType | undefined>(undefined);

export const useSocket = () => {
  const context = useContext(SocketContext);
  if (context === undefined) {
    throw new Error('useSocket must be used within a SocketProvider');
  }
  return context;
};

interface SocketProviderProps {
  children: React.ReactNode;
}

export const SocketProvider: React.FC<SocketProviderProps> = ({ children }) => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const { user, token } = useAuth();

  const WS_URL = 'http://localhost:8000';

  useEffect(() => {
    if (user && token) {
      const newSocket = io(WS_URL, {
        auth: {
          token,
          userId: user.id,
        },
        transports: ['websocket', 'polling'],
      });

      newSocket.on('connect', () => {
        console.log('Connected to server');
        setIsConnected(true);
      });

      newSocket.on('disconnect', () => {
        console.log('Disconnected from server');
        setIsConnected(false);
      });

      newSocket.on('error', (error) => {
        console.error('Socket error:', error);
      });

      setSocket(newSocket);

      return () => {
        newSocket.close();
        setSocket(null);
        setIsConnected(false);
      };
    }
  }, [user, token, WS_URL]);

  const emit = <K extends keyof SocketEvents>(event: K, data: SocketEvents[K]) => {
    if (socket) {
      console.log(`📤 Emitting socket event: ${event as string}`, data);
      socket.emit(event as string, data);
    } else {
      console.warn('⚠️ Socket not connected, cannot emit:', event);
    }
  };

  const on = <K extends keyof SocketEvents>(
    event: K,
    callback: (data: SocketEvents[K]) => void
  ) => {
    if (socket) {
      socket.on(event as string, (data) => {
        console.log(`📡 Socket event received: ${event as string}`, data);
        callback(data);
      });
    }
  };

  const off = <K extends keyof SocketEvents>(
    event: K,
    callback?: (data: SocketEvents[K]) => void
  ) => {
    if (socket) {
      if (callback) {
        socket.off(event as string, callback);
      } else {
        socket.off(event as string);
      }
    }
  };

  const value = {
    socket,
    isConnected,
    emit,
    on,
    off,
  };

  return <SocketContext.Provider value={value}>{children}</SocketContext.Provider>;
};
