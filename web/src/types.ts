export interface Device {
    id: string;
    name: string;
    ip: string;
    state: boolean;
    power: number; // Watts
    voltage: number; // Volts
    current: number; // mA
    updatedAt: number;
}

export type DeviceStatus = Pick<Device, 'state' | 'power' | 'voltage' | 'current' | 'updatedAt'>;
