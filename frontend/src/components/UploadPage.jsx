import { useState, useCallback, useEffect } from 'react';

const API = 'http://localhost:8000';

// ── Single file drop-zone ──────────────────────────────────────────────────
function FileZone({ label, accept, file, onFile, hint }) {
    const [dragging, setDragging] = useState(false);

    const onDrop = useCallback((e) => {
        e.preventDefault();
        setDragging(false);
        const f = e.dataTransfer.files[0];
        if (f) onFile(f);
    }, [onFile]);

    const onDragOver = (e) => { e.preventDefault(); setDragging(true); };
    const onDragLeave = () => setDragging(false);

    return (
        <label
            className={`file-zone ${dragging ? 'dragging' : ''} ${file ? 'has-file' : ''}`}
            onDrop={onDrop}
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
        >
            <input
                type="file"
                accept={accept}
                style={{ display: 'none' }}
                onChange={e => e.target.files[0] && onFile(e.target.files[0])}
            />
            <div className="zone-icon">{file ? '✓' : '↑'}</div>
            <div className="zone-label">{label}</div>
            {file
                ? <div className="zone-file">{file.name}</div>
                : <div className="zone-hint">{hint || `Drag & drop or click`}</div>}
        </label>
    );
}

// ── Multi file drop-zone ───────────────────────────────────────────────────
function MultiFileZone({ label, accept, files, onFiles, hint }) {
    const [dragging, setDragging] = useState(false);

    const addFiles = (newFiles) => {
        onFiles(prev => {
            const merged = [...prev];
            for (const f of newFiles) {
                if (!merged.find(x => x.name === f.name)) merged.push(f);
            }
            return merged;
        });
    };

    const onDrop = useCallback((e) => {
        e.preventDefault();
        setDragging(false);
        addFiles([...e.dataTransfer.files]);
    }, []);

    const onDragOver = (e) => { e.preventDefault(); setDragging(true); };
    const onDragLeave = () => setDragging(false);

    return (
        <div>
            <label
                className={`file-zone ${dragging ? 'dragging' : ''} ${files.length > 0 ? 'has-file' : ''}`}
                onDrop={onDrop}
                onDragOver={onDragOver}
                onDragLeave={onDragLeave}
            >
                <input
                    type="file"
                    accept={accept}
                    multiple
                    style={{ display: 'none' }}
                    onChange={e => addFiles([...e.target.files])}
                />
                <div className="zone-icon">{files.length > 0 ? '✓' : '↑'}</div>
                <div className="zone-label">{label}</div>
                {files.length > 0
                    ? <div className="zone-file">{files.length} file{files.length > 1 ? 's' : ''} selected</div>
                    : <div className="zone-hint">{hint || 'Drag & drop or click (multiple allowed)'}</div>}
            </label>
            {files.length > 0 && (
                <div className="file-chips">
                    {files.map((f, i) => (
                        <div key={i} className="chip">
                            <span>{f.name}</span>
                            <button onClick={() => onFiles(prev => prev.filter((_, j) => j !== i))}>✕</button>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

// ── Main Upload Page ───────────────────────────────────────────────────────
export default function UploadPage() {
    const [assignments, setAssignments] = useState([]);
    const [selectedAssignmentId, setSelectedAssignmentId] = useState('');
    const [studentId, setStudentId] = useState('');
    const [codeFile, setCodeFile] = useState(null);
    const [assignmentFile, setAssignmentFile] = useState(null);
    const [testInputs, setTestInputs] = useState([]);
    const [expectedOutputs, setExpectedOutputs] = useState([]);
    const [status, setStatus] = useState(null); // null | 'loading' | 'success' | 'error'
    const [message, setMessage] = useState('');

    useEffect(() => {
        fetch(`${API}/assignments`)
            .then(res => res.json())
            .then(data => setAssignments(data))
            .catch(err => console.error('Failed to fetch assignments:', err));
    }, []);

    const isReady = studentId.trim() && codeFile && (selectedAssignmentId || (assignmentFile && testInputs.length > 0 && expectedOutputs.length > 0));

    async function handleSubmit(e) {
        e.preventDefault();
        if (!isReady) return;
        setStatus('loading');
        setMessage('');

        const form = new FormData();
        form.append('student_id', studentId.trim());
        form.append('code', codeFile);
        if (selectedAssignmentId) {
            form.append('assignment_id', selectedAssignmentId);
            // We still need to satisfy the multi-part form if it's strictly required by FastAPI
            // but the backend is updated to make them optional if assignment_id is present.
            // Wait, I should check if I made them optional in backend.
        } else {
            form.append('assignment', assignmentFile);
            testInputs.forEach(f => form.append('test_inputs', f));
            expectedOutputs.forEach(f => form.append('expected_outputs', f));
        }

        try {
            const res = await fetch(`${API}/evaluate`, { method: 'POST', body: form });
            const data = await res.json();
            if (res.status === 202) {
                setStatus('success');
                setMessage(data.message);
                // reset form
                setStudentId(''); setCodeFile(null); setAssignmentFile(null);
                setTestInputs([]); setExpectedOutputs([]);
            } else {
                throw new Error(data.detail || 'Submission failed');
            }
        } catch (err) {
            setStatus('error');
            setMessage(err.message);
        }
    }

    return (
        <>
            <div className="page-header">
                <h1>Upload & Evaluate</h1>
                <p>Upload student code, assignment description, test inputs, and expected outputs to start an evaluation.</p>
            </div>

            <form onSubmit={handleSubmit}>
                <div className="upload-grid">

                    {/* Assignment Selector */}
                    <div className="upload-section full-width">
                        <div className="upload-section-label">Link to Assignment</div>
                        <select
                            className="text-input"
                            value={selectedAssignmentId}
                            onChange={e => setSelectedAssignmentId(e.target.value)}
                        >
                            <option value="">-- Manual Upload (Upload files below) --</option>
                            {assignments.map(a => (
                                <option key={a.id} value={a.id}>{a.title}</option>
                            ))}
                        </select>
                    </div>

                    {/* Student ID */}
                    <div className="upload-section full-width">
                        <div className="upload-section-label">Student Identifier <span className="req">*</span></div>
                        <input
                            id="student-id-input"
                            className="text-input"
                            type="text"
                            placeholder="e.g. 2021CS10001 or Alice Smith"
                            value={studentId}
                            onChange={e => setStudentId(e.target.value)}
                        />
                    </div>

                    {/* Code */}
                    <div className="upload-section">
                        <div className="upload-section-label">Student Code <span className="req">*</span></div>
                        <FileZone
                            label="C Source File"
                            accept=".c"
                            file={codeFile}
                            onFile={setCodeFile}
                            hint="Drop a .c file here"
                        />
                    </div>

                    {!selectedAssignmentId && (
                        <>
                            {/* Assignment */}
                            <div className="upload-section">
                                <div className="upload-section-label">Assignment Description <span className="req">*</span></div>
                                <FileZone
                                    label="Assignment / Marking Scheme"
                                    accept=".txt,.md,.pdf"
                                    file={assignmentFile}
                                    onFile={setAssignmentFile}
                                    hint="Drop assignment.txt here"
                                />
                            </div>

                            {/* Test Inputs */}
                            <div className="upload-section">
                                <div className="upload-section-label">Test Inputs <span className="req">*</span></div>
                                <MultiFileZone
                                    label="Test Input Files"
                                    accept=".txt"
                                    files={testInputs}
                                    onFiles={setTestInputs}
                                    hint="Drop test1.txt, test2.txt … (order matters)"
                                />
                            </div>

                            {/* Expected Outputs */}
                            <div className="upload-section">
                                <div className="upload-section-label">Expected Outputs <span className="req">*</span></div>
                                <MultiFileZone
                                    label="Expected Output Files"
                                    accept=".txt"
                                    files={expectedOutputs}
                                    onFiles={setExpectedOutputs}
                                    hint="Drop expected1.txt, expected2.txt … (same order as inputs)"
                                />
                            </div>
                        </>
                    )}

                </div>

                {/* Validation hint */}
                {!isReady && (
                    <div className="upload-hint">
                        Fill all fields and attach at least one test input + one expected output to submit.
                    </div>
                )}

                {/* Status banner */}
                {status === 'success' && (
                    <div className="status-banner success">
                        {message}
                    </div>
                )}
                {status === 'error' && (
                    <div className="status-banner error">
                        {message}
                    </div>
                )}

                <button
                    id="evaluate-submit-btn"
                    type="submit"
                    className={`submit-btn ${status === 'loading' ? 'loading' : ''}`}
                    disabled={!isReady || status === 'loading'}
                >
                    {status === 'loading' ? (
                        <><span className="spinner" /> Evaluating…</>
                    ) : (
                        '⚡ Start Evaluation'
                    )}
                </button>
            </form>
        </>
    );
}
