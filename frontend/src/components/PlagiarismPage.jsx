import { useState, useEffect } from 'react';
import { fetchAssignments, fetchPlagiarismResults, triggerPlagiarismCheck, compareTwoFiles } from '../api';

export default function PlagiarismPage() {
    const [tab, setTab] = useState('all');

    return (
        <>
            <div className="page-header">
                <h1>Plagiarism Detection</h1>
                <p>Analyze code similarity across assignments or directly compare two snippets.</p>
            </div>

            <div className="modal-tabs" style={{ marginBottom: '24px' }}>
                <button
                    className={`tab-btn ${tab === 'all' ? 'active' : ''}`}
                    onClick={() => setTab('all')}
                >
                    Check All Students
                </button>
                <button
                    className={`tab-btn ${tab === 'compare' ? 'active' : ''}`}
                    onClick={() => setTab('compare')}
                >
                    Compare 2 Files
                </button>
            </div>

            {tab === 'all' && <AllStudentsPlagiarism />}
            {tab === 'compare' && <CompareTwoFiles />}
        </>
    );
}

function AllStudentsPlagiarism() {
    const [assignments, setAssignments] = useState([]);
    const [selectedId, setSelectedId] = useState('');
    const [plagiarismData, setPlagiarismData] = useState(null);
    const [plagiarismRunning, setPlagiarismRunning] = useState(false);
    const [loadingAssignments, setLoadingAssignments] = useState(true);

    useEffect(() => {
        fetchAssignments().then(data => {
            setAssignments(data);
            setLoadingAssignments(false);
        });
    }, []);

    useEffect(() => {
        if (!selectedId) {
            setPlagiarismData(null);
            return;
        }
        setPlagiarismData(null);
        fetchPlagiarismResults(selectedId).then(setPlagiarismData).catch(() => {});
    }, [selectedId]);

    const handleRunPlagiarism = async () => {
        if (!selectedId) return;
        setPlagiarismRunning(true);
        try {
            await triggerPlagiarismCheck(selectedId);
            setTimeout(async () => {
                const pollInterval = setInterval(async () => {
                    try {
                        const data = await fetchPlagiarismResults(selectedId);
                        if (data.total_results > 0) {
                            setPlagiarismData(data);
                            setPlagiarismRunning(false);
                            clearInterval(pollInterval);
                        }
                    } catch (e) { /* keep polling */ }
                }, 3000);
                setTimeout(() => { clearInterval(pollInterval); setPlagiarismRunning(false); }, 120000);
            }, 2000);
        } catch (err) {
            alert(err.message);
            setPlagiarismRunning(false);
        }
    };

    if (loadingAssignments) return <div className="loading">Loading…</div>;

    return (
        <div className="table-card" style={{ padding: '24px' }}>
            <div style={{ marginBottom: '20px' }}>
                <label className="form-label">Select Assignment</label>
                <select 
                    className="text-input" 
                    value={selectedId} 
                    onChange={e => setSelectedId(e.target.value)}
                    style={{ maxWidth: '400px' }}
                >
                    <option value="">-- Choose Assignment --</option>
                    {assignments.map(a => (
                        <option key={a.id} value={a.id}>{a.title} (#{a.id})</option>
                    ))}
                </select>
            </div>

            {selectedId && (
                <div className="plagiarism-section" style={{ padding: 0 }}>
                    <div className="plagiarism-header">
                        <div>
                            <h4>Plagiarism Analysis</h4>
                            <p className="plagiarism-subtitle">Results for Assignment #{selectedId}.</p>
                        </div>
                        <button
                            className={`action-btn primary ${plagiarismRunning ? 'loading' : ''}`}
                            onClick={handleRunPlagiarism}
                            disabled={plagiarismRunning}
                        >
                            {plagiarismRunning ? <><span className="spinner" /> Analyzing…</> : '🔍 Run Plagiarism Check'}
                        </button>
                    </div>

                    {plagiarismData && plagiarismData.total_results > 0 ? (
                        <>
                            <div className="plagiarism-summary-grid">
                                <div className="plag-stat-card">
                                    <div className="plag-stat-label">Students Analyzed</div>
                                    <div className="plag-stat-value">{plagiarismData.total_results}</div>
                                </div>
                                <div className="plag-stat-card">
                                    <div className="plag-stat-label">Highest Similarity</div>
                                    <div className={`plag-stat-value ${
                                        plagiarismData.results[0]?.max_similarity_score >= 70 ? 'flagged' :
                                        plagiarismData.results[0]?.max_similarity_score >= 40 ? 'warning' : 'clean'
                                    }`}>
                                        {plagiarismData.results[0]?.max_similarity_score?.toFixed(1)}%
                                    </div>
                                </div>
                                <div className="plag-stat-card">
                                    <div className="plag-stat-label">Flagged (≥70%)</div>
                                    <div className="plag-stat-value flagged">
                                        {plagiarismData.results.filter(r => r.max_similarity_score >= 70).length}
                                    </div>
                                </div>
                                <div className="plag-stat-card">
                                    <div className="plag-stat-label">Warnings (40-70%)</div>
                                    <div className="plag-stat-value warning">
                                        {plagiarismData.results.filter(r => r.max_similarity_score >= 40 && r.max_similarity_score < 70).length}
                                    </div>
                                </div>
                            </div>

                            <div className="table-card" style={{ marginTop: '24px' }}>
                                <table>
                                    <thead>
                                        <tr>
                                            <th>Student</th>
                                            <th>Similarity</th>
                                            <th>Most Similar To</th>
                                            <th>Status</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {plagiarismData.results.map((r, i) => (
                                            <tr key={r.id || i}>
                                                <td style={{ fontWeight: 600 }}>{r.student_id}</td>
                                                <td>
                                                    <div className="similarity-bar-wrap">
                                                        <div className="similarity-bar">
                                                            <div
                                                                className={`similarity-bar-fill ${
                                                                    r.max_similarity_score >= 70 ? 'flagged' :
                                                                    r.max_similarity_score >= 40 ? 'warning' : 'clean'
                                                                }`}
                                                                style={{ width: `${Math.min(r.max_similarity_score, 100)}%` }}
                                                            />
                                                        </div>
                                                        <span className={`similarity-value ${
                                                            r.max_similarity_score >= 70 ? 'flagged' :
                                                            r.max_similarity_score >= 40 ? 'warning' : 'clean'
                                                        }`}>
                                                            {r.max_similarity_score.toFixed(1)}%
                                                        </span>
                                                    </div>
                                                </td>
                                                <td>{r.most_similar_to || '—'}</td>
                                                <td>
                                                    <span className={`badge ${
                                                        r.max_similarity_score >= 70 ? 'fail' :
                                                        r.max_similarity_score >= 40 ? 'pending' : 'pass'
                                                    }`}>
                                                        {r.max_similarity_score >= 70 ? '🚨 Flagged' :
                                                         r.max_similarity_score >= 40 ? '⚠ Warning' : '✓ Clean'}
                                                    </span>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </>
                    ) : !plagiarismRunning ? (
                        <div className="empty-state small" style={{ marginTop: '24px' }}>
                            <div className="empty-icon">🔍</div>
                            <h3>No plagiarism data for this assignment</h3>
                            <p>Run a plagiarism check to analyze code similarity between submissions.</p>
                        </div>
                    ) : null}
                </div>
            )}
        </div>
    );
}

function CompareTwoFiles() {
    const [code1, setCode1] = useState('');
    const [code2, setCode2] = useState('');
    const [comparing, setComparing] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    const handleCompare = async () => {
        if (!code1.trim() || !code2.trim()) return;
        setComparing(true);
        setError(null);
        setResult(null);
        try {
            const data = await compareTwoFiles(code1, code2);
            setResult(data.similarity_score);
        } catch (err) {
            setError(err.message || 'Comparison failed');
        }
        setComparing(false);
    };

    return (
        <div className="table-card" style={{ padding: '24px' }}>
            <h3 style={{ marginBottom: '16px' }}>Direct Code Comparison</h3>
            <p style={{ color: 'var(--text-muted)', marginBottom: '24px' }}>
                Paste the contents of two code submissions below to get an instant JPlag similarity score between them. Supported language is C.
            </p>

            <div style={{ display: 'flex', gap: '24px', marginBottom: '24px' }}>
                <div style={{ flex: 1 }}>
                    <label className="form-label">Code Snippet 1</label>
                    <textarea 
                        className="text-input" 
                        rows={15} 
                        value={code1}
                        onChange={e => setCode1(e.target.value)}
                        placeholder="Paste first code file here..."
                        style={{ fontFamily: 'monospace', resize: 'vertical' }}
                    />
                </div>
                <div style={{ flex: 1 }}>
                    <label className="form-label">Code Snippet 2</label>
                    <textarea 
                        className="text-input" 
                        rows={15}
                        value={code2}
                        onChange={e => setCode2(e.target.value)}
                        placeholder="Paste second code file here..."
                        style={{ fontFamily: 'monospace', resize: 'vertical' }}
                    />
                </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
                <button
                    className={`action-btn primary ${comparing ? 'loading' : ''}`}
                    onClick={handleCompare}
                    disabled={!code1.trim() || !code2.trim() || comparing}
                >
                    {comparing ? <><span className="spinner" /> Comparing…</> : '⚖️ Compare Code'}
                </button>
                
                {error && <div className="status-banner error" style={{ flex: 1 }}>⚠ {error}</div>}

                {result !== null && (
                    <div className="plag-stat-card" style={{ flex: 1, margin: 0, padding: '16px', background: 'rgba(255,255,255,0.02)' }}>
                        <div className="plag-stat-label">Similarity Score</div>
                        <div className={`plag-stat-value ${
                            result >= 70 ? 'flagged' :
                            result >= 40 ? 'warning' : 'clean'
                        }`}>
                            {result.toFixed(1)}% <span style={{ fontSize: '0.8rem', fontWeight: 'normal', color: 'var(--text-muted)' }}>
                                ({result >= 70 ? 'High Risk' : result >= 40 ? 'Moderate Risk' : 'Low Risk'})
                            </span>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
