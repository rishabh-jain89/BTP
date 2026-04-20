import { useState, useEffect } from 'react';
import {
    fetchSubmission,
    askSubmissionQuestion,
    fetchSubmissionAskHistory,
    fetchSubmissionQuestions,
} from '../api';

const TABS = ['Grader', 'Logic', 'Debugger', 'Quality', 'Q&A'];

function JsonBlock({ data }) {
    if (!data) return <div className="report-value" style={{ color: 'var(--text-muted)' }}>No data available</div>;
    const txt = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
    return <div className="report-value">{txt}</div>;
}

function ValueRenderer({ value }) {
    if (value === null || value === undefined) return <span style={{ color: 'var(--text-muted)' }}>—</span>;

    let parsed = value;
    if (typeof value === 'string' && (value.trim().startsWith('[') || value.trim().startsWith('{'))) {
        try { parsed = JSON.parse(value); } catch (e) { /* ignore */ }
    }

    if (Array.isArray(parsed)) {
        if (parsed.length === 0) return <span style={{ color: 'var(--text-muted)' }}>None</span>;
        return (
            <ul className="agent-report-comments">
                {parsed.map((item, i) => (
                    <li key={i}><ValueRenderer value={item} /></li>
                ))}
            </ul>
        );
    }

    if (typeof parsed === 'object' && parsed !== null) {
        const entries = Object.entries(parsed);
        if (entries.length === 0) return <span style={{ color: 'var(--text-muted)' }}>Empty object</span>;
        return (
            <div className="inner-attr-grid">
                {entries.map(([k, v]) => (
                    <div key={k} className="inner-attr">
                        <span className="attr-label">{k.replace(/^- /, '')}:</span>
                        <span className="attr-val"><ValueRenderer value={v} /></span>
                    </div>
                ))}
            </div>
        );
    }

    return <span>{String(parsed)}</span>;
}

function FormattedReport({ data }) {
    if (!data) return <div className="report-value" style={{ color: 'var(--text-muted)' }}>No report data available</div>;

    let obj = data;
    if (typeof data === 'string') {
        try { obj = JSON.parse(data); } catch (e) { return <div className="report-value">{data}</div>; }
    }

    if (typeof obj !== 'object' || obj === null || Array.isArray(obj)) {
        return <div className="report-value">{JSON.stringify(obj, null, 2)}</div>;
    }

    const entries = Object.entries(obj);
    const isFlat = entries.every(([_, val]) => typeof val !== 'object' || val === null);

    if (isFlat) {
        return (
            <div className="agent-report-section">
                <ValueRenderer value={obj} />
            </div>
        );
    }

    return (
        <div className="agent-report-container">
            {entries.map(([key, val]) => {
                const title = key
                    .split('_')
                    .map(w => w.replace(/^- /, ''))
                    .map(w => w.charAt(0).toUpperCase() + w.slice(1))
                    .join(' ');

                if (val && typeof val === 'object' && !Array.isArray(val) && (val.comments || val.score || val.description || val.rating)) {
                    return (
                        <div key={key} className="agent-report-section">
                            <div className="agent-report-section-header">
                                <h5>{title}</h5>
                                {(val.score != null || val.rating != null) && (
                                    <div className="agent-report-score">
                                        {val.score ?? val.rating}<span>/10</span>
                                    </div>
                                )}
                            </div>
                            {val.description && <p className="agent-report-description">{val.description}</p>}
                            {val.feedback && <p className="agent-report-description">{val.feedback}</p>}
                            <ValueRenderer value={val.comments} />
                        </div>
                    );
                }

                return (
                    <div key={key} className="agent-report-section">
                        <div className="agent-report-section-header"><h5>{title}</h5></div>
                        <ValueRenderer value={val} />
                    </div>
                );
            })}
        </div>
    );
}

function AnswerBadge({ answer }) {
    const normalized = (answer || '').toLowerCase();
    let className = 'badge pending';
    if (normalized === 'yes') className = 'badge pass';
    else if (normalized === 'no') className = 'badge fail';
    else if (normalized === 'uncertain') className = 'badge pending';

    return <span className={className}>{answer || '—'}</span>;
}

function QuestionCard({ item, showAskedAt = true }) {
    return (
        <div
            style={{
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: 14,
                padding: 14,
                marginBottom: 12,
                background: 'rgba(255,255,255,0.03)',
            }}
        >
            <div style={{ marginBottom: 8 }}>
                <strong>Q:</strong> {item.question_text}
            </div>

            <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap', marginBottom: 8 }}>
                <div><strong>Answer:</strong> <AnswerBadge answer={item.answer} /></div>
                {item.confidence != null && (
                    <div>
                        <strong>Confidence:</strong> {typeof item.confidence === 'number' ? item.confidence.toFixed(2) : item.confidence}
                    </div>
                )}
                {showAskedAt && item.asked_at && (
                    <div style={{ color: 'var(--text-muted)' }}>
                        {new Date(item.asked_at).toLocaleString()}
                    </div>
                )}
                {!showAskedAt && item.answered_at && (
                    <div style={{ color: 'var(--text-muted)' }}>
                        {new Date(item.answered_at).toLocaleString()}
                    </div>
                )}
            </div>

            {item.justification && (
                <div style={{ marginBottom: 8 }}>
                    <strong>Why:</strong> {item.justification}
                </div>
            )}

            {Array.isArray(item.evidence) && item.evidence.length > 0 && (
                <div>
                    <strong>Evidence:</strong>
                    <ul className="agent-report-comments" style={{ marginTop: 6 }}>
                        {item.evidence.map((ev, idx) => (
                            <li key={idx}>{ev}</li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}

export default function DetailModal({ submissionId, onClose }) {
    const [detail, setDetail] = useState(null);
    const [tab, setTab] = useState('Grader');

    const [askText, setAskText] = useState('');
    const [askLoading, setAskLoading] = useState(false);
    const [askError, setAskError] = useState('');
    const [askSuccess, setAskSuccess] = useState('');
    const [askHistory, setAskHistory] = useState([]);
    const [assignmentQuestionResults, setAssignmentQuestionResults] = useState([]);

    const loadQuestionData = async (id) => {
        try {
            const [history, assignmentResults] = await Promise.all([
                fetchSubmissionAskHistory(id),
                fetchSubmissionQuestions(id),
            ]);
            setAskHistory(history || []);
            setAssignmentQuestionResults(assignmentResults || []);
        } catch (err) {
            console.error('Failed to load question data', err);
        }
    };

    const pollAskHistory = async (id, attempts = 4) => {
        for (let i = 0; i < attempts; i++) {
            await new Promise(resolve => setTimeout(resolve, 1500));
            await loadQuestionData(id);
        }
    };

    useEffect(() => {
        fetchSubmission(submissionId).then(setDetail);
        loadQuestionData(submissionId);
    }, [submissionId]);

    const handleAskQuestion = async () => {
        if (!submissionId || !askText.trim()) return;

        try {
            setAskLoading(true);
            setAskError('');
            setAskSuccess('');
            await askSubmissionQuestion(submissionId, askText.trim());
            setAskSuccess('Question queued successfully. Fetching answer...');
            setAskText('');
            await pollAskHistory(submissionId);
            setAskSuccess('Answer received.');
        } catch (err) {
            setAskError(err.message || 'Failed to ask question');
        } finally {
            setAskLoading(false);
        }
    };

    if (!detail) return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal" onClick={e => e.stopPropagation()}>
                <div className="loading">Loading…</div>
            </div>
        </div>
    );

    const ev = detail.evaluation || {};
    const bd = ev.breakdown || {};

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal" onClick={e => e.stopPropagation()}>
                <div className="modal-header">
                    <div>
                        <h2>Submission #{detail.id}</h2>
                        <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: 2 }}>
                            Student: <strong>{detail.student_id}</strong> &nbsp;·&nbsp; {new Date(detail.submitted_at).toLocaleString()}
                        </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                        {ev.final_score != null && (
                            <span style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--accent2)' }}>
                                {ev.final_score?.toFixed(1)} <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>/10</span>
                            </span>
                        )}
                        <button className="modal-close" onClick={onClose}>✕</button>
                    </div>
                </div>

                <div className="modal-tabs">
                    {TABS.map(t => (
                        <button key={t} className={`tab-btn ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
                            {t}
                        </button>
                    ))}
                </div>

                <div className="modal-body">
                    {tab === 'Grader' && (
                        <>
                            <div className="report-section">
                                <h4>Score Breakdown</h4>
                                <div className="breakdown-grid">
                                    {['functionality', 'logic', 'efficiency', 'quality'].map(k => (
                                        <div className="breakdown-item" key={k}>
                                            <div className="label">{k.charAt(0).toUpperCase() + k.slice(1)}</div>
                                            <div className="val">{bd[k] != null ? bd[k].toFixed(1) : '—'}</div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                            <div className="report-section">
                                <h4>Final Verdict</h4>
                                <div className="report-value">{ev.final_verdict || 'No verdict yet'}</div>
                            </div>
                            <div className="report-section">
                                <h4>Penalties Applied</h4>
                                <div>
                                    {ev.penalties_applied?.length
                                        ? ev.penalties_applied.map((p, i) => <span key={i} className="penalty-tag">{p}</span>)
                                        : <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>None</span>
                                    }
                                </div>
                            </div>
                            <div className="report-section">
                                <h4>Test Cases</h4>
                                <div className="report-value">
                                    {(detail.execution_runs || []).map((r, i) => (
                                        <div key={i} style={{ marginBottom: 6 }}>
                                            <span style={{ color: r.status === 'success' ? 'var(--pass)' : 'var(--fail)', fontWeight: 600 }}>
                                                {r.test_case}:
                                            </span>{' '}
                                            exit={r.exit_code}
                                            {r.stderr ? <span style={{ color: 'var(--fail)' }}> ⚠ {r.stderr.slice(0, 120)}</span> : ''}
                                        </div>
                                    ))}
                                    {!detail.execution_runs?.length && <span style={{ color: 'var(--text-muted)' }}>No runs recorded</span>}
                                </div>
                            </div>
                        </>
                    )}

                    {tab === 'Logic' && (
                        <div className="report-section">
                            <h4>Logic & Functionality Report</h4>
                            <FormattedReport data={ev.logic_report} />
                        </div>
                    )}

                    {tab === 'Debugger' && (
                        <div className="report-section">
                            <h4>Static Analysis & Debugger Report</h4>
                            <FormattedReport data={ev.debugger_report} />
                        </div>
                    )}

                    {tab === 'Quality' && (
                        <div className="report-section">
                            <h4>Code Quality & Optimization Report</h4>
                            <FormattedReport data={ev.quality_report} />
                        </div>
                    )}

                    {tab === 'Q&A' && (
                        <>
                            <div className="report-section">
                                <h4>Ask a Question About This Submission</h4>
                                <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
                                    <input
                                        className="text-input"
                                        type="text"
                                        value={askText}
                                        onChange={(e) => setAskText(e.target.value)}
                                        placeholder="e.g. Does this code handle negative inputs correctly?"
                                        style={{ flex: 1 }}
                                    />
                                    <button
                                        className={`action-btn primary ${askLoading ? 'loading' : ''}`}
                                        onClick={handleAskQuestion}
                                        disabled={askLoading || !askText.trim()}
                                    >
                                        {askLoading ? 'Asking…' : 'Ask'}
                                    </button>
                                </div>

                                {askError && <div className="status-banner error">✗ {askError}</div>}
                                {askSuccess && <div className="status-banner success">✓ {askSuccess}</div>}
                            </div>

                            <div className="report-section">
                                <h4>Assignment Question Results</h4>
                                {assignmentQuestionResults.length === 0 ? (
                                    <div className="report-value" style={{ color: 'var(--text-muted)' }}>
                                        No assignment-level question results available yet.
                                    </div>
                                ) : (
                                    assignmentQuestionResults.map(item => (
                                        <QuestionCard key={item.id} item={item} showAskedAt={false} />
                                    ))
                                )}
                            </div>

                            <div className="report-section">
                                <h4>Ad-hoc Question History</h4>
                                {askHistory.length === 0 ? (
                                    <div className="report-value" style={{ color: 'var(--text-muted)' }}>
                                        No ad-hoc questions asked yet.
                                    </div>
                                ) : (
                                    askHistory.map(item => (
                                        <QuestionCard key={item.id} item={item} showAskedAt={true} />
                                    ))
                                )}
                            </div>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}