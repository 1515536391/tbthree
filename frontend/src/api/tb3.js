import client from './client';

export const api = {
  health: () => client.get('/health'),
  accounts: () => client.get('/accounts'),

  edges: () => client.get('/edges'),
  edge: (addr) => client.get(`/edges/${addr}`),

  tasks: () => client.get('/tasks'),
  task: (taskId) => client.get(`/tasks/${taskId}`),

  logsByTask: (taskId) => client.get(`/tasks/${taskId}/logs`),
  logsAll: () => client.get('/logs'),
  auditLogs: (taskId) => client.get(`/audit/tasks/${taskId}/logs`),

  proposals: () => client.get('/governance/proposals'),
  approveProposal: (id) => client.post(`/governance/proposals/${id}/approve`),
  rejectProposal: (id, reason) => client.post(`/governance/proposals/${id}/reject`, null, { params: { reason } }),

  propagations: () => client.get('/reputation/propagations'),

  demoStatus: () => client.get('/demo/status'),
  demoSeed: (payload) => client.post('/demo/seed', payload),
};
