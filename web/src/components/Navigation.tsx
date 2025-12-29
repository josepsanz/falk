import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { cn } from '../helpers/cn';

export const Navigation: React.FC = () => {
    const navigate = useNavigate();
    const location = useLocation();

    return (
        <header className="sticky top-0 z-50 w-full border-b border-white/10 bg-black/90 backdrop-blur-md">
            <div className="container relative flex h-16 items-center">
                <div className="font-bold text-xl tracking-tight">
                    <span className="text-accent-primary">FALK</span>
                </div>

                <nav className="absolute left-1/2 -translate-x-1/2 flex items-center gap-2">
                    <button
                        onClick={() => navigate('/')}
                        className={cn(
                            "btn text-uppercase fw-bold me-1",
                            location.pathname === '/'
                                ? "btn-success"
                                : "btn-outline-success"
                        )}
                    >
                        Dashboard
                    </button>

                    <button
                        onClick={() => navigate('/analytics')}
                        className={cn(
                            "btn text-uppercase fw-bold ms-1",
                            location.pathname === '/analytics'
                                ? "btn-success"
                                : "btn-outline-success"
                        )}
                    >
                        Analytics
                    </button>
                </nav>
            </div>
        </header>
    );
};
