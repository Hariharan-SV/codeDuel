import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { SocketProvider } from './contexts/SocketContext'
import { ToastProvider } from './contexts/ToastContext'
import LoginScreen from './components/LoginScreen'
import TopicSelection from './components/TopicSelection'
import MatchmakingScreen from './components/MatchmakingScreen'
import DuelLobby from './components/DuelLobby'
import DuelScreen from './components/DuelScreen'
import ResultsScreen from './components/ResultsScreen'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'

function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <SocketProvider>
          <Router>
            <Layout>
              <Routes>
                <Route path="/" element={<LoginScreen />} />
                <Route path="/topics" element={
                  <ProtectedRoute>
                    <TopicSelection />
                  </ProtectedRoute>
                } />
                <Route path="/matchmaking" element={
                  <ProtectedRoute>
                    <MatchmakingScreen />
                  </ProtectedRoute>
                } />
                <Route path="/lobby/:duelId" element={
                  <ProtectedRoute>
                    <DuelLobby />
                  </ProtectedRoute>
                } />
                <Route path="/duel/:duelId" element={
                  <ProtectedRoute>
                    <DuelScreen />
                  </ProtectedRoute>
                } />
                <Route path="/results/:duelId" element={
                  <ProtectedRoute>
                    <ResultsScreen />
                  </ProtectedRoute>
                } />
              </Routes>
            </Layout>
          </Router>
        </SocketProvider>
      </AuthProvider>
    </ToastProvider>
  )
}

export default App
