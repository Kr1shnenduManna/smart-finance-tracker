import { useState, useEffect, useMemo } from 'react';
import { getActiveBudgets, getBudgetAlerts, getTransactions, getAccounts } from '../api/endpoints';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';
import { Sparkles, AlertTriangle, ArrowRight, Coffee, Car, Home, ShoppingBag, Film, Utensils, Zap, CreditCard, Smartphone, Plane, Heart, BookOpen, Repeat, ChevronDown } from 'lucide-react';
import { Link } from 'react-router-dom';

const categoryIcons = {
  'food': Utensils, 'drink': Utensils, 'dining': Utensils, 'groceries': Utensils,
  'transport': Car, 'fuel': Car, 'auto': Car,
  'rent': Home, 'housing': Home,
  'utilities': Zap, 'bill': Zap, 'recharge': Smartphone,
  'shopping': ShoppingBag,
  'entertainment': Film,
  'coffee': Coffee,
  'travel': Plane, 'healthcare': Heart, 'medical': Heart,
  'education': BookOpen,
  'emi': CreditCard, 'loan': CreditCard,
  'subscription': Repeat,
};

const categoryColors = {
  'food': '#FF5722', 'drink': '#FF5722', 'dining': '#FF5722', 'groceries': '#FF9800',
  'transport': '#FFC107', 'fuel': '#FFC107',
  'rent': '#795548', 'housing': '#795548',
  'shopping': '#8b5cf6',
  'entertainment': '#ec4899',
  'utilities': '#06b6d4', 'recharge': '#E91E63',
  'travel': '#2196F3', 'healthcare': '#8BC34A',
  'education': '#00BCD4',
  'emi': '#9C27B0', 'loan': '#9C27B0',
  'subscription': '#673AB7',
};

function getIcon(name) {
  if (!name) return Utensils;
  const lower = name.toLowerCase();
  for (const [key, Icon] of Object.entries(categoryIcons)) {
    if (lower.includes(key)) return Icon;
  }
  return Utensils;
}

function getColor(name) {
  if (!name) return '#6b7280';
  const lower = name.toLowerCase();
  for (const [key, color] of Object.entries(categoryColors)) {
    if (lower.includes(key)) return color;
  }
  return '#6b7280';
}

function formatCurrency(n) {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n || 0);
}

function formatDate(dateStr) {
  const d = new Date(dateStr);
  const now = new Date();
  const diff = Math.floor((now - d) / (1000 * 60 * 60 * 24));
  if (diff === 0) return 'Today';
  if (diff === 1) return 'Yesterday';
  return d.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' });
}

export default function Dashboard() {
  const [accounts, setAccounts] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState('all');
  const [allTransactions, setAllTransactions] = useState([]);
  const [budgets, setBudgets] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [chartRange, setChartRange] = useState(30);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [accRes, budgetsRes, alertsRes, txRes] = await Promise.all([
        getAccounts().catch(() => ({ data: [] })),
        getActiveBudgets().catch(() => ({ data: [] })),
        getBudgetAlerts().catch(() => ({ data: [] })),
        getTransactions({ page_size: 100 }).catch(() => ({ data: { results: [] } })),
      ]);
      setAccounts(accRes.data?.results || accRes.data || []);
      setBudgets(Array.isArray(budgetsRes.data) ? budgetsRes.data : budgetsRes.data?.results || []);
      setAlerts(alertsRes.data || []);
      setAllTransactions(txRes.data?.results || txRes.data || []);
    } catch (err) {
      console.error('Dashboard load error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Filter transactions by selected account
  const transactions = useMemo(() => {
    if (selectedAccount === 'all') return allTransactions;
    return allTransactions.filter((tx) => String(tx.account) === String(selectedAccount));
  }, [allTransactions, selectedAccount]);

  // Compute summary from actual transactions
  const summary = useMemo(() => {
    const income = transactions
      .filter((tx) => tx.transaction_type === 'income')
      .reduce((s, tx) => s + parseFloat(tx.amount || 0), 0);
    const expense = transactions
      .filter((tx) => tx.transaction_type === 'expense')
      .reduce((s, tx) => s + parseFloat(tx.amount || 0), 0);
    return { total_income: income, total_expenses: expense, net: income - expense };
  }, [transactions]);

  // Account balance
  const accountBalance = useMemo(() => {
    if (selectedAccount === 'all') {
      return accounts.reduce((s, a) => s + parseFloat(a.balance || 0), 0);
    }
    const acc = accounts.find((a) => String(a.id) === String(selectedAccount));
    return acc ? parseFloat(acc.balance || 0) : 0;
  }, [accounts, selectedAccount]);

  // Dynamic chart data from real transactions
  const chartData = useMemo(() => {
    const days = chartRange;
    const map = {};
    const now = new Date();
    for (let i = days; i >= 0; i--) {
      const d = new Date(now);
      d.setDate(d.getDate() - i);
      const key = d.toISOString().split('T')[0];
      map[key] = { date: d.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' }), income: 0, expense: 0 };
    }
    transactions.forEach((tx) => {
      if (map[tx.date]) {
        if (tx.transaction_type === 'income') map[tx.date].income += parseFloat(tx.amount);
        else map[tx.date].expense += parseFloat(tx.amount);
      }
    });
    return Object.values(map);
  }, [transactions, chartRange]);

  // Top expense category
  const topExpenseCategory = useMemo(() => {
    const catMap = {};
    transactions.filter((tx) => tx.transaction_type === 'expense').forEach((tx) => {
      const cat = tx.category_name || 'Other';
      catMap[cat] = (catMap[cat] || 0) + parseFloat(tx.amount);
    });
    const sorted = Object.entries(catMap).sort((a, b) => b[1] - a[1]);
    return sorted[0] || null;
  }, [transactions]);

  const selectedAccountName = useMemo(() => {
    if (selectedAccount === 'all') return 'All Accounts';
    const acc = accounts.find((a) => String(a.id) === String(selectedAccount));
    return acc ? acc.name : 'All Accounts';
  }, [accounts, selectedAccount]);

  if (loading) {
    return <div className="loading-spinner"><div className="spinner" /></div>;
  }

  return (
    <div>
      {/* Header with Account Selector */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: 'var(--gray-900)' }}>Dashboard</h1>
        <div style={{ position: 'relative' }}>
          <select
            value={selectedAccount}
            onChange={(e) => setSelectedAccount(e.target.value)}
            style={{
              padding: '8px 36px 8px 14px', border: '1px solid var(--gray-300)', borderRadius: 8,
              fontSize: 14, fontWeight: 500, background: '#fff', appearance: 'none', cursor: 'pointer', minWidth: 180,
            }}
          >
            <option value="all">All Accounts</option>
            {accounts.map((acc) => (
              <option key={acc.id} value={acc.id}>{acc.name} ({acc.account_type.replace('_', ' ')})</option>
            ))}
          </select>
          <ChevronDown size={16} style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none', color: 'var(--gray-400)' }} />
        </div>
      </div>

      {/* Stat Cards */}
      <div className="stat-cards">
        <div className="stat-card">
          <div className="stat-top"><span className="stat-label">Account Balance</span></div>
          <div className="stat-value">{formatCurrency(accountBalance)}</div>
          <div style={{ fontSize: 12, color: 'var(--gray-400)', marginTop: 4 }}>{selectedAccountName}</div>
        </div>
        <div className="stat-card">
          <div className="stat-top"><span className="stat-label">Total Income</span></div>
          <div className="stat-value income">+{formatCurrency(summary.total_income)}</div>
          <MiniLineChart data={transactions.filter((t) => t.transaction_type === 'income')} color="#22c55e" />
        </div>
        <div className="stat-card">
          <div className="stat-top"><span className="stat-label">Total Expenses</span></div>
          <div className="stat-value expense">-{formatCurrency(summary.total_expenses)}</div>
          <MiniLineChart data={transactions.filter((t) => t.transaction_type === 'expense')} color="#ef4444" />
        </div>
        <div className="stat-card">
          <div className="stat-top"><span className="stat-label">Net Savings</span></div>
          <div className="stat-value" style={{ color: summary.net >= 0 ? 'var(--success)' : 'var(--danger)' }}>{formatCurrency(summary.net)}</div>
          <MiniLineChart data={transactions} color={summary.net >= 0 ? '#22c55e' : '#ef4444'} />
        </div>
      </div>

      {/* Chart + Insights */}
      <div className="dashboard-grid">
        <div className="chart-card">
          <div className="card-header">
            <div>
              <h3>Cash Flow</h3>
              <p>Income vs Expenses — last {chartRange} days</p>
            </div>
            <div className="chart-toggle">
              <button className={chartRange === 30 ? 'active' : ''} onClick={() => setChartRange(30)}>30 Days</button>
              <button className={chartRange === 90 ? 'active' : ''} onClick={() => setChartRange(90)}>90 Days</button>
            </div>
          </div>
          <div className="card-body">
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="gIncome" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#22c55e" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gExpense" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#9ca3af' }} interval="preserveStartEnd" />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#9ca3af' }} tickFormatter={(v) => `₹${v}`} />
                <Tooltip formatter={(v, name) => [`₹${parseFloat(v).toLocaleString('en-IN')}`, name === 'income' ? 'Income' : 'Expense']} />
                <Area type="monotone" dataKey="income" stroke="#22c55e" strokeWidth={2} fill="url(#gIncome)" />
                <Area type="monotone" dataKey="expense" stroke="#ef4444" strokeWidth={2} fill="url(#gExpense)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="insights-card">
          <div className="badge"><Sparkles size={14} /> SMART INSIGHTS</div>
          <h3>Spending Summary</h3>
          <p>
            {topExpenseCategory
              ? <>Your top expense is <span className="highlight">{topExpenseCategory[0]}</span> at {formatCurrency(topExpenseCategory[1])}.</>
              : <>Add transactions to see spending insights here.</>}
          </p>
          {alerts.length > 0 && (
            <p style={{ color: 'var(--warning)', fontWeight: 600, fontSize: 13 }}>
              <AlertTriangle size={14} style={{ verticalAlign: -2 }} /> {alerts.length} budget{alerts.length > 1 ? 's' : ''} over threshold
            </p>
          )}
          <div className="prediction-box">
            <div className="label">Net Position</div>
            <div className="value" style={{ color: summary.net >= 0 ? 'var(--success)' : 'var(--danger)' }}>{formatCurrency(Math.abs(summary.net))}</div>
            <div className="sub">{summary.net >= 0 ? 'Surplus' : 'Deficit'} this period</div>
          </div>
          <Link to="/analytics" className="btn btn-success btn-full">View Full Analysis <ArrowRight size={16} /></Link>
        </div>
      </div>

      {/* Budgets + Recent Transactions */}
      <div className="dashboard-bottom">
        <div className="card">
          <div className="card-header">
            <h3>Budgets at a Glance</h3>
            <Link to="/budgets" style={{ fontSize: 13, color: 'var(--primary)', fontWeight: 600 }}>Manage All</Link>
          </div>
          <div className="card-body">
            {budgets.length === 0 ? (
              <div className="empty-state"><p>No active budgets yet</p><Link to="/budgets" className="btn btn-primary btn-sm">Create Budget</Link></div>
            ) : budgets.slice(0, 4).map((b) => {
              const Icon = getIcon(b.category_name);
              const color = getColor(b.category_name);
              const pct = b.spent_percentage || 0;
              const isOver = pct >= (b.alert_threshold || 80);
              return (
                <div key={b.id} className="budget-item">
                  <div className="budget-icon" style={{ background: color + '15', color }}><Icon size={18} /></div>
                  <div className="budget-info" style={{ flex: 1 }}>
                    <div className="name">{b.category_name}</div>
                    <div className="progress-bar">
                      <div className="fill" style={{ width: `${Math.min(pct, 100)}%`, background: pct >= 100 ? 'var(--danger)' : pct >= 75 ? 'var(--warning)' : color }} />
                    </div>
                    {isOver && <div className="budget-alert"><AlertTriangle size={12} /> Threshold reached ({pct.toFixed(0)}%)</div>}
                  </div>
                  <div className="budget-amounts">₹{b.spent_amount?.toFixed(0) || 0} <span>/ ₹{parseFloat(b.amount).toFixed(0)}</span></div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3>Recent Transactions</h3>
            <Link to="/transactions" style={{ fontSize: 13, color: 'var(--primary)', fontWeight: 600 }}>View All</Link>
          </div>
          <div className="card-body">
            {transactions.length === 0 ? (
              <div className="empty-state"><p>No transactions yet</p><Link to="/transactions" className="btn btn-primary btn-sm">Add Transaction</Link></div>
            ) : transactions.slice(0, 5).map((tx) => {
              const Icon = getIcon(tx.category_name);
              const isIncome = tx.transaction_type === 'income';
              return (
                <div key={tx.id} className="transaction-item">
                  <div className="tx-icon"><Icon size={18} /></div>
                  <div className="tx-info">
                    <div className="name">{tx.description || tx.category_name || 'Transaction'}</div>
                    <div className="meta">{formatDate(tx.date)} • {tx.category_name || 'Uncategorized'}</div>
                  </div>
                  <div className={`tx-amount ${isIncome ? 'income' : 'expense'}`}>{isIncome ? '+' : '-'}{formatCurrency(tx.amount)}</div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

function MiniLineChart({ data, color }) {
  const chartData = useMemo(() => {
    const days = {};
    for (let i = 6; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      days[d.toISOString().split('T')[0]] = 0;
    }
    (data || []).forEach((tx) => {
      if (days[tx.date] !== undefined) days[tx.date] += parseFloat(tx.amount || 0);
    });
    return Object.values(days).map((v) => ({ v: v || 0 }));
  }, [data]);

  return (
    <div className="mini-chart">
      <ResponsiveContainer width="100%" height={32}>
        <LineChart data={chartData.some((d) => d.v > 0) ? chartData : [{ v: 1 }, { v: 1 }, { v: 1 }, { v: 1 }, { v: 1 }, { v: 1 }, { v: 1 }]}>
          <Line type="monotone" dataKey="v" stroke={color} strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
