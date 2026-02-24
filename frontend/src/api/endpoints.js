import API from './axios';

// ── Auth ──
export const login = (credentials) => API.post('/api-auth/login/', credentials);
export const logout = () => API.post('/api-auth/logout/');
export const register = (data) => API.post('/api/accounts/register/', data);
export const getMe = () => API.get('/api/accounts/users/me/');
export const updateProfile = (data) => API.patch('/api/accounts/users/me/', data);

// ── Accounts (financial accounts) ──
export const getAccounts = () => API.get('/api/accounts/accounts/');
export const createAccount = (data) => API.post('/api/accounts/accounts/', data);
export const updateAccount = (id, data) => API.put(`/api/accounts/accounts/${id}/`, data);
export const deleteAccount = (id) => API.delete(`/api/accounts/accounts/${id}/`);

// ── Categories ──
export const getCategories = () => API.get('/api/transactions/categories/');
export const getIncomeCategories = () => API.get('/api/transactions/categories/income/');
export const getExpenseCategories = () => API.get('/api/transactions/categories/expense/');

// ── Transactions ──
export const getTransactions = (params) => API.get('/api/transactions/transactions/', { params });
export const createTransaction = (data) => API.post('/api/transactions/transactions/', data);
export const updateTransaction = (id, data) => API.put(`/api/transactions/transactions/${id}/`, data);
export const deleteTransaction = (id) => API.delete(`/api/transactions/transactions/${id}/`);
export const getTransactionSummary = () => API.get('/api/transactions/transactions/summary/');
export const getTransactionsByCategory = () => API.get('/api/transactions/transactions/by_category/');

// ── Budgets ──
export const getBudgets = () => API.get('/api/budgets/budgets/');
export const createBudget = (data) => API.post('/api/budgets/budgets/', data);
export const updateBudget = (id, data) => API.put(`/api/budgets/budgets/${id}/`, data);
export const deleteBudget = (id) => API.delete(`/api/budgets/budgets/${id}/`);
export const getActiveBudgets = () => API.get('/api/budgets/budgets/active/');
export const getBudgetAlerts = () => API.get('/api/budgets/budgets/alerts/');
