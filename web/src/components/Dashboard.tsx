import React, { useState } from 'react';
import { Search } from 'lucide-react';
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
        today: 1.2,
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
        today: 4.5,
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
        today: 0.8,
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
        today: 1.1,
        updatedAt: Date.now()
    }
];

const generateChartData = () => {
    const data = [];
    const now = new Date();
    for (let i = 24; i >= 0; i--) {
        const time = new Date(now.getTime() - i * 60 * 60 * 1000);
        const hour = time.getHours();

        // Simulate higher usage during day/evening (8am-11pm) and low at night
        let baseValue = 200;
        if (hour >= 7 && hour <= 23) {
            baseValue = 400 + Math.random() * 300; // Active hours
            if (hour >= 18 && hour <= 21) baseValue += 400; // Evening peak
        } else {
            baseValue = 150 + Math.random() * 50; // Night base
        }

        data.push({
            time: time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            value: Math.floor(baseValue),
        });
    }
    return data;
};

const MOCK_CHART_DATA = generateChartData();

interface DashboardProps {
    isPage?: boolean;
}

export const Dashboard: React.FC<DashboardProps> = () => {
    const [devices, setDevices] = useState<Device[]>(MOCK_DEVICES);

    const handleToggleDevice = (id: string) => {
        setDevices(prev => prev.map(d =>
            d.id === id ? { ...d, state: !d.state } : d
        ));
    };

    const activeCount = devices.filter(d => d.state).length;
    // Calculate power only for active devices
    const totalPower = devices.filter(d => d.state).reduce((acc, dev) => acc + dev.power, 0);

    return (
        <main className="container py-6 flex-1">
            {/* Overview Section */}

            <div className="mb-6">
                <h2 className="d-flex align-items-center mt-3 mb-3 gap-2 fs-4">
                    <Search className="text-success" size={20} />
                    Overview
                </h2>

                <div className="bg-[#09090b] border border-[#27272a] rounded-[2rem] overflow-hidden">
                    <div className="row g-0 px-2 py-3">
                        {/* Stats Row */}
                        <div className="col-4 px-4 py-2">
                            <div className="text-[12px] text-[#71717a] uppercase tracking-widest mb-1">Active</div>
                            <div className="flex items-baseline gap-1">
                                <span className="text-3xl font-bold text-white tracking-tight">{activeCount}</span>
                                <span className="text-sm text-[#52525b]">/ {devices.length}</span>
                            </div>
                        </div>

                        <div className="col-4 px-4 py-2">
                            <div className="text-[12px] text-[#71717a] uppercase tracking-widest mb-1">Power</div>
                            <div className="flex items-baseline gap-1">
                                <span className="text-3xl font-bold text-white tracking-tight">{totalPower.toFixed(0)}</span>
                                <span className="text-sm text-[#52525b]">W</span>
                            </div>
                        </div>

                        <div className="col-4 px-4 py-2">
                            <div className="text-[12px] text-[#71717a] uppercase tracking-widest mb-1">Cost</div>
                            <div className="text-3xl font-bold text-white tracking-tight">€1.24</div>
                        </div>
                    </div>

                    {/* Integrated Chart - More compact */}
                    <div className="p-3 border-t border-[#27272a]">
                        <div className="h-[180px] w-full">
                            <EnergyChart data={MOCK_CHART_DATA} />
                        </div>
                    </div>
                </div>
            </div>

            {/* Devices */}
            <div style={{ display: 'flex', flexDirection: 'column', marginTop: '15px' }}>
                <h2>Devices</h2>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                {devices.map(device => (
                    <DeviceCard key={device.id} device={device} onToggle={handleToggleDevice} />
                ))}
            </div>
        </main>
    );
};
