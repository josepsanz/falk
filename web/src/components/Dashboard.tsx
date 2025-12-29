import React, { useState } from 'react';
import { Zap, Settings } from 'lucide-react';
import type { Device } from '../types';
import { DeviceCard } from './DeviceCard';
import { EnergyChart } from './EnergyChart';

// Mock Data
const MOCK_DEVICES: Device[] = [
    {
        id: '1',
        name: 'Oficina',
        ip: '192.168.1.101',
        state: true,
        power: 125.5,
        voltage: 220.1,
        current: 570,
        updatedAt: Date.now()
    },
    {
        id: '2',
        name: 'Termo',
        ip: '192.168.1.102',
        state: true,
        power: 350.2,
        voltage: 219.8,
        current: 1590,
        updatedAt: Date.now()
    },
    {
        id: '3',
        name: 'Nevera Siemens',
        ip: '192.168.1.105',
        state: false,
        power: 0.0,
        voltage: 221.0,
        current: 0,
        updatedAt: Date.now() - 3600000
    },
    {
        id: '4',
        name: 'Nevera Daewoo',
        ip: '192.168.1.106',
        state: true,
        power: 85.0,
        voltage: 220.5,
        current: 385,
        updatedAt: Date.now()
    }
];

const generateChartData = () => {
    const data = [];
    const now = new Date();
    for (let i = 24; i >= 0; i--) {
        const time = new Date(now.getTime() - i * 60 * 60 * 1000);
        data.push({
            time: time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            value: Math.floor(Math.random() * (600 - 200) + 200), // Random value between 200W and 600W
        });
    }
    return data;
};

const MOCK_CHART_DATA = generateChartData();


interface DashboardProps {
    isPage?: boolean;
}

export const Dashboard: React.FC<DashboardProps> = ({ isPage = false }) => {
    const [devices] = useState<Device[]>(MOCK_DEVICES);
    const totalPower = devices.reduce((acc, dev) => acc + dev.power, 0);

    return (
        <>
            {!isPage && (
                <header>
                    <div className="container header-content">
                        <div className="logo">
                            <Zap size={28} />
                            <span>Falk Energy</span>
                        </div>
                        <button className="btn btn-ghost">
                            <Settings size={20} />
                        </button>
                    </div>
                </header>
            )}

            <main className="container py-8">
                <div className="mb-8">
                    <h1>Dashboard</h1>
                    <p className="text-muted">Real-time home energy monitoring</p>
                </div>

                {/* Overview Stats */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div className="card bg-gradient-to-br from-bg-card to-[#06b6d411] border-accent-primary/30">
                        <div className="card-title text-accent-primary">Total Power Usage</div>
                        <div className="flex items-baseline gap-2">
                            <span className="text-4xl font-bold text-white">{totalPower.toFixed(1)}</span>
                            <span className="text-lg text-muted">W</span>
                        </div>
                    </div>

                    <div className="card">
                        <div className="card-title">Active Devices</div>
                        <div className="text-4xl font-bold text-white">
                            {devices.filter(d => d.state).length}
                            <span className="text-lg text-muted font-normal ml-2">/ {devices.length}</span>
                        </div>
                    </div>

                    <div className="card">
                        <div className="card-title">Est. Cost (Today)</div>
                        <div className="text-4xl font-bold text-white">
                            €1.24
                        </div>
                    </div>
                </div>

                {/* Charts Section */}
                <div className="mb-8 h-[400px]">
                    <EnergyChart data={MOCK_CHART_DATA} title="Power Consumption Trend (24h)" />
                </div>

                {/* Devices Grid */}
                <div className="mb-6 flex items-center gap-2">
                    <h2>Connected Devices</h2>
                </div>

                <div className="grid-dashboard">
                    {devices.map(device => (
                        <DeviceCard key={device.id} device={device} />
                    ))}
                </div>
            </main>
        </>
    );
};
