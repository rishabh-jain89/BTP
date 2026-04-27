import { useEffect, useMemo, useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';
import { fetchAnalytics, fetchAssignments, fetchAssignmentAnalytics } from '../api';

const DIST_COLORS = ['#ff6b6b', '#ff9f43', '#ffc107', '#6c63ff', '#00d4aa'];

function EmptyState({ text }) {
  return (
    <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '40px 0' }}>
      {text}
    </div>
  );
}

function ChartCard({ title, children }) {
  return (
    <div className="chart-card">
      <h3>{title}</h3>
      {children}
    </div>
  );
}

function KpiCard({ label, value, className = '' }) {
  return (
    <div className="kpi-card">
      <div className="kpi-label">{label}</div>
      <div className={`kpi-value ${className}`}>{value}</div>
    </div>
  );
}

export default function Dashboard() {
  const [overall, setOverall] = useState(null);
  const [assignments, setAssignments] = useState([]);
  const [selectedAssignmentId, setSelectedAssignmentId] = useState('');
  const [assignmentAnalytics, setAssignmentAnalytics] = useState(null);
  const [loadingAssignmentAnalytics, setLoadingAssignmentAnalytics] = useState(false);

  useEffect(() => {
    fetchAnalytics().then(setOverall).catch(console.error);
    fetchAssignments().then((res) => {
      setAssignments(res || []);
      if (res?.length) {
        setSelectedAssignmentId(String(res[0].id));
      }
    }).catch(console.error);
  }, []);

  useEffect(() => {
    if (!selectedAssignmentId) {
      setAssignmentAnalytics(null);
      return;
    }

    setLoadingAssignmentAnalytics(true);
    fetchAssignmentAnalytics(selectedAssignmentId)
      .then(setAssignmentAnalytics)
      .catch(console.error)
      .finally(() => setLoadingAssignmentAnalytics(false));
  }, [selectedAssignmentId]);

  const overallDistData = useMemo(() => {
    if (!overall?.score_distribution) return [];
    return Object.entries(overall.score_distribution).map(([range, count], i) => ({
      range,
      count,
      color: DIST_COLORS[i % DIST_COLORS.length],
    }));
  }, [overall]);

  const assignmentDistData = useMemo(() => {
    if (!assignmentAnalytics?.score_distribution) return [];
    return Object.entries(assignmentAnalytics.score_distribution).map(([range, count], i) => ({
      range,
      count,
      color: DIST_COLORS[i % DIST_COLORS.length],
    }));
  }, [assignmentAnalytics]);

  const penaltyData = useMemo(() => {
    return (assignmentAnalytics?.common_penalties || []).map(([name, count]) => ({
      name: String(name),
      count,
    }));
  }, [assignmentAnalytics]);

  const debuggerMistakes = useMemo(() => {
    return (assignmentAnalytics?.debugger_mistakes || []).map(([name, count]) => ({
      name: String(name),
      count,
    }));
  }, [assignmentAnalytics]);

  const logicMistakes = useMemo(() => {
    return (assignmentAnalytics?.logic_mistakes || []).map(([name, count]) => ({
      name: String(name),
      count,
    }));
  }, [assignmentAnalytics]);

  const qualityMistakes = useMemo(() => {
    return (assignmentAnalytics?.quality_mistakes || []).map(([name, count]) => ({
      name: String(name),
      count,
    }));
  }, [assignmentAnalytics]);

  if (!overall) {
    return <div className="loading">Loading dashboard…</div>;
  }

  return (
    <>
      <div className="page-header">
        <h1>Dashboard</h1>
        <p>Overall class performance and assignment-wise mistake analysis.</p>
      </div>

      <div className="section-block">
        <h2 style={{ marginBottom: 16 }}>Overall Overview</h2>
        <div className="kpi-grid">
          <KpiCard label="Total Submissions" value={overall.total_submissions} className="purple" />
          <KpiCard label="Avg Score" value={`${overall.avg_score}/10`} className="green" />
          <KpiCard label="Pass Rate" value={`${overall.pass_rate}%`} className={overall.pass_rate >= 50 ? 'green' : 'red'} />
          <KpiCard label="Pending Eval" value={overall.pending} className="yellow" />
        </div>

        <div className="charts-row">
          <ChartCard title="Overall Score Distribution">
            {overallDistData.every((d) => d.count === 0) ? (
              <EmptyState text="No evaluated submissions yet" />
            ) : (
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={overallDistData} barSize={36}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis dataKey="range" tick={{ fill: '#7986a3', fontSize: 12 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#7986a3', fontSize: 12 }} axisLine={false} tickLine={false} allowDecimals={false} />
                  <Tooltip />
                  <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                    {overallDistData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </ChartCard>
        </div>
      </div>

      <div className="section-block" style={{ marginTop: 28 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, gap: 12 }}>
          <div>
            <h2 style={{ marginBottom: 4 }}>Assignment-wise Analytics</h2>
            <p style={{ color: 'var(--text-muted)', margin: 0 }}>
              See performance and mistakes for one assignment at a time.
            </p>
          </div>

          <select
            value={selectedAssignmentId}
            onChange={(e) => setSelectedAssignmentId(e.target.value)}
            style={{
              minWidth: 260,
              padding: '10px 12px',
              borderRadius: 10,
              background: 'var(--card-bg)',
              color: 'var(--text-primary)',
              border: '1px solid rgba(255,255,255,0.12)',
            }}
          >
            {assignments.map((assignment) => (
              <option key={assignment.id} value={assignment.id}>
                {assignment.title}
              </option>
            ))}
          </select>
        </div>

        {loadingAssignmentAnalytics ? (
          <div className="loading">Loading assignment analytics…</div>
        ) : !assignmentAnalytics ? (
          <EmptyState text="No assignment selected" />
        ) : (
          <>
            <div className="kpi-grid">
              <KpiCard label="Total Submissions" value={assignmentAnalytics.total_submissions} className="purple" />
              <KpiCard label="Avg Score" value={`${assignmentAnalytics.avg_score}/10`} className="green" />
              <KpiCard label="Pass Rate" value={`${assignmentAnalytics.pass_rate}%`} className={assignmentAnalytics.pass_rate >= 50 ? 'green' : 'red'} />
              <KpiCard label="Pending Eval" value={assignmentAnalytics.pending} className="yellow" />
            </div>

            <div className="charts-row">
              <ChartCard title="Assignment Score Distribution">
                {assignmentDistData.every((d) => d.count === 0) ? (
                  <EmptyState text="No evaluated submissions for this assignment" />
                ) : (
                  <ResponsiveContainer width="100%" height={240}>
                    <BarChart data={assignmentDistData} barSize={36}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                      <XAxis dataKey="range" tick={{ fill: '#7986a3', fontSize: 12 }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fill: '#7986a3', fontSize: 12 }} axisLine={false} tickLine={false} allowDecimals={false} />
                      <Tooltip />
                      <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                        {assignmentDistData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </ChartCard>

              <ChartCard title="Penalty Breakdown">
                {penaltyData.length === 0 ? (
                  <EmptyState text="No penalties recorded for this assignment" />
                ) : (
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={penaltyData} layout="vertical" barSize={18}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" horizontal={false} />
                      <XAxis type="number" tick={{ fill: '#7986a3', fontSize: 12 }} axisLine={false} tickLine={false} allowDecimals={false} />
                      <YAxis type="category" dataKey="name" tick={{ fill: '#c9d1d9', fontSize: 12, fontWeight: 500 }} width={200} axisLine={false} tickLine={false} />
                      <Tooltip />
                      <Bar dataKey="count" fill="#ff6b6b" radius={[0, 6, 6, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </ChartCard>
            </div>

            <div className="charts-row">
              <ChartCard title="Debugger Mistakes">
                {debuggerMistakes.length === 0 ? (
                  <EmptyState text="No debugger-classified mistakes yet" />
                ) : (
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={debuggerMistakes} layout="vertical" barSize={18}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" horizontal={false} />
                      <XAxis type="number" tick={{ fill: '#7986a3', fontSize: 12 }} axisLine={false} tickLine={false} allowDecimals={false} />
                      <YAxis type="category" dataKey="name" tick={{ fill: '#c9d1d9', fontSize: 12, fontWeight: 500 }} width={200} axisLine={false} tickLine={false} />
                      <Tooltip />
                      <Bar dataKey="count" fill="#ff9f43" radius={[0, 6, 6, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </ChartCard>

              <ChartCard title="Logic Mistakes">
                {logicMistakes.length === 0 ? (
                  <EmptyState text="No logic-classified mistakes yet" />
                ) : (
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={logicMistakes} layout="vertical" barSize={18}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" horizontal={false} />
                      <XAxis type="number" tick={{ fill: '#7986a3', fontSize: 12 }} axisLine={false} tickLine={false} allowDecimals={false} />
                      <YAxis type="category" dataKey="name" tick={{ fill: '#c9d1d9', fontSize: 12, fontWeight: 500 }} width={200} axisLine={false} tickLine={false} />
                      <Tooltip />
                      <Bar dataKey="count" fill="#6c63ff" radius={[0, 6, 6, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </ChartCard>
            </div>

            <div className="charts-row">
              <ChartCard title="Quality Mistakes">
                {qualityMistakes.length === 0 ? (
                  <EmptyState text="No quality-classified mistakes yet" />
                ) : (
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={qualityMistakes} layout="vertical" barSize={18}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" horizontal={false} />
                      <XAxis type="number" tick={{ fill: '#7986a3', fontSize: 12 }} axisLine={false} tickLine={false} allowDecimals={false} />
                      <YAxis type="category" dataKey="name" tick={{ fill: '#c9d1d9', fontSize: 12, fontWeight: 500 }} width={200} axisLine={false} tickLine={false} />
                      <Tooltip />
                      <Bar dataKey="count" fill="#00d4aa" radius={[0, 6, 6, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </ChartCard>
            </div>
          </>
        )}
      </div>
    </>
  );
}