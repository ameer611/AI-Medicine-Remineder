import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  BarChart,
  Bar,
} from 'recharts'

export function AdherenceLineChart({ data }) {
  return (
    <div className="panel" style={{ height: 320 }}>
      <h3>Adherence timeline</h3>
      <ResponsiveContainer width="100%" height="88%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="rate" stroke="#0f766e" strokeWidth={3} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export function AdherenceBarChart({ data }) {
  return (
    <div className="panel" style={{ height: 320 }}>
      <h3>Per-medication adherence</h3>
      <ResponsiveContainer width="100%" height="88%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="rate" fill="#b45309" radius={[8, 8, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
