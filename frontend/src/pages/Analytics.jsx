import { useState, useEffect, useMemo } from 'react';
import { getTransactions, getTransactionsByCategory, getTransactionSummary, getAccounts } from '../api/endpoints';
import { BarChart, Bar, PieChart, Pie, Cell, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { useCurrency } from '../context/CurrencyContext';

const COLORS = ['#6366f1', '#f43f5e', '#10b981', '#f59e0b', '#3b82f6', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316', '#64748b'];

export default function Analytics() {
  const [transactions, setTransactions] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState('all');
  const [period, setPeriod] = useState('30'); // days
  const [loading, setLoading] = useState(true);
  const { fc, symbol, convert } = useCurrency();

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [txRes, accRes] = await Promise.all([
        getTransactions({ page_size: 500 }).catch(() => ({ data: [] })),
        getAccounts().catch(() => ({ data: [] })),
      ]);
      setTransactions(txRes.data?.results || txRes.data || []);
      setAccounts(accRes.data?.results || accRes.data || []);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  // Filter by account & period
  const filtered = useMemo(() => {
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - parseInt(period));
    return transactions.filter((tx) => {
      if (selectedAccount !== 'all' && String(tx.account) !== selectedAccount) return false;
      return new Date(tx.date) >= cutoff;
    });
  }, [transactions, selectedAccount, period]);

  // Category breakdown
  const categoryData = useMemo(() => {
    const map = {};
    filtered.filter(t => t.transaction_type === 'expense').forEach((tx) => {
      const cat = tx.category_name || 'Uncategorized';
      map[cat] = (map[cat] || 0) + parseFloat(tx.amount);
    });
    return Object.entries(map)
      .map(([name, value]) => ({ name, value: Math.round(value) }))
      .sort((a, b) => b.value - a.value);
  }, [filtered]);

  // Monthly trend (income vs expense by month)
  const monthlyTrend = useMemo(() => {
    const map = {};
    filtered.forEach((tx) => {
      const d = new Date(tx.date);
      const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
      if (!map[key]) map[key] = { month: key, income: 0, expense: 0 };
      if (tx.transaction_type === 'income') map[key].income += parseFloat(tx.amount);
      else map[key].expense += parseFloat(tx.amount);
    });
    return Object.values(map).sort((a, b) => a.month.localeCompare(b.month));
  }, [filtered]);

  // Daily spending (last N days)
  const dailySpending = useMemo(() => {
    const map = {};
    filtered.filter(t => t.transaction_type === 'expense').forEach((tx) => {
      const key = tx.date;
      map[key] = (map[key] || 0) + parseFloat(tx.amount);
    });
    return Object.entries(map)
      .map(([date, amount]) => ({ date, amount: Math.round(amount) }))
      .sort((a, b) => a.date.localeCompare(b.date))
      .slice(-30);
  }, [filtered]);

  // Summary stats
  const stats = useMemo(() => {
    const inc = filtered.filter(t => t.transaction_type === 'income').reduce((s, t) => s + parseFloat(t.amount), 0);
    const exp = filtered.filter(t => t.transaction_type === 'expense').reduce((s, t) => s + parseFloat(t.amount), 0);
    const avgDaily = parseInt(period) > 0 ? exp / parseInt(period) : 0;
    return { income: inc, expense: exp, savings: inc - exp, avgDaily };
  }, [filtered, period]);

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>;

  return (
    <div>
      <div className="page-header">
        <h1>Analytics</h1>
        <div style={{ display: 'flex', gap: 12 }}>
          <select value={selectedAccount} onChange={(e) => setSelectedAccount(e.target.value)} style={{ minWidth: 140 }}>
            <option value="all">All Accounts</option>
            {accounts.map(a => <option key={a.id} value={String(a.id)}>{a.name}</option>)}
          </select>
          <select value={period} onChange={(e) => setPeriod(e.target.value)} style={{ minWidth: 120 }}>
            <option value="7">Last 7 days</option>
            <option value="30">Last 30 days</option>
            <option value="90">Last 90 days</option>
            <option value="365">Last year</option>
          </select>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="stats-grid" style={{ marginBottom: 24 }}>
        <div className="card"><div className="card-body" style={{ padding: 20 }}>
          <div style={{ fontSize: 12, color: 'var(--gray-500)' }}>Total Income</div>
          <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--success)' }}>{fc(stats.income)}</div>
        </div></div>
        <div className="card"><div className="card-body" style={{ padding: 20 }}>
          <div style={{ fontSize: 12, color: 'var(--gray-500)' }}>Total Expenses</div>
          <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--danger)' }}>{fc(stats.expense)}</div>
        </div></div>
        <div className="card"><div className="card-body" style={{ padding: 20 }}>
          <div style={{ fontSize: 12, color: 'var(--gray-500)' }}>Net Savings</div>
          <div style={{ fontSize: 24, fontWeight: 700, color: stats.savings >= 0 ? 'var(--success)' : 'var(--danger)' }}>{fc(stats.savings)}</div>
        </div></div>
        <div className="card"><div className="card-body" style={{ padding: 20 }}>
          <div style={{ fontSize: 12, color: 'var(--gray-500)' }}>Avg Daily Spend</div>
          <div style={{ fontSize: 24, fontWeight: 700 }}>{fc(stats.avgDaily)}</div>
        </div></div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 24 }}>
        {/* Income vs Expense Bar Chart */}
        <div className="card">
          <div className="card-header"><h3>Income vs Expenses</h3></div>
          <div className="card-body" style={{ height: 300 }}>
            {monthlyTrend.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={monthlyTrend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--gray-100)" />
                  <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} tickFormatter={(v) => `${symbol}${(convert(v)/1000).toFixed(0)}k`} />
                  <Tooltip formatter={(v) => fc(v)} />
                  <Legend />
                  <Bar dataKey="income" fill="#10b981" radius={[4, 4, 0, 0]} name="Income" />
                  <Bar dataKey="expense" fill="#f43f5e" radius={[4, 4, 0, 0]} name="Expense" />
                </BarChart>
              </ResponsiveContainer>
            ) : <div className="empty-state"><p>No data for this period</p></div>}
          </div>
        </div>

        {/* Spending by Category Pie */}
        <div className="card">
          <div className="card-header"><h3>Spending by Category</h3></div>
          <div className="card-body" style={{ height: 300 }}>
            {categoryData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={categoryData} cx="50%" cy="50%" outerRadius={100} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                    {categoryData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip formatter={(v) => fc(v)} />
                </PieChart>
              </ResponsiveContainer>
            ) : <div className="empty-state"><p>No expense data</p></div>}
          </div>
        </div>
      </div>

      {/* Daily Spending Trend */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header"><h3>Daily Spending Trend</h3></div>
        <div className="card-body" style={{ height: 300 }}>
          {dailySpending.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={dailySpending}>
                <defs>
                  <linearGradient id="spendGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--gray-100)" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={(d) => new Date(d).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })} />
                <YAxis tick={{ fontSize: 12 }} tickFormatter={(v) => `${symbol}${(convert(v) / 1000).toFixed(0)}k`} />
                <Tooltip formatter={(v) => fc(v)} labelFormatter={(d) => new Date(d).toLocaleDateString('en-IN', { weekday: 'short', month: 'short', day: 'numeric' })} />
                <Area type="monotone" dataKey="amount" stroke="#f43f5e" fill="url(#spendGrad)" strokeWidth={2} name="Spending" />
              </AreaChart>
            </ResponsiveContainer>
          ) : <div className="empty-state"><p>No spending data</p></div>}
        </div>
      </div>

      {/* Category Breakdown Table */}
      <div className="card">
        <div className="card-header"><h3>Category Breakdown</h3></div>
        <div className="card-body">
          {categoryData.length > 0 ? (
            <div className="table-wrapper">
              <table>
                <thead><tr><th>Category</th><th>Amount</th><th>% of Total</th><th>Visual</th></tr></thead>
                <tbody>
                  {categoryData.map((c, i) => {
                    const total = categoryData.reduce((s, x) => s + x.value, 0);
                    const pct = total > 0 ? (c.value / total) * 100 : 0;
                    return (
                      <tr key={c.name}>
                        <td style={{ fontWeight: 500 }}>
                          <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: COLORS[i % COLORS.length], marginRight: 8 }} />
                          {c.name}
                        </td>
                        <td style={{ fontWeight: 600 }}>{fc(c.value)}</td>
                        <td>{pct.toFixed(1)}%</td>
                        <td>
                          <div style={{ background: 'var(--gray-100)', borderRadius: 4, height: 8, width: 120, overflow: 'hidden' }}>
                            <div style={{ width: `${pct}%`, background: COLORS[i % COLORS.length], height: '100%', borderRadius: 4 }} />
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : <div className="empty-state"><p>No data to display</p></div>}
        </div>
      </div>
    </div>
  );
}
