import React, { useState } from 'react';
import {
    AreaChart, Area,
    BarChart, Bar,
    XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import { Select } from './ui/Select';

// Mock Data Generators
const generateData = (period: 'Hourly' | 'Daily' | 'Monthly', baseValue: number) => {
    const data = [];
    const now = new Date();

    let count = 24;
    let interval = 3600000; // 1 hour
    let format: Intl.DateTimeFormatOptions = { hour: '2-digit', minute: '2-digit' };

    if (period === 'Daily') {
        count = 30;
        interval = 86400000; // 1 day
        format = { month: 'short', day: 'numeric' };
    } else if (period === 'Monthly') {
        count = 12;
        // Approximation for monthly generation logic
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

        // Energy (kWh) - Aggregate bars
        // More variability for realism
        const energy = Math.max(0.1, (Math.random() * baseValue * 0.005));

        // Power (W) - Instantaneous curve
        // Base value +/- 50% random fluctuation
        const power = Math.max(0, Math.floor(baseValue + (Math.random() - 0.5) * (baseValue * 0.5)));

        data.push({
            time: timeLabel,
            energy: parseFloat(energy.toFixed(2)),
            power: power
        });
    }
    return data;
};

// Mock Devices (Should ideally be shared context or state)
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
        <div className="container py-8">
            <div className="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1>Analytics</h1>
                    <p className="text-muted">Historical energy consumption analysis</p>
                </div>

                <div className="flex flex-col sm:flex-row gap-4">
                    <Select
                        options={[
                            { id: 'Hourly', label: 'Hourly' },
                            { id: 'Daily', label: 'Daily' },
                            { id: 'Monthly', label: 'Monthly' },
                        ]}
                        value={timeRange}
                        onChange={(value) => setTimeRange(value as any)}
                        className="w-full sm:w-64"
                    />
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
                {/* Sidebar / Device Selection */}
                <div className="lg:col-span-1">
                    <h3 className="text-sm font-semibold text-muted uppercase tracking-wider mb-3">Select Device</h3>
                    <Select
                        options={DEVICES.map(d => ({ id: d.id, label: d.name }))}
                        value={selectedDevice}
                        onChange={setSelectedDevice}
                        className="w-full"
                    />
                </div>

                {/* Main Charts Area */}
                <div className="lg:col-span-3 space-y-8">

                    {/* 1. Energy Consumption (Bar Chart) */}
                    <div className="card h-[400px] flex flex-col">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="card-title text-base text-zinc-200">
                                Energy Consumption (kWh)
                            </h3>
                            <div className="text-right">
                                <div className="text-2xl font-bold text-white">
                                    {totalEnergy.toFixed(2)} <span className="text-sm font-normal text-muted">kWh</span>
                                </div>
                                <div className="text-xs text-muted">Total for period</div>
                            </div>
                        </div>

                        <div className="flex-1 w-full min-h-0">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#333" />
                                    <XAxis
                                        dataKey="time"
                                        stroke="#666"
                                        fontSize={12}
                                        tickLine={false}
                                        axisLine={false}
                                        minTickGap={30}
                                    />
                                    <YAxis
                                        stroke="#666"
                                        fontSize={12}
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

                    {/* 2. Power Time Series (Area Chart) */}
                    <div className="card h-[350px] flex flex-col">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="card-title text-base text-zinc-200">
                                Power Trend (Watts) - Time Series
                            </h3>
                        </div>

                        <div className="flex-1 w-full min-h-0">
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                                    <defs>
                                        <linearGradient id="colorValueAnalyticsPower" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#4ade80" stopOpacity={0.3} />
                                            <stop offset="95%" stopColor="#4ade80" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#333" />
                                    <XAxis
                                        dataKey="time"
                                        stroke="#666"
                                        fontSize={12}
                                        tickLine={false}
                                        axisLine={false}
                                        minTickGap={30}
                                    />
                                    <YAxis
                                        stroke="#666"
                                        fontSize={12}
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
                                        fill="url(#colorValueAnalyticsPower)"
                                        strokeWidth={2}
                                    />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
};
