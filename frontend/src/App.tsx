import { lazy, Suspense } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './components/auth/AuthProvider';
import { ProtectedRoute } from './components/auth/ProtectedRoute';

const Demo = lazy(() => import('./pages/Demo'));
const Guide = lazy(() => import('./pages/Guide'));
const Inbox = lazy(() => import('./pages/Inbox'));
const Landing = lazy(() => import('./pages/Landing'));
const Login = lazy(() => import('./pages/Login'));
const Plan = lazy(() => import('./pages/Plan'));
const Projects = lazy(() => import('./pages/Projects'));
const Week = lazy(() => import('./pages/Week'));
const Settings = lazy(() => import('./pages/Settings'));
const Signup = lazy(() => import('./pages/Signup'));
const Today = lazy(() => import('./pages/Today'));

export function RouteFallback() {
  return <div role="status" aria-live="polite" className="flex min-h-screen items-center justify-center bg-canvas px-4 text-sm font-medium text-muted">Loading ChronOS…</div>;
}

export function AppRoutes() {
  return <Suspense fallback={<RouteFallback />}><Routes>
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
      <Route path="/week" element={<Week />} />
      <Route path="/projects" element={<Projects />} />
      <Route path="/projects/:projectId" element={<Projects />} />
      <Route path="/settings" element={<Settings />} />
      <Route path="/command" element={<Navigate to="/today" replace />} />
      <Route path="/calendar" element={<Navigate to="/plan" replace />} />
      <Route path="/rescue" element={<Navigate to="/today" replace />} />
      <Route path="/reflection" element={<Navigate to="/today" replace />} />
    </Route>
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes></Suspense>;
}

export default function App() {
  return <BrowserRouter><AuthProvider><AppRoutes /></AuthProvider></BrowserRouter>;
}
