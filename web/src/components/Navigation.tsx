import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { cn } from '../helpers/cn';

export const Navigation: React.FC = () => {
    const navigate = useNavigate();
    const location = useLocation();

    const navItems = [
        { path: '/', label: 'Dashboard', icon: 'fa-solid fa-gauge' },
        { path: '/analytics', label: 'Analytics', icon: 'fa-solid fa-chart-line' },
    ];

    return (
        <header className="sticky top-0 z-50 w-full border-b border-[#27272a] bg-[#09090b]">
            <div className="container flex h-16 items-center justify-between">
                <div className="d-flex align-items-center gap-2 font-bold text-lg tracking-tight">
                    <span className="text-[#22c55e]">FALK</span>
                </div>

                <nav className="d-flex align-items-center gap-2">
                    {navItems.map((item) => {
                        const isActive = location.pathname === item.path;
                        return (
                            <button
                                key={item.path}
                                onClick={() => navigate(item.path)}
                                className={cn(
                                    "btn d-flex align-items-center gap-2",
                                    isActive ? "btn-success" : "btn-outline-secondary text-light"
                                )}
                            >
                                <i className={item.icon}></i>
                                {item.label}
                            </button>
                        );
                    })}
                </nav>
            </div>
        </header>
    );
};
