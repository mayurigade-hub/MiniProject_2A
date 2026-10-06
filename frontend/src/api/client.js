const API_BASE = '/api';

export async function fetchLectures() {
  const res = await fetch(`${API_BASE}/lectures`);
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Failed to fetch catalog');
  }
  return res.json();
}

export async function fetchLectureDetails(id) {
  const res = await fetch(`${API_BASE}/lectures/${id}`);
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Failed to fetch lecture details');
  }
  return res.json();
}

export async function fetchLectureMetadata(id) {
  const res = await fetch(`${API_BASE}/lectures/${id}/metadata`);
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Failed to fetch lecture metadata');
  }
  return res.json();
}

export async function uploadLecture(formData) {
  const res = await fetch(`${API_BASE}/lectures/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Upload failed with status ${res.status}`);
  }
  return res.json();
}

export async function checkLectureStatus(id) {
  const res = await fetch(`${API_BASE}/lectures/${id}/status`);
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Status check failed');
  }
  return res.json();
}

export async function generateLectureLanguages(id) {
  const res = await fetch(`${API_BASE}/lectures/${id}/languages`, { method: 'POST' });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Could not generate additional audio-description languages');
  }
  return res.json();
}
