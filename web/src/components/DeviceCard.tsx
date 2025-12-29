import React from 'react';
import { Zap, Activity, Power as PowerIcon } from 'lucide-react';
import type { Device } from '../types';
import { cn } from '../helpers/cn';

interface DeviceCardProps {
    device: Device;
}

export const DeviceCard: React.FC<DeviceCardProps> = ({ device }) => {

    return (
        <div className={cn("card relative overflow-hidden group")}>
            <div className="flex justify-between items-start mb-4">
                <div>
                    <div className="flex items-center gap-2 mb-1">
                        <h3 className="text-lg font-semibold text-white">{device.name}</h3>
                        {device.state && (
                            <span className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                            </span>
                        )}
                    </div>
                    <div className="text-xs text-muted font-mono opacity-60 break-all">{device.ip}</div>
                </div>
                <div className={cn(
                    "p-2 rounded-full bg-opacity-10 transition-colors",
                    device.state ? "bg-green-500 text-green-400" : "bg-zinc-700 text-zinc-500"
                )}>
                    <PowerIcon size={20} />
                </div>
            </div>

            <div className="grid grid-cols-2 gap-4 mt-4">
                <div className="col-span-2">
                    <div className="card-title flex items-center gap-1.5">
                        <Zap size={14} className="text-accent-primary" />
                        Power Usage
                    </div>
                    <div className="flex items-baseline">
                        <span className={cn("card-value", device.state ? "text-white" : "text-zinc-600")}>
                            {device.power.toFixed(1)}
                        </span>
                        <span className="card-unit">W</span>
                    </div>
                </div>

                <div>
                    <div className="card-title flex items-center gap-1.5">
                        <Activity size={14} className="text-zinc-500" />
                        Voltage
                    </div>
                    <div className="flex items-baseline">
                        <span className="text-lg font-mono text-zinc-300">
                            {device.voltage.toFixed(1)}
                        </span>
                        <span className="card-unit text-xs">V</span>
                    </div>
                </div>

                <div>
                    <div className="card-title flex items-center gap-1.5">
                        <Activity size={14} className="text-zinc-500" />
                        Current
                    </div>
                    <div className="flex items-baseline">
                        <span className="text-lg font-mono text-zinc-300">
                            {device.current}
                        </span>
                        <span className="card-unit text-xs">mA</span>
                    </div>
                </div>
            </div>

            {/* Background decoration */}
            <div className="absolute -bottom-10 -right-10 w-32 h-32 bg-accent-primary opacity-5 rounded-full blur-3xl group-hover:opacity-10 transition-opacity pointer-events-none"></div>
        </div>
    );
};
