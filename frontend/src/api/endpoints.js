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

// ── Currency ──
export const getCurrencies = () => API.get('/api/accounts/currencies/');
export const getExchangeRate = (from, to, amount) => {
  const params = { from, to };
  if (amount) params.amount = amount;
  return API.get('/api/accounts/exchange-rate/', { params });
};
export const getAllExchangeRates = () => API.get('/api/accounts/exchange-rates/');

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

// ── Bills ──
export const getBills = () => API.get('/api/bills/bills/');
export const createBill = (data) => API.post('/api/bills/bills/', data);
export const updateBill = (id, data) => API.put(`/api/bills/bills/${id}/`, data);
export const deleteBill = (id) => API.delete(`/api/bills/bills/${id}/`);
export const getUpcomingBills = () => API.get('/api/bills/bills/upcoming/');
export const getOverdueBills = () => API.get('/api/bills/bills/overdue/');
export const getBillsSummary = () => API.get('/api/bills/bills/summary/');
export const markBillPaid = (id, data) => API.post(`/api/bills/bills/${id}/mark_paid/`, data);
export const cancelBill = (id) => API.post(`/api/bills/bills/${id}/cancel/`);
export const getBillNotifications = () => API.get('/api/bills/notifications/');
export const getUnreadNotifications = () => API.get('/api/bills/notifications/unread/');
export const markNotificationRead = (id) => API.post(`/api/bills/notifications/${id}/mark_as_read/`);
export const markAllNotificationsRead = () => API.post('/api/bills/notifications/mark_all_read/');

// ── Savings Goals ──
export const getGoals = () => API.get('/api/goals/goals/');
export const createGoal = (data) => API.post('/api/goals/goals/', data);
export const updateGoal = (id, data) => API.put(`/api/goals/goals/${id}/`, data);
export const deleteGoal = (id) => API.delete(`/api/goals/goals/${id}/`);
export const getActiveGoals = () => API.get('/api/goals/goals/active/');
export const getCompletedGoals = () => API.get('/api/goals/goals/completed/');
export const getGoalsSummary = () => API.get('/api/goals/goals/summary/');
export const addGoalContribution = (id, data) => API.post(`/api/goals/goals/${id}/add_contribution/`, data);
export const completeGoal = (id) => API.post(`/api/goals/goals/${id}/complete/`);
