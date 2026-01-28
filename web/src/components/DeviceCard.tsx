import React, { useState } from 'react';
import { Power } from 'lucide-react';
import type { Device } from '../types';
import { cn } from '../helpers/cn';

interface DeviceCardProps {
    device: Device;
    onToggle?: (id: string) => void;
}

export const DeviceCard: React.FC<DeviceCardProps> = ({ device, onToggle }) => {
    const [isOn, setIsOn] = useState(device.state);

    const handleToggle = () => {
        setIsOn(!isOn);
        onToggle?.(device.id);
    };

    return (
        <div
            className={cn("card", isOn ? "border-[#22c55e]/30" : "")}
            style={{
                display: 'flex',
                flexDirection: 'row',
                alignItems: 'center',
                gap: '12px',
                padding: '10px 12px'
            }}
        >
            {/* Power Icon Button */}
            <button
                onClick={handleToggle}
                style={{
                    flexShrink: 0,
                    width: '36px',
                    height: '36px',
                    borderRadius: '8px',
                    border: 'none',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    backgroundColor: isOn ? '#22c55e' : '#27272a',
                    color: isOn ? '#000' : '#71717a'
                }}
                aria-label={isOn ? "Turn Off" : "Turn On"}
            >
                <Power size={18} strokeWidth={2.5} />
            </button>

            {/* Device Info */}
            <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: '14px', fontWeight: 500, color: 'white', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {device.name}
                </div>
                <div style={{ fontSize: '11px', color: '#1f51ff', fontFamily: 'monospace' }}>
                    {device.ip}
                </div>
            </div>

            {/* Stats: Current, Power, Today */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                {/* Current */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <span style={{ fontFamily: 'monospace', fontSize: '13px', color: isOn ? 'white' : '#71717a' }}>
                        {device.current}
                    </span>
                    <span style={{ fontSize: '10px', color: '#71717a' }}>mA</span>
                </div>

                {/* Power */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <span style={{ fontFamily: 'monospace', fontSize: '13px', color: isOn ? 'white' : '#71717a' }}>
                        {device.power.toFixed(0)}
                    </span>
                    <span style={{ fontSize: '10px', color: '#71717a' }}>W</span>
                </div>

                {/* Today */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <span style={{ fontFamily: 'monospace', fontSize: '13px', color: isOn ? 'white' : '#71717a' }}>
                        {device.today.toFixed(1)}
                    </span>
                    <span style={{ fontSize: '10px', color: '#71717a' }}>kWh</span>
                </div>
            </div>
        </div>
    );
};
