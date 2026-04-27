const API = 'http://localhost:8000';

async function parseResponse(response, fallbackMessage) {
  if (!response.ok) {
    let errorMessage = fallbackMessage;
    try {
      const error = await response.json();
      errorMessage = error.detail || fallbackMessage;
    } catch {
      // keep fallback message
    }
    throw new Error(errorMessage);
  }

  return response.json();
}

async function get(path, fallbackMessage = 'Request failed') {
  const response = await fetch(`${API}${path}`);
  return parseResponse(response, fallbackMessage);
}

async function del(path, fallbackMessage = 'Delete failed') {
  const response = await fetch(`${API}${path}`, {
    method: 'DELETE',
  });
  return parseResponse(response, fallbackMessage);
}

async function postJson(path, body, fallbackMessage = 'Request failed') {
  const response = await fetch(`${API}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return parseResponse(response, fallbackMessage);
}

async function postForm(path, formData, fallbackMessage = 'Request failed') {
  const response = await fetch(`${API}${path}`, {
    method: 'POST',
    body: formData,
  });
  return parseResponse(response, fallbackMessage);
}

// ── Original endpoints ──────────────────────────────────────────────────────

export const fetchAnalytics = () =>
  get('/analytics', 'Failed to fetch analytics');

export const fetchSubmissions = () =>
  get('/submissions', 'Failed to fetch submissions');

export const fetchSubmission = (id) =>
  get(`/submissions/${id}`, 'Failed to fetch submission');

// ── Assignments ─────────────────────────────────────────────────────────────

export const fetchAssignments = () =>
  get('/assignments', 'Failed to fetch assignments');

export const fetchAssignment = (id) =>
  get(`/assignments/${id}`, 'Failed to fetch assignment');

export const createAssignment = (data) =>
  postJson('/assignments', data, 'Failed to create assignment');

export const createAssignmentUpload = (formData) =>
  postForm('/assignments/upload', formData, 'Failed to create assignment');

export const uploadBulkZip = (assignmentId, formData) =>
  postForm(`/assignments/${assignmentId}/upload-bulk`, formData, 'Bulk upload failed');

export const deleteAssignment = (id) =>
  del(`/assignments/${id}/delete`, 'Delete assignment failed');

export const fetchAssignmentSubmissions = (assignmentId) =>
  get(`/assignments/${assignmentId}/submissions`, 'Failed to fetch assignment submissions');

export const fetchAssignmentDashboard = (assignmentId) =>
  get(`/assignments/${assignmentId}/dashboard`, 'Failed to fetch assignment dashboard');

export const fetchAssignmentAnalytics = (assignmentId) =>
  get(`/assignments/${assignmentId}/analytics`, 'Failed to fetch assignment analytics');

// ── Students ────────────────────────────────────────────────────────────────

export const fetchStudents = () =>
  get('/students', 'Failed to fetch students');

export const deleteStudent = (rollNumber) =>
  del(`/students/${rollNumber}/delete`, 'Delete student failed');

export const uploadStudentCSV = (formData) =>
  postForm('/students/upload-csv', formData, 'CSV upload failed');

// ── Evaluation ──────────────────────────────────────────────────────────────

export const triggerEvaluation = (submissionId) =>
  postJson(`/evaluate/individual/${submissionId}`, {}, 'Evaluation trigger failed');

export const reEvaluateAssignment = (assignmentId) =>
  postJson(`/assignments/${assignmentId}/re-evaluate`, {}, 'Re-evaluation trigger failed');

export const deleteSubmission = (id) =>
  del(`/submissions/${id}/delete`, 'Delete submission failed');

export const fetchJobStatus = (jobId) =>
  get(`/jobs/${jobId}`, 'Failed to fetch job status');

// ── Plagiarism ──────────────────────────────────────────────────────────────

export const triggerPlagiarismCheck = (assignmentId) =>
  postJson(`/assignments/${assignmentId}/run-plagiarism`, {}, 'Plagiarism check failed');

export const fetchPlagiarismResults = (assignmentId) =>
  get(`/assignments/${assignmentId}/plagiarism`, 'Failed to fetch plagiarism results');

export const compareTwoFiles = (code1, code2) =>
  postJson('/plagiarism/compare', { code1, code2 }, 'Failed to compare files');

// ── Questions ───────────────────────────────────────────────────────────────

export const fetchAssignmentQuestions = (assignmentId) =>
  get(`/assignments/${assignmentId}/questions`, 'Failed to fetch assignment questions');

export const createAssignmentQuestion = (assignmentId, questionText) =>
  postJson(
    `/assignments/${assignmentId}/questions`,
    { question_text: questionText },
    'Failed to create question'
  );

export const askSubmissionQuestion = (submissionId, questionText) =>
  postJson(
    `/submissions/${submissionId}/ask`,
    { question_text: questionText },
    'Failed to ask question'
  );

export const fetchSubmissionAskHistory = (submissionId) =>
  get(`/submissions/${submissionId}/ask-history`, 'Failed to fetch ask history');

export const fetchSubmissionQuestions = (submissionId) =>
  get(`/submissions/${submissionId}/questions`, 'Failed to fetch submission questions');