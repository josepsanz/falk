import React from 'react';
import { ChevronDown } from 'lucide-react';

interface SelectOption {
    id: string;
    label: string;
}

interface SelectProps {
    options: SelectOption[];
    value: string;
    onChange: (value: string) => void;
    placeholder?: string;
    className?: string;
}

export const Select: React.FC<SelectProps> = ({
    options,
    value,
    onChange,
    placeholder = 'Select an option',
    className = ''
}) => {
    return (
        <div className={`relative ${className}`}>
            <select
                value={value}
                onChange={(e) => onChange(e.target.value)}
                className="w-full appearance-none bg-[#18181b] border border-[#27272a] text-white rounded-lg px-4 py-3 pr-10 cursor-pointer hover:border-[#22c55e]/50 focus:outline-none focus:border-[#22c55e] transition-colors"
            >
                {placeholder && (
                    <option value="" disabled>
                        {placeholder}
                    </option>
                )}
                {options.map((option) => (
                    <option key={option.id} value={option.id}>
                        {option.label}
                    </option>
                ))}
            </select>
            <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-zinc-400">
                <ChevronDown size={20} />
            </div>
        </div>
    );
};
