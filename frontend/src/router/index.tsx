import { Navigate, Route, Routes } from 'react-router-dom';
import BasicLayout from '../layouts/BasicLayout';
import AgentConsole from '../pages/AgentConsole';
import CandidateList from '../pages/CandidateList';
import Dashboard from '../pages/Dashboard';
import EventLog from '../pages/EventLog';
import Home from '../pages/Home';
import Integrations from '../pages/Integrations';
import ResumeCenter from '../pages/ResumeCenter';
import TaskCenter from '../pages/TaskCenter';

export default function AppRouter() {
  return (
    <Routes>
      <Route element={<BasicLayout />}>
        <Route path="/" element={<Navigate to="/home" replace />} />
        <Route path="/home" element={<Home />} />
        <Route path="/agent" element={<AgentConsole />} />
        <Route path="/resumes" element={<ResumeCenter />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/candidates" element={<CandidateList />} />
        <Route path="/tasks" element={<TaskCenter />} />
        <Route path="/confirmations" element={<Navigate to="/tasks" replace />} />
        <Route path="/integrations" element={<Integrations />} />
        <Route path="/events" element={<EventLog />} />
        <Route path="*" element={<Navigate to="/home" replace />} />
      </Route>
    </Routes>
  );
}
