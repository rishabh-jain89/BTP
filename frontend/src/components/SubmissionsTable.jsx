import { useState, useEffect } from 'react';
import { fetchSubmissions, deleteSubmission } from '../api';
import DetailModal from './DetailModal';

function ScoreBar({ score }) {
    const pct = score != null ? (score / 10) * 100 : 0;
    return (
        <div className="score-bar-wrap">
            <span>{score != null ? score.toFixed(1) : '—'}</span>
            <div className="score-bar">
                <div className="score-bar-fill" style={{ width: `${pct}%` }} />
            </div>
        </div>
    );
}

function StatusBadge({ status, score }) {
    if (status === 'pending') return <span className="badge pending">Pending</span>;
    if (score >= 5) return <span className="badge pass">Pass</span>;
    return <span className="badge fail">Fail</span>;
}

export default function SubmissionsTable() {
    const [rows, setRows] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selected, setSelected] = useState(null);

    const load = () => {
        setLoading(true);
        fetchSubmissions().then(data => { setRows(data); setLoading(false); });
    };

    useEffect(load, []);

    const handleDelete = async (id, e) => {
        e.stopPropagation();
        if (!confirm('Delete this submission and its evaluation results?')) return;
        try {
            await deleteSubmission(id);
            load();
        } catch (err) {
            alert(err.message);
        }
    };

    if (loading) return <div className="loading">Loading submissions…</div>;

    return (
        <>
            <div className="page-header">
                <h1>Submissions</h1>
                <p>All student submissions and their evaluation status.</p>
            </div>

            <div className="table-card">
                <div className="table-header">
                    <h3>All Submissions</h3>
                    <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>{rows.length} total</span>
                </div>
                {rows.length === 0 ? (
                    <div className="empty">No submissions yet. Run the evaluator to get started.</div>
                ) : (
                    <table>
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Student</th>
                                <th>Score / 10</th>
                                <th>Status</th>
                                <th>Submitted At</th>
                                <th style={{ textAlign: 'right' }}>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows.map((row, index) => (
                                <tr key={row.id} onClick={() => setSelected(row.id)} title="Click for full report">
                                    <td style={{ color: 'var(--text-muted)' }}>
                                        {index + 1}
                                    </td>
                                    <td style={{ fontWeight: 600 }}>{row.student_id}</td>
                                    <td><ScoreBar score={row.final_score} /></td>
                                    <td><StatusBadge status={row.status} score={row.final_score} /></td>
                                    <td style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                                        {new Date(row.submitted_at).toLocaleString()}
                                    </td>
                                    <td style={{ textAlign: 'right' }}>
                                        <button
                                            className="action-btn tiny danger"
                                            onClick={(e) => handleDelete(row.id, e)}
                                            title="Delete evaluation"
                                        >
                                            🗑
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            {selected && <DetailModal submissionId={selected} onClose={() => setSelected(null)} />}
        </>
    );
}
