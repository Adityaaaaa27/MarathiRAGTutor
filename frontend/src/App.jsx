import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Splash from './pages/Splash'
import Explore from './pages/Explore'
import Chat from './pages/Chat'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Splash />} />
      <Route path="/explore" element={<Explore />} />
      <Route path="/chat" element={<Chat />} />
    </Routes>
  )
}

export default App
