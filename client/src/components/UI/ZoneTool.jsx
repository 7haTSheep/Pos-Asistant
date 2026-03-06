import React from 'react';
import { useStore } from '../../store/store';
import { Square } from 'lucide-react';

export const ZoneTool = ({ apiUrl }) => {
    const zoneToolActive = useStore((state) => state.zoneToolActive);
    const setZoneToolActive = useStore((state) => state.setZoneToolActive);
    const startZoneDrawing = useStore((state) => state.startZoneDrawing);
    const updateZoneDrawing = useStore((state) => state.updateZoneDrawing);
    const finishZoneDrawing = useStore((state) => state.finishZoneDrawing);
    const cancelZoneDrawing = useStore((state) => state.cancelZoneDrawing);
    const zoneDrawing = useStore((state) => state.zoneDrawing);
    const zones = useStore((state) => state.zones);
    const removeZone = useStore((state) => state.removeZone);
    const [selectedZone, setSelectedZone] = React.useState(null);

    const handleToggleZoneTool = () => {
        if (zoneToolActive && zoneDrawing) {
            cancelZoneDrawing();
        }
        setZoneToolActive(!zoneToolActive);
    };

    const handleCanvasPointerDown = (point) => {
        if (!zoneToolActive || zoneDrawing) return;
        startZoneDrawing(point);
    };

    const handleCanvasPointerMove = (point) => {
        if (!zoneToolActive || !zoneDrawing) return;
        updateZoneDrawing(point);
    };

    const handleCanvasPointerUp = () => {
        if (!zoneToolActive || !zoneDrawing) return;
        finishZoneDrawing();
    };

    React.useEffect(() => {
        if (!zoneToolActive) {
            setSelectedZone(null);
        }
    }, [zoneToolActive]);

    return (
        <div className="zone-tool-container">
            {/* Zone Tool Toggle Button */}
            <button
                onClick={handleToggleZoneTool}
                className={`zone-tool-toggle ${zoneToolActive ? 'active' : ''}`}
                title="Draw Zone"
            >
                <Square size={20} />
                <span>Zone</span>
            </button>

            {/* Zone Drawing Indicator */}
            {zoneDrawing && (
                <div className="zone-drawing-indicator">
                    <p className="text-xs text-gray-300">Drag to draw zone rectangle</p>
                    <button
                        onClick={cancelZoneDrawing}
                        className="text-xs text-red-400 hover:text-red-300"
                    >
                        Cancel
                    </button>
                </div>
            )}

            {/* Zones List */}
            {zones.length > 0 && (
                <div className="zones-list">
                    <h4 className="text-xs font-semibold text-gray-400 uppercase mb-2">Zones</h4>
                    {zones.map((zone) => (
                        <div
                            key={zone.id}
                            className={`zone-item ${selectedZone?.id === zone.id ? 'selected' : ''}`}
                            onClick={() => setSelectedZone(zone)}
                        >
                            <div className="zone-item-info">
                                <span className="zone-item-name">{zone.name}</span>
                                <span className="zone-item-bounds text-xs text-gray-500">
                                    R{zone.rowMin}-{zone.rowMax}, C{zone.colMin}-{zone.colMax}
                                </span>
                            </div>
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    removeZone(zone.id);
                                    if (selectedZone?.id === zone.id) setSelectedZone(null);
                                }}
                                className="zone-item-delete text-xs text-red-400 hover:text-red-300"
                            >
                                ×
                            </button>
                        </div>
                    ))}
                </div>
            )}

            {/* Zone Detail Modal */}
            {selectedZone && (
                <div className="zone-detail-modal">
                    <div className="zone-detail-content">
                        <div className="zone-detail-header">
                            <h3>{selectedZone.name}</h3>
                            <button onClick={() => setSelectedZone(null)}>×</button>
                        </div>
                        <div className="zone-detail-body">
                            <p className="text-sm text-gray-400 mb-4">
                                Rows {selectedZone.rowMin}–{selectedZone.rowMax}, 
                                Cols {selectedZone.colMin}–{selectedZone.colMax}
                            </p>
                            {apiUrl && (
                                <a
                                    href={`${apiUrl}/zone/inventory?row_min=${selectedZone.rowMin}&row_max=${selectedZone.rowMax}&col_min=${selectedZone.colMin}&col_max=${selectedZone.colMax}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-xs text-blue-400 hover:text-blue-300"
                                >
                                    View Inventory →
                                </a>
                            )}
                        </div>
                    </div>
                </div>
            )}

            <style jsx>{`
                .zone-tool-container {
                    position: absolute;
                    bottom: 20px;
                    left: 20px;
                    z-index: 100;
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                }

                .zone-tool-toggle {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    padding: 10px 16px;
                    background: #1f2937;
                    border: 1px solid #374151;
                    border-radius: 8px;
                    color: #9ca3af;
                    cursor: pointer;
                    transition: all 0.2s;
                    font-size: 14px;
                }

                .zone-tool-toggle:hover {
                    background: #374151;
                    color: #fff;
                }

                .zone-tool-toggle.active {
                    background: #2563eb;
                    border-color: #3b82f6;
                    color: #fff;
                }

                .zone-drawing-indicator {
                    background: #1f2937;
                    border: 1px solid #374151;
                    border-radius: 8px;
                    padding: 12px;
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                }

                .zones-list {
                    background: #1f2937;
                    border: 1px solid #374151;
                    border-radius: 8px;
                    padding: 12px;
                    max-height: 200px;
                    overflow-y: auto;
                }

                .zone-item {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding: 8px;
                    margin-bottom: 4px;
                    background: #374151;
                    border-radius: 6px;
                    cursor: pointer;
                    transition: background 0.2s;
                }

                .zone-item:hover {
                    background: #4b5563;
                }

                .zone-item.selected {
                    background: #2563eb;
                }

                .zone-item-info {
                    display: flex;
                    flex-direction: column;
                    gap: 2px;
                }

                .zone-item-name {
                    font-size: 13px;
                    font-weight: 500;
                }

                .zone-item-bounds {
                    font-size: 11px;
                }

                .zone-item-delete {
                    background: none;
                    border: none;
                    font-size: 18px;
                    cursor: pointer;
                    padding: 0 4px;
                }

                .zone-detail-modal {
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(0, 0, 0, 0.7);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 1000;
                }

                .zone-detail-content {
                    background: #1f2937;
                    border: 1px solid #374151;
                    border-radius: 12px;
                    padding: 20px;
                    min-width: 300px;
                    max-width: 500px;
                }

                .zone-detail-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 16px;
                }

                .zone-detail-header h3 {
                    font-size: 18px;
                    font-weight: 600;
                }

                .zone-detail-header button {
                    background: none;
                    border: none;
                    color: #9ca3af;
                    font-size: 24px;
                    cursor: pointer;
                    padding: 0;
                    line-height: 1;
                }

                .zone-detail-header button:hover {
                    color: #fff;
                }

                .zone-detail-body {
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                }
            `}</style>
        </div>
    );
};
