import React, { useState } from 'react';
import {
    AreaChart, Area,
    BarChart, Bar,
    XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';

const generateData = (period: 'Hourly' | 'Daily' | 'Monthly', baseValue: number) => {
    const data = [];
    const now = new Date();

    let count = 24;
    let interval = 3600000;
    let format: Intl.DateTimeFormatOptions = { hour: '2-digit', minute: '2-digit' };

    if (period === 'Daily') {
        count = 30;
        interval = 86400000;
        format = { month: 'short', day: 'numeric' };
    } else if (period === 'Monthly') {
        count = 12;
        format = { month: 'short', year: '2-digit' };
    }

    for (let i = count; i >= 0; i--) {
        let timeLabel = '';
        if (period === 'Monthly') {
            const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
            timeLabel = d.toLocaleDateString([], format);
        } else {
            const time = new Date(now.getTime() - i * interval);
            timeLabel = time.toLocaleDateString([], format);
            if (period === 'Hourly') {
                timeLabel = time.toLocaleTimeString([], format);
            }
        }

        const energy = Math.max(0.1, (Math.random() * baseValue * 0.005));
        const power = Math.max(0, Math.floor(baseValue + (Math.random() - 0.5) * (baseValue * 0.5)));

        data.push({
            time: timeLabel,
            energy: parseFloat(energy.toFixed(2)),
            power: power
        });
    }
    return data;
};

const DEVICES = [
    { id: 'all', name: 'Total Consumption' },
    { id: '1', name: 'Oficina' },
    { id: '2', name: 'Termo' },
    { id: '3', name: 'Nevera Siemens' },
    { id: '4', name: 'Nevera Daewoo' }
];

export const Analytics: React.FC = () => {
    const [timeRange, setTimeRange] = useState<'Hourly' | 'Daily' | 'Monthly'>('Hourly');
    const [selectedDevice, setSelectedDevice] = useState<string>('all');

    const baseLoad = selectedDevice === 'all' ? 400 : 100;
    const chartData = generateData(timeRange, baseLoad);
    const totalEnergy = chartData.reduce((acc, curr) => acc + curr.energy, 0);

    return (
        <main className="container py-4">
            {/* Header */}
            <div className="row mb-4">
                <div className="col-12">
                    <h2 className="d-flex align-items-center gap-2">
                        <i className="fa-solid fa-chart-line text-success"></i>
                        Analytics
                    </h2>
                </div>
            </div>

            {/* Controls */}
            <div className="row mb-4">
                <div className="col-md-6 mb-3 mb-md-0">
                    <label className="form-label text-muted text-uppercase small fw-bold">Device</label>
                    <select
                        className="form-select bg-dark text-white border-secondary"
                        value={selectedDevice}
                        onChange={(e) => setSelectedDevice(e.target.value)}
                    >
                        {DEVICES.map(d => (
                            <option key={d.id} value={d.id}>{d.name}</option>
                        ))}
                    </select>
                </div>
                <div className="col-md-6">
                    <label className="form-label text-muted text-uppercase small fw-bold">Period</label>
                    <select
                        className="form-select bg-dark text-white border-secondary"
                        value={timeRange}
                        onChange={(e) => setTimeRange(e.target.value as any)}
                    >
                        <option value="Hourly">Hourly</option>
                        <option value="Daily">Daily</option>
                        <option value="Monthly">Monthly</option>
                    </select>
                </div>
            </div>

            {/* Content Row */}
            <div className="row">
                <div className="col-12">
                    <div className="card mb-4">
                        <div className="card-header bg-transparent border-secondary d-flex justify-content-between align-items-center">
                            <span className="text-uppercase small text-muted fw-bold">Total Energy ({timeRange})</span>
                            <div className="d-flex align-items-baseline gap-1">
                                <span className="h4 mb-0 fw-bold text-white">{totalEnergy.toFixed(2)}</span>
                                <span className="small text-muted">kWh</span>
                            </div>
                        </div>

                        <div className="card-body">
                            {/* Energy Chart Section */}
                            <div className="mb-5">
                                <h6 className="card-title mb-4">Energy Consumption</h6>
                                <div style={{ height: '300px', width: '100%' }}>
                                    <ResponsiveContainer width="100%" height="100%">
                                        <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#333" />
                                            <XAxis
                                                dataKey="time"
                                                stroke="#666"
                                                fontSize={11}
                                                tickLine={false}
                                                axisLine={false}
                                                minTickGap={30}
                                            />
                                            <YAxis
                                                stroke="#666"
                                                fontSize={11}
                                                tickLine={false}
                                                axisLine={false}
                                            />
                                            <Tooltip
                                                cursor={{ fill: '#333', opacity: 0.2 }}
                                                contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', color: '#fafafa' }}
                                                itemStyle={{ color: '#22c55e' }}
                                            />
                                            <Bar
                                                dataKey="energy"
                                                fill="#15803d"
                                                radius={[4, 4, 0, 0]}
                                                fillOpacity={0.8}
                                            />
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>

                            <hr className="border-secondary my-4" />

                            {/* Power Chart Section */}
                            <div>
                                <h6 className="card-title mb-4">Power Trend</h6>
                                <div style={{ height: '300px', width: '100%' }}>
                                    <ResponsiveContainer width="100%" height="100%">
                                        <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                                            <defs>
                                                <linearGradient id="analyticsPowerGradientBootstrap" x1="0" y1="0" x2="0" y2="1">
                                                    <stop offset="5%" stopColor="#4ade80" stopOpacity={0.3} />
                                                    <stop offset="95%" stopColor="#4ade80" stopOpacity={0} />
                                                </linearGradient>
                                            </defs>
                                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#333" />
                                            <XAxis
                                                dataKey="time"
                                                stroke="#666"
                                                fontSize={11}
                                                tickLine={false}
                                                axisLine={false}
                                                minTickGap={30}
                                            />
                                            <YAxis
                                                stroke="#666"
                                                fontSize={11}
                                                tickLine={false}
                                                axisLine={false}
                                                tickFormatter={(val) => `${val}W`}
                                            />
                                            <Tooltip
                                                contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', color: '#fafafa' }}
                                                itemStyle={{ color: '#4ade80' }}
                                            />
                                            <Area
                                                type="monotone"
                                                dataKey="power"
                                                stroke="#4ade80"
                                                fillOpacity={1}
                                                fill="url(#analyticsPowerGradientBootstrap)"
                                                strokeWidth={2}
                                            />
                                        </AreaChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    );
};
