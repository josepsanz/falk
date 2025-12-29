import React from 'react';
import { cn } from '../../helpers/cn';

interface TabsProps {
    tabs: { id: string; label: string }[];
    activeTab: string;
    onChange: (id: string) => void;
    className?: string;
}

export const Tabs: React.FC<TabsProps> = ({ tabs, activeTab, onChange, className }) => {
    return (
        <div className={cn("flex space-x-3 p-1", className)}>
            {tabs.map((tab) => (
                <button
                    key={tab.id}
                    onClick={() => onChange(tab.id)}
                    className={cn(
                        "px-5 py-2 rounded border transition-all duration-200 text-sm font-bold uppercase tracking-wider",
                        activeTab === tab.id
                            ? "bg-accent-primary text-black border-accent-primary shadow-[0_0_15px_rgba(34,197,94,0.4)]"
                            : "bg-transparent text-text-secondary border-border-color hover:border-accent-primary hover:text-accent-primary"
                    )}
                >
                    {tab.label}
                </button>
            ))}
        </div>
    );
};
