import { useState, useEffect, useCallback } from 'react';
import { fetchStudents, deleteStudent, uploadStudentCSV } from '../api';

export default function StudentsPage() {
    const [students, setStudents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [showCSV, setShowCSV] = useState(false);
    const [deleting, setDeleting] = useState(null);
    const [toast, setToast] = useState(null);

    const load = useCallback(() => {
        setLoading(true);
        fetchStudents().then(data => { setStudents(data); setLoading(false); });
    }, []);

    useEffect(load, [load]);

    const showToast = (msg, type = 'success') => {
        setToast({ msg, type });
        setTimeout(() => setToast(null), 3500);
    };

    const handleDelete = async (rollNumber) => {
        if (!confirm(`Delete student ${rollNumber} and all their submissions?`)) return;
        setDeleting(rollNumber);
        try {
            await deleteStudent(rollNumber);
            showToast(`Student ${rollNumber} deleted successfully.`);
            load();
        } catch (err) {
            showToast(err.message, 'error');
        }
        setDeleting(null);
    };

    const filtered = students.filter(s =>
        s.roll_number.toLowerCase().includes(search.toLowerCase()) ||
        (s.name || '').toLowerCase().includes(search.toLowerCase())
    );

    return (
        <>
            <div className="page-header">
                <h1>Students</h1>
                <p>Manage student profiles and import names via CSV.</p>
            </div>

            <div className="students-toolbar">
                <div className="search-wrapper">
                    <span className="search-icon">⌕</span>
                    <input
                        className="text-input search-input"
                        type="text"
                        placeholder="Search by roll number or name…"
                        value={search}
                        onChange={e => setSearch(e.target.value)}
                    />
                </div>
                <div style={{ display: 'flex', gap: 10 }}>
                    <button className="action-btn primary" onClick={() => setShowCSV(true)}>
                        ↑ Import CSV
                    </button>
                </div>
            </div>

            {loading ? (
                <div className="loading">Loading students…</div>
            ) : filtered.length === 0 ? (
                <div className="empty-state">
                    <div className="empty-icon">👤</div>
                    <h3>{search ? 'No matching students' : 'No students yet'}</h3>
                    <p>{search ? 'Try a different search term.' : 'Students are created automatically during bulk upload.'}</p>
                </div>
            ) : (
                <div className="table-card">
                    <div className="table-header">
                        <h3>Student Profiles</h3>
                        <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                            {filtered.length} of {students.length}
                        </span>
                    </div>
                    <table>
                        <thead>
                            <tr>
                                <th>Roll Number</th>
                                <th>Name</th>
                                <th>Registered</th>
                                <th style={{ textAlign: 'right' }}>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filtered.map(s => (
                                <tr key={s.id}>
                                    <td style={{ fontWeight: 600, fontFamily: "'JetBrains Mono', monospace" }}>
                                        {s.roll_number}
                                    </td>
                                    <td>
                                        {s.name || <span style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>Not set</span>}
                                    </td>
                                    <td style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                                        {new Date(s.created_at).toLocaleDateString()}
                                    </td>
                                    <td style={{ textAlign: 'right' }}>
                                        <button
                                            className="action-btn danger tiny"
                                            onClick={() => handleDelete(s.roll_number)}
                                            disabled={deleting === s.roll_number}
                                            title="Delete student & all submissions"
                                        >
                                            {deleting === s.roll_number ? '…' : '🗑'}
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {showCSV && (
                <CSVUploadModal
                    onClose={() => setShowCSV(false)}
                    onDone={() => { setShowCSV(false); load(); }}
                    showToast={showToast}
                />
            )}

            {toast && (
                <div className={`toast ${toast.type}`}>
                    {toast.type === 'success' ? '✓' : '✗'} {toast.msg}
                </div>
            )}
        </>
    );
}


/* ═══════════════════════  CSV UPLOAD MODAL  ════════════════════════════════ */

function CSVUploadModal({ onClose, onDone, showToast }) {
    const [csvFile, setCsvFile] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [result, setResult] = useState(null);

    const handleUpload = async () => {
        if (!csvFile) return;
        setUploading(true);
        try {
            const form = new FormData();
            form.append('csv_file', csvFile);
            const res = await uploadStudentCSV(form);
            setResult(res);
            showToast(`Updated ${res.updated} students, created ${res.created} new profiles.`);
        } catch (err) {
            showToast(err.message, 'error');
        }
        setUploading(false);
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 520 }}>
                <div className="modal-header">
                    <h2>Import Student Names</h2>
                    <button className="modal-close" onClick={onClose}>✕</button>
                </div>

                <div className="modal-body">
                    <div className="bulk-upload-info">
                        <p>Upload a CSV file with two columns to set student names:</p>
                        <div className="code-block">
                            roll_number,name<br />
                            2021001,Alice Johnson<br />
                            2021002,Bob Smith<br />
                            2021003,Charlie Brown
                        </div>
                    </div>

                    <label className={`file-zone ${csvFile ? 'has-file' : ''}`}>
                        <input
                            type="file"
                            accept=".csv"
                            style={{ display: 'none' }}
                            onChange={e => e.target.files[0] && setCsvFile(e.target.files[0])}
                        />
                        <div className="zone-icon">{csvFile ? '✓' : '↑'}</div>
                        <div className="zone-label">CSV File</div>
                        {csvFile
                            ? <div className="zone-file">{csvFile.name}</div>
                            : <div className="zone-hint">Drag & drop or click to select</div>
                        }
                    </label>

                    {result && (
                        <div className="status-banner success" style={{ marginTop: 16 }}>
                            ✓ Processed {result.total_processed} rows — {result.created} created, {result.updated} updated.
                        </div>
                    )}

                    <div style={{ display: 'flex', gap: 10, marginTop: 16 }}>
                        <button
                            className={`submit-btn ${uploading ? 'loading' : ''}`}
                            onClick={handleUpload}
                            disabled={!csvFile || uploading}
                            style={{ flex: 1, justifyContent: 'center' }}
                        >
                            {uploading ? <><span className="spinner" /> Importing…</> : '↑ Import CSV'}
                        </button>
                        {result && (
                            <button className="action-btn" onClick={onDone} style={{ padding: '13px 28px' }}>
                                Done
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
