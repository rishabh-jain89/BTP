import { useState, useEffect } from 'react';
import {
    fetchAssignments,
    fetchAssignment,
    createAssignment,
    uploadBulkZip,
    deleteAssignment,
    deleteSubmission,
    fetchAssignmentSubmissions,
    triggerEvaluation,
    triggerPlagiarismCheck,
    fetchPlagiarismResults,
    fetchAssignmentQuestions,
    createAssignmentQuestion,
} from '../api';
import DetailModal from './DetailModal';

/* ═══════════════════════════════  MAIN PAGE  ═══════════════════════════════ */

export default function AssignmentsPage() {
    const [assignments, setAssignments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showCreate, setShowCreate] = useState(false);
    const [selectedAssignment, setSelectedAssignment] = useState(null);

    const load = () => {
        setLoading(true);
        fetchAssignments()
            .then(data => setAssignments(data))
            .finally(() => setLoading(false));
    };

    useEffect(() => {
        load();
    }, []);

    const handleDeleteAssignment = async (id, e) => {
        e.stopPropagation();
        if (!confirm('Are you sure you want to delete this assignment and ALL its submissions? This cannot be undone.')) return;
        try {
            await deleteAssignment(id);
            load();
        } catch (err) {
            alert(err.message);
        }
    };

    return (
        <>
            <div className="page-header">
                <h1>Assignments</h1>
                <p>Create assignments, manage test cases, upload submissions, and configure assignment-level questions.</p>
            </div>

            <div style={{ display: 'flex', gap: 12, marginBottom: 24 }}>
                <button className="action-btn primary" onClick={() => setShowCreate(true)}>
                    + New Assignment
                </button>
            </div>

            {loading ? (
                <div className="loading">Loading assignments…</div>
            ) : assignments.length === 0 ? (
                <div className="empty-state">
                    <div className="empty-icon">📋</div>
                    <h3>No assignments yet</h3>
                    <p>Create your first assignment to get started.</p>
                </div>
            ) : (
                <div className="assignments-grid">
                    {assignments.map(a => (
                        <AssignmentCard
                            key={a.id}
                            assignment={a}
                            onClick={() => setSelectedAssignment(a.id)}
                            onDelete={(e) => handleDeleteAssignment(a.id, e)}
                        />
                    ))}
                </div>
            )}

            {showCreate && (
                <CreateAssignmentModal
                    onClose={() => setShowCreate(false)}
                    onCreated={() => {
                        setShowCreate(false);
                        load();
                    }}
                />
            )}

            {selectedAssignment && (
                <AssignmentDetailModal
                    assignmentId={selectedAssignment}
                    onClose={() => setSelectedAssignment(null)}
                    onRefresh={load}
                />
            )}
        </>
    );
}


/* ═══════════════════════════  ASSIGNMENT CARD  ═════════════════════════════ */

function AssignmentCard({ assignment, onClick, onDelete }) {
    return (
        <div className="assignment-card" onClick={onClick}>
            <div className="assignment-card-header">
                <div className="assignment-card-id">#{assignment.id}</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div className="assignment-card-date">
                        {new Date(assignment.created_at).toLocaleDateString()}
                    </div>
                    <button className="action-btn danger tiny" onClick={onDelete} title="Delete Assignment">
                        🗑
                    </button>
                </div>
            </div>
            <h3 className="assignment-card-title">{assignment.title}</h3>
            <div className="assignment-card-stats">
                <div className="stat">
                    <span className="stat-value">{assignment.test_case_count}</span>
                    <span className="stat-label">Test Cases</span>
                </div>
                <div className="stat">
                    <span className="stat-value">{assignment.submission_count}</span>
                    <span className="stat-label">Submissions</span>
                </div>
            </div>
        </div>
    );
}


/* ═══════════════════════  CREATE ASSIGNMENT MODAL  ═════════════════════════ */

function CreateAssignmentModal({ onClose, onCreated }) {
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [testCases, setTestCases] = useState([{ input_text: '', expected_output: '' }]);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');

    const addTestCase = () => setTestCases(prev => [...prev, { input_text: '', expected_output: '' }]);
    const removeTestCase = (i) => setTestCases(prev => prev.filter((_, j) => j !== i));
    const updateTestCase = (i, field, val) => {
        setTestCases(prev => prev.map((tc, j) => (j === i ? { ...tc, [field]: val } : tc)));
    };

    const isValid = title.trim() && testCases.every(tc => tc.input_text.trim() && tc.expected_output.trim());

    async function handleSubmit(e) {
        e.preventDefault();
        if (!isValid) return;
        setSaving(true);
        setError('');

        try {
            await createAssignment({
                title: title.trim(),
                description: description.trim() || null,
                test_cases: testCases,
            });
            onCreated();
        } catch (err) {
            setError(err.message);
            setSaving(false);
        }
    }

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal wide-modal" onClick={e => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>Create New Assignment</h2>
                    <button className="modal-close" onClick={onClose}>✕</button>
                </div>

                <form className="modal-body" onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label className="form-label">Title <span className="req">*</span></label>
                        <input
                            className="text-input"
                            type="text"
                            placeholder="e.g. Linked List Operations"
                            value={title}
                            onChange={e => setTitle(e.target.value)}
                            autoFocus
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label">Description</label>
                        <textarea
                            className="text-input textarea"
                            placeholder="Assignment description, problem statement, marking scheme…"
                            value={description}
                            onChange={e => setDescription(e.target.value)}
                            rows={4}
                        />
                    </div>

                    <div className="form-group">
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <label className="form-label">Test Cases <span className="req">*</span></label>
                            <button type="button" className="action-btn small" onClick={addTestCase}>
                                + Add Test Case
                            </button>
                        </div>

                        <div className="test-cases-list">
                            {testCases.map((tc, i) => (
                                <div className="test-case-row" key={i}>
                                    <div className="test-case-number">#{i + 1}</div>
                                    <div className="test-case-fields">
                                        <textarea
                                            className="text-input tc-input"
                                            placeholder="Input string"
                                            value={tc.input_text}
                                            onChange={e => updateTestCase(i, 'input_text', e.target.value)}
                                            rows={2}
                                        />
                                        <textarea
                                            className="text-input tc-input"
                                            placeholder="Expected output"
                                            value={tc.expected_output}
                                            onChange={e => updateTestCase(i, 'expected_output', e.target.value)}
                                            rows={2}
                                        />
                                    </div>
                                    {testCases.length > 1 && (
                                        <button type="button" className="remove-tc-btn" onClick={() => removeTestCase(i)}>✕</button>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>

                    {error && <div className="status-banner error">✗ {error}</div>}

                    <button
                        type="submit"
                        className={`submit-btn ${saving ? 'loading' : ''}`}
                        disabled={!isValid || saving}
                        style={{ width: '100%', justifyContent: 'center' }}
                    >
                        {saving ? <><span className="spinner" /> Creating…</> : '✓ Create Assignment'}
                    </button>
                </form>
            </div>
        </div>
    );
}


/* ═══════════════════  ASSIGNMENT DETAIL MODAL  ═════════════════════════════ */

function AssignmentDetailModal({ assignmentId, onClose, onRefresh }) {
    const [assignment, setAssignment] = useState(null);
    const [submissions, setSubmissions] = useState(null);
    const [tab, setTab] = useState('details');
    const [zipFile, setZipFile] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [uploadResult, setUploadResult] = useState(null);
    const [evalStatus, setEvalStatus] = useState({});
    const [selectedSubmission, setSelectedSubmission] = useState(null);
    const [plagiarismData, setPlagiarismData] = useState(null);
    const [plagiarismRunning, setPlagiarismRunning] = useState(false);

    const [questions, setQuestions] = useState([]);
    const [questionsLoading, setQuestionsLoading] = useState(false);
    const [questionText, setQuestionText] = useState('');
    const [questionSaving, setQuestionSaving] = useState(false);
    const [questionError, setQuestionError] = useState('');

    const loadAssignment = async () => {
        const data = await fetchAssignment(assignmentId);
        setAssignment(data);
    };

    const loadSubmissions = async () => {
        const data = await fetchAssignmentSubmissions(assignmentId);
        setSubmissions(data);
    };

    const loadPlagiarism = async () => {
        try {
            const data = await fetchPlagiarismResults(assignmentId);
            setPlagiarismData(data);
        } catch {
            setPlagiarismData(null);
        }
    };

    const loadQuestions = async () => {
        try {
            setQuestionsLoading(true);
            setQuestionError('');
            const data = await fetchAssignmentQuestions(assignmentId);
            setQuestions(data);
        } catch (err) {
            setQuestionError(err.message || 'Failed to load questions');
        } finally {
            setQuestionsLoading(false);
        }
    };

    useEffect(() => {
        loadAssignment();
        loadSubmissions();
        loadPlagiarism();
        loadQuestions();
    }, [assignmentId]);

    const handleRunPlagiarism = async () => {
        setPlagiarismRunning(true);
        try {
            await triggerPlagiarismCheck(assignmentId);
            setTimeout(async () => {
                const pollInterval = setInterval(async () => {
                    try {
                        const data = await fetchPlagiarismResults(assignmentId);
                        if (data.total_results > 0) {
                            setPlagiarismData(data);
                            setPlagiarismRunning(false);
                            clearInterval(pollInterval);
                        }
                    } catch {
                        // keep polling
                    }
                }, 3000);

                setTimeout(() => {
                    clearInterval(pollInterval);
                    setPlagiarismRunning(false);
                }, 120000);
            }, 2000);
        } catch (err) {
            alert(err.message);
            setPlagiarismRunning(false);
        }
    };

    const handleBulkUpload = async () => {
        if (!zipFile) return;
        setUploading(true);
        setUploadResult(null);
        try {
            const form = new FormData();
            form.append('zip_file', zipFile);
            const result = await uploadBulkZip(assignmentId, form);
            setUploadResult(result);
            setZipFile(null);
            await loadSubmissions();
            onRefresh();
        } catch (err) {
            setUploadResult({ errors: [err.message] });
        }
        setUploading(false);
    };

    const handleTriggerEval = async (submissionId) => {
        setEvalStatus(prev => ({ ...prev, [submissionId]: 'queuing' }));
        try {
            await triggerEvaluation(submissionId);
            setEvalStatus(prev => ({ ...prev, [submissionId]: 'queued' }));
            await loadSubmissions();
        } catch {
            setEvalStatus(prev => ({ ...prev, [submissionId]: 'error' }));
        }
    };

    const handleDeleteSubmission = async (submissionId, e) => {
        e.stopPropagation();
        if (!confirm('Delete this submission and its evaluation data?')) return;
        try {
            await deleteSubmission(submissionId);
            await loadSubmissions();
            onRefresh();
        } catch (err) {
            alert(err.message);
        }
    };

    const handleAddQuestion = async () => {
        if (!questionText.trim()) return;

        try {
            setQuestionSaving(true);
            setQuestionError('');
            await createAssignmentQuestion(assignmentId, questionText.trim());
            setQuestionText('');
            await loadQuestions();
        } catch (err) {
            setQuestionError(err.message || 'Failed to add question');
        } finally {
            setQuestionSaving(false);
        }
    };

    if (!assignment) {
        return (
            <div className="modal-overlay" onClick={onClose}>
                <div className="modal wide-modal" onClick={e => e.stopPropagation()}>
                    <div className="loading">Loading…</div>
                </div>
            </div>
        );
    }

    return (
        <>
            <div className="modal-overlay" onClick={onClose}>
                <div className="modal wide-modal" onClick={e => e.stopPropagation()}>
                    <div className="modal-header">
                        <div>
                            <h2>{assignment.title}</h2>
                            <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: 2 }}>
                                Assignment #{assignment.id} · {new Date(assignment.created_at).toLocaleDateString()}
                            </div>
                        </div>
                        <button className="modal-close" onClick={onClose}>✕</button>
                    </div>

                    <div className="modal-tabs">
                        {['details', 'questions', 'submissions', 'upload', 'plagiarism'].map(t => (
                            <button
                                key={t}
                                className={`tab-btn ${tab === t ? 'active' : ''}`}
                                onClick={() => setTab(t)}
                            >
                                {t === 'details'
                                    ? 'Details'
                                    : t === 'questions'
                                    ? 'Questions'
                                    : t === 'submissions'
                                    ? 'Submissions'
                                    : t === 'upload'
                                    ? 'Bulk Upload'
                                    : 'Plagiarism'}
                            </button>
                        ))}
                    </div>

                    <div className="modal-body">
                        {tab === 'details' && (
                            <>
                                {assignment.description && (
                                    <div className="report-section">
                                        <h4>Description</h4>
                                        <div className="report-value">{assignment.description}</div>
                                    </div>
                                )}
                                <div className="report-section">
                                    <h4>Test Cases ({assignment.test_cases.length})</h4>
                                    <div className="test-cases-display">
                                        {assignment.test_cases.map((tc, i) => (
                                            <div className="test-case-display-row" key={tc.id}>
                                                <div className="tc-display-header">Test Case #{i + 1}</div>
                                                <div className="tc-display-grid">
                                                    <div>
                                                        <div className="tc-display-label">Input</div>
                                                        <div className="tc-display-value">{tc.input_text}</div>
                                                    </div>
                                                    <div>
                                                        <div className="tc-display-label">Expected Output</div>
                                                        <div className="tc-display-value">{tc.expected_output}</div>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </>
                        )}

                        {tab === 'questions' && (
                            <div className="report-section">
                                <h4>Assignment Questions</h4>
                                <p style={{ color: 'var(--text-muted)', marginTop: 0 }}>
                                    Add reusable questions that teachers may want to ask about submissions for this assignment.
                                </p>

                                <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
                                    <input
                                        className="text-input"
                                        type="text"
                                        value={questionText}
                                        onChange={(e) => setQuestionText(e.target.value)}
                                        placeholder="e.g. Does the code handle negative inputs?"
                                        style={{ flex: 1 }}
                                    />
                                    <button
                                        className={`action-btn primary ${questionSaving ? 'loading' : ''}`}
                                        onClick={handleAddQuestion}
                                        disabled={questionSaving || !questionText.trim()}
                                    >
                                        {questionSaving ? 'Adding…' : 'Add Question'}
                                    </button>
                                </div>

                                {questionError && (
                                    <div className="status-banner error" style={{ marginBottom: 12 }}>
                                        ✗ {questionError}
                                    </div>
                                )}

                                {questionsLoading ? (
                                    <div className="loading">Loading questions…</div>
                                ) : questions.length === 0 ? (
                                    <div className="empty-state small">
                                        <p>No assignment questions added yet.</p>
                                    </div>
                                ) : (
                                    <div className="test-cases-display">
                                        {questions.map((q, index) => (
                                            <div className="test-case-display-row" key={q.id}>
                                                <div className="tc-display-header">Question #{index + 1}</div>
                                                <div className="tc-display-value">{q.question_text}</div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}

                        {tab === 'submissions' && (
                            <>
                                {!submissions ? (
                                    <div className="loading">Loading submissions…</div>
                                ) : submissions.submissions?.length === 0 ? (
                                    <div className="empty-state small">
                                        <p>No submissions yet. Use Bulk Upload to add student code.</p>
                                    </div>
                                ) : (
                                    <div className="table-card">
                                        <div className="table-header">
                                            <h3>Student Submissions</h3>
                                            <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                                                {submissions.total} total
                                            </span>
                                        </div>
                                        <table>
                                            <thead>
                                                <tr>
                                                    <th>#</th>
                                                    <th>Student</th>
                                                    <th>Score</th>
                                                    <th>Status</th>
                                                    <th>Actions</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {submissions.submissions.map(s => {
                                                    const rawStatus = s.status || 'pending';
                                                    const badgeClass =
                                                        rawStatus === 'evaluated'
                                                            ? (s.final_score >= 5 ? 'pass' : 'fail')
                                                            : rawStatus === 'failed'
                                                            ? 'fail'
                                                            : 'pending';

                                                    const badgeLabel =
                                                        rawStatus === 'evaluated'
                                                            ? (s.final_score >= 5 ? 'Pass' : 'Fail')
                                                            : rawStatus === 'queued'
                                                            ? 'Queued'
                                                            : rawStatus === 'running'
                                                            ? 'Running'
                                                            : rawStatus === 'failed'
                                                            ? 'Failed'
                                                            : 'Pending';

                                                    return (
                                                        <tr key={s.id}>
                                                            <td style={{ color: 'var(--text-muted)' }}>{s.id}</td>
                                                            <td style={{ fontWeight: 600 }}>{s.student_id}</td>
                                                            <td>
                                                                {s.final_score != null
                                                                    ? <span style={{ color: 'var(--accent2)', fontWeight: 600 }}>{s.final_score.toFixed(1)}/10</span>
                                                                    : <span style={{ color: 'var(--text-muted)' }}>—</span>
                                                                }
                                                            </td>
                                                            <td>
                                                                <span className={`badge ${badgeClass}`}>
                                                                    {badgeLabel}
                                                                </span>
                                                            </td>
                                                            <td>
                                                                <div style={{ display: 'flex', gap: 6 }}>
                                                                    <button
                                                                        className="action-btn tiny"
                                                                        onClick={(e) => {
                                                                            e.stopPropagation();
                                                                            setSelectedSubmission(s.id);
                                                                        }}
                                                                        title="View details"
                                                                    >
                                                                        👁
                                                                    </button>
                                                                    {(rawStatus === 'pending' || rawStatus === 'failed') && (
                                                                        <button
                                                                            className={`action-btn tiny eval ${evalStatus[s.id] === 'queuing' ? 'loading' : ''}`}
                                                                            onClick={(e) => {
                                                                                e.stopPropagation();
                                                                                handleTriggerEval(s.id);
                                                                            }}
                                                                            disabled={evalStatus[s.id] === 'queuing' || evalStatus[s.id] === 'queued'}
                                                                            title="Trigger evaluation"
                                                                        >
                                                                            {evalStatus[s.id] === 'queued'
                                                                                ? '✓'
                                                                                : evalStatus[s.id] === 'queuing'
                                                                                ? '…'
                                                                                : '⚡'}
                                                                        </button>
                                                                    )}
                                                                    <button
                                                                        className="action-btn tiny danger"
                                                                        onClick={(e) => handleDeleteSubmission(s.id, e)}
                                                                        title="Delete submission"
                                                                    >
                                                                        🗑
                                                                    </button>
                                                                </div>
                                                            </td>
                                                        </tr>
                                                    );
                                                })}
                                            </tbody>
                                        </table>
                                    </div>
                                )}
                            </>
                        )}

                        {tab === 'upload' && (
                            <div className="bulk-upload-section">
                                <div className="bulk-upload-info">
                                    <h4>Bulk Upload Student Submissions</h4>
                                    <p>Upload a <code>.zip</code> file containing student code files. Expected format:</p>
                                    <div className="code-block">
                                        submissions.zip<br />
                                        ├── 2021001.c<br />
                                        ├── 2021002.c<br />
                                        └── 2021003.c
                                    </div>
                                    <p>Each <code>.c</code> filename (without extension) is the student's roll number.</p>
                                </div>

                                <label className={`file-zone ${zipFile ? 'has-file' : ''}`}>
                                    <input
                                        type="file"
                                        accept=".zip"
                                        style={{ display: 'none' }}
                                        onChange={e => e.target.files[0] && setZipFile(e.target.files[0])}
                                    />
                                    <div className="zone-icon">{zipFile ? '✓' : '↑'}</div>
                                    <div className="zone-label">ZIP File</div>
                                    {zipFile
                                        ? <div className="zone-file">{zipFile.name}</div>
                                        : <div className="zone-hint">Drag & drop or click to select</div>
                                    }
                                </label>

                                {uploadResult && (
                                    <div className={`status-banner ${uploadResult.errors?.length && !uploadResult.submissions_created ? 'error' : 'success'}`}>
                                        {uploadResult.submissions_created != null
                                            ? `✓ ${uploadResult.submissions_created} submissions created from ${uploadResult.total_extracted} files.`
                                            : ''}
                                        {uploadResult.errors?.length > 0 && (
                                            <div style={{ marginTop: 6, fontSize: '0.82rem' }}>
                                                {uploadResult.errors.map((e, i) => <div key={i}>⚠ {e}</div>)}
                                            </div>
                                        )}
                                    </div>
                                )}

                                <button
                                    className={`submit-btn ${uploading ? 'loading' : ''}`}
                                    onClick={handleBulkUpload}
                                    disabled={!zipFile || uploading}
                                    style={{ width: '100%', justifyContent: 'center', marginTop: 16 }}
                                >
                                    {uploading ? <><span className="spinner" /> Uploading…</> : '📦 Upload & Process ZIP'}
                                </button>
                            </div>
                        )}

                        {tab === 'plagiarism' && (
                            <div className="plagiarism-section">
                                <div className="plagiarism-header">
                                    <div>
                                        <h4>Plagiarism Analysis</h4>
                                        <p className="plagiarism-subtitle">
                                            Detect code similarity between student submissions.
                                        </p>
                                    </div>
                                    <button
                                        className={`action-btn primary ${plagiarismRunning ? 'loading' : ''}`}
                                        onClick={handleRunPlagiarism}
                                        disabled={plagiarismRunning || (submissions?.submissions?.length || 0) < 2}
                                    >
                                        {plagiarismRunning ? <><span className="spinner" /> Analyzing…</> : 'Run Plagiarism Check'}
                                    </button>
                                </div>

                                {(submissions?.submissions?.length || 0) < 2 && (
                                    <div className="status-banner error">
                                        ⚠ At least 2 submissions are required for plagiarism detection.
                                    </div>
                                )}

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

                                        <div className="table-card">
                                            <div className="table-header">
                                                <h3>Similarity Results</h3>
                                                <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                                                    Sorted by highest similarity
                                                </span>
                                            </div>
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
                                    <div className="empty-state small">
                                        <div className="empty-icon">🔍</div>
                                        <h3>No plagiarism data</h3>
                                        <p>Run a plagiarism check to analyze code similarity between submissions.</p>
                                    </div>
                                ) : null}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {selectedSubmission && (
                <DetailModal
                    submissionId={selectedSubmission}
                    onClose={() => setSelectedSubmission(null)}
                />
            )}
        </>
    );
}