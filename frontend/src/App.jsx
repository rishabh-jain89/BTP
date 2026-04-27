import { useState } from 'react';
import './index.css';
import Dashboard from './components/Dashboard';
import SubmissionsTable from './components/SubmissionsTable';
import UploadPage from './components/UploadPage';
import AssignmentsPage from './components/AssignmentsPage';
import StudentsPage from './components/StudentsPage';
import PlagiarismPage from './components/PlagiarismPage';

const NAV = [
  { id: 'dashboard', label: 'Dashboard', icon: '/icons/dashboard.svg' },
  { id: 'assignments', label: 'Assignments', icon: '/icons/assignments.svg' },
  { id: 'students', label: 'Students', icon: '/icons/students.svg' },
  { id: 'submissions', label: 'Submissions', icon: '/icons/submissions.svg' },
  { id: 'plagiarism', label: 'Plagiarism', icon: '/icons/plagiarism.svg' },
  { id: 'upload', label: 'Upload & Eval', icon: '/icons/upload.svg' },
];

export default function App() {
  const [page, setPage] = useState('dashboard');

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-logo">Programming<span> Evaluation</span></div>
        <div className="nav-section-label">Overview</div>
        {NAV.slice(0, 1).map(n => (
          <div
            key={n.id}
            className={`nav-item ${page === n.id ? 'active' : ''}`}
            onClick={() => setPage(n.id)}
          >
            <img src={n.icon} alt={n.label} className="nav-icon" />
            <span>{n.label}</span>
          </div>
        ))}
        <div className="nav-section-label">Management</div>
        {NAV.slice(1, 3).map(n => (
          <div
            key={n.id}
            className={`nav-item ${page === n.id ? 'active' : ''}`}
            onClick={() => setPage(n.id)}
          >
            <img src={n.icon} alt={n.label} className="nav-icon" />
            <span>{n.label}</span>
          </div>
        ))}
        <div className="nav-section-label">Evaluation</div>
        {NAV.slice(3).map(n => (
          <div
            key={n.id}
            className={`nav-item ${page === n.id ? 'active' : ''}`}
            onClick={() => setPage(n.id)}
          >
            <img src={n.icon} alt={n.label} className="nav-icon" />
            <span>{n.label}</span>
          </div>
        ))}
      </aside>

      <main className="main-content">
        {page === 'dashboard' && <Dashboard />}
        {page === 'assignments' && <AssignmentsPage />}
        {page === 'students' && <StudentsPage />}
        {page === 'submissions' && <SubmissionsTable />}
        {page === 'plagiarism' && <PlagiarismPage />}
        {page === 'upload' && <UploadPage />}
      </main>
    </div>
  );
}
