import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './components/auth/AuthProvider';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import Demo from './pages/Demo';
import Guide from './pages/Guide';
import Inbox from './pages/Inbox';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Plan from './pages/Plan';
import Settings from './pages/Settings';
import Signup from './pages/Signup';
import Today from './pages/Today';

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/guide" element={<Guide />} />
      <Route path="/about" element={<Navigate to="/guide" replace />} />
      <Route path="/demo" element={<Demo />} />
      <Route element={<ProtectedRoute />}>
        <Route path="/today" element={<Today />} />
        <Route path="/inbox" element={<Inbox />} />
        <Route path="/plan" element={<Plan />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/command" element={<Navigate to="/today" replace />} />
        <Route path="/calendar" element={<Navigate to="/plan" replace />} />
        <Route path="/rescue" element={<Navigate to="/today" replace />} />
        <Route path="/reflection" element={<Navigate to="/today" replace />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
