import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Command from './pages/Command';
import Inbox from './pages/Inbox';
import Calendar from './pages/Calendar';
import Rescue from './pages/Rescue';
import Reflection from './pages/Reflection';
import Settings from './pages/Settings';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />

        {/* App Workspace Routes */}
        <Route path="/command" element={<Command />} />
        <Route path="/inbox" element={<Inbox />} />
        <Route path="/calendar" element={<Calendar />} />
        <Route path="/rescue" element={<Rescue />} />
        <Route path="/reflection" element={<Reflection />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </BrowserRouter>
  );
}
