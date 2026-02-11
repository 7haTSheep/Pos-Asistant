import React, { useState, useEffect } from 'react';
import { HelpCircle, X } from 'lucide-react';
import { useStore } from '../../store/store';

const shortcuts = [
    {
        category: 'Movement', items: [
            { keys: ['↑', '↓', '←', '→'], desc: 'Move selected object (0.5 units)' },
            { keys: ['Shift', '+', '↑↓←→'], desc: 'Fine move (0.1 units)' },
        ]
    },
    {
        category: 'Actions', items: [
            { keys: ['R'], desc: 'Rotate 90°' },
            { keys: ['Del'], desc: 'Delete selected object' },
            { keys: ['Esc'], desc: 'Deselect' },
        ]
    },
    {
        category: 'Mouse', items: [
            { keys: ['Click + Drag'], desc: 'Move object on floor (edit mode)' },
            { keys: ['Click'], desc: 'Select object' },
            { keys: ['Right Drag'], desc: 'Rotate camera' },
            { keys: ['Scroll'], desc: 'Zoom in/out' },
        ]
    },
    {
        category: 'Other', items: [
            { keys: ['?'], desc: 'Toggle this help panel' },
        ]
    },
];

export const ControlsHelp = () => {
    const [isOpen, setIsOpen] = useState(false);
    const mode = useStore((state) => state.mode);

    useEffect(() => {
        const handleKey = (e) => {
            if (e.key === '?' || (e.key === '/' && e.shiftKey)) {
                e.preventDefault();
                setIsOpen(prev => !prev);
            }
        };
        window.addEventListener('keydown', handleKey);
        return () => window.removeEventListener('keydown', handleKey);
    }, []);

    return (
        <>
            {/* Toggle Button */}
            <button
                onClick={() => setIsOpen(prev => !prev)}
                className="fixed bottom-4 right-4 z-50 w-10 h-10 rounded-full bg-gray-700/80 hover:bg-gray-600 text-white flex items-center justify-center transition-all hover:scale-110 backdrop-blur-sm border border-gray-600/50"
                title="Show controls (?)"
            >
                <HelpCircle size={20} />
            </button>

            {/* Help Panel */}
            {isOpen && (
                <div className="fixed bottom-16 right-4 z-50 w-80 max-h-[70vh] overflow-y-auto bg-gray-900/95 backdrop-blur-md text-white rounded-xl border border-gray-700/50 shadow-2xl">
                    {/* Header */}
                    <div className="flex items-center justify-between p-4 border-b border-gray-700/50">
                        <h3 className="text-sm font-bold uppercase tracking-wider text-gray-300">
                            Controls & Shortcuts
                        </h3>
                        <button
                            onClick={() => setIsOpen(false)}
                            className="text-gray-400 hover:text-white transition"
                        >
                            <X size={16} />
                        </button>
                    </div>

                    {/* Mode indicator */}
                    <div className="px-4 py-2 border-b border-gray-700/50">
                        <div className="flex items-center gap-2 text-xs">
                            <span className={`w-2 h-2 rounded-full ${mode === 'edit' ? 'bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.5)]' : 'bg-gray-500'}`} />
                            <span className="text-gray-400">
                                Current mode: <span className={`font-semibold ${mode === 'edit' ? 'text-emerald-400' : 'text-gray-300'}`}>{mode === 'edit' ? 'Edit' : 'View'}</span>
                            </span>
                        </div>
                        {mode !== 'edit' && (
                            <p className="text-xs text-amber-400/80 mt-1">
                                ⚠ Enable Edit mode to use movement shortcuts
                            </p>
                        )}
                    </div>

                    {/* Shortcuts */}
                    <div className="p-4 space-y-4">
                        {shortcuts.map(group => (
                            <div key={group.category}>
                                <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
                                    {group.category}
                                </h4>
                                <div className="space-y-1.5">
                                    {group.items.map((item, i) => (
                                        <div key={i} className="flex items-center justify-between gap-2">
                                            <span className="text-xs text-gray-400">{item.desc}</span>
                                            <div className="flex items-center gap-1 shrink-0">
                                                {item.keys.map((key, j) => (
                                                    key === '+' ? (
                                                        <span key={j} className="text-gray-500 text-xs">+</span>
                                                    ) : (
                                                        <kbd key={j} className="px-1.5 py-0.5 text-xs bg-gray-700/80 border border-gray-600/50 rounded text-gray-300 font-mono min-w-[24px] text-center">
                                                            {key}
                                                        </kbd>
                                                    )
                                                ))}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </>
    );
};
