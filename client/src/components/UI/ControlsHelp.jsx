import React, { useState, useEffect } from 'react';
import { HelpCircle, X } from 'lucide-react';
import { useStore } from '../../store/store';

const shortcuts = [
    {
        category: 'Movement', items: [
            { keys: ['Up', 'Down', 'Left', 'Right'], desc: 'Move selected object (0.5 units)' },
            { keys: ['Shift', '+', 'Arrows'], desc: 'Fine move (0.1 units)' },
        ]
    },
    {
        category: 'Actions', items: [
            { keys: ['R'], desc: 'Rotate 90 degrees' },
            { keys: ['Del'], desc: 'Delete selected object' },
            { keys: ['Esc'], desc: 'Deselect' },
        ]
    },
    {
        category: 'Mouse', items: [
            { keys: ['Left Drag'], desc: 'Move object on floor' },
            { keys: ['Left Click'], desc: 'Select object' },
            { keys: ['View'], desc: 'Camera is locked to top-down' },
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
                setIsOpen((prev) => !prev);
            }
        };
        window.addEventListener('keydown', handleKey);
        return () => window.removeEventListener('keydown', handleKey);
    }, []);

    return (
        <>
            <button
                onClick={() => setIsOpen((prev) => !prev)}
                className="help-toggle"
                title="Show controls (?)"
            >
                <HelpCircle size={20} />
            </button>

            {isOpen && (
                <div className="help-panel">
                    <div className="help-header">
                        <h3>Controls & Shortcuts</h3>
                        <button
                            onClick={() => setIsOpen(false)}
                            className="help-close"
                        >
                            <X size={16} />
                        </button>
                    </div>

                    <div className="help-mode">
                        <div className="help-mode-row">
                            <span className={`mode-dot ${mode === 'edit' ? 'is-edit' : ''}`} />
                            <span className="help-mode-text">
                                Current mode: <span className={`mode-label ${mode === 'edit' ? 'is-edit' : ''}`}>{mode === 'edit' ? 'Edit' : 'View'}</span>
                            </span>
                        </div>
                        {mode !== 'edit' && (
                            <p className="help-mode-warning">
                                Enable Edit mode to use movement shortcuts
                            </p>
                        )}
                    </div>

                    <div className="help-body">
                        {shortcuts.map((group) => (
                            <div key={group.category} className="help-group">
                                <h4>{group.category}</h4>
                                <div>
                                    {group.items.map((item, i) => (
                                        <div key={i} className="help-row">
                                            <span className="help-desc">{item.desc}</span>
                                            <div className="help-keys">
                                                {item.keys.map((key, j) => (
                                                    key === '+' ? (
                                                        <span key={j} className="help-plus">+</span>
                                                    ) : (
                                                        <kbd key={j} className="help-key">
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
