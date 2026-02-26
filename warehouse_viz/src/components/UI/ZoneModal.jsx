import { useEffect, useMemo, useState } from 'react';

const formatRange = (min, max) => (min === max ? `${min}` : `${min}-${max}`);

export const ZoneModal = ({ zone, onClose, apiUrl }) => {
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const boundsQuery = useMemo(() => {
        if (!zone) return '';
        const params = new URLSearchParams({
            row_min: zone.rowMin,
            row_max: zone.rowMax,
            col_min: zone.colMin,
            col_max: zone.colMax,
            layer_min: zone.layerMin,
            layer_max: zone.layerMax,
        });
        return params.toString();
    }, [zone]);

    useEffect(() => {
        if (!zone || !apiUrl) return;
        setLoading(true);
        setError('');
        fetch(`${apiUrl}/zone/inventory?${boundsQuery}`)
            .then((response) => response.json())
            .then((data) => {
                setItems(Array.isArray(data.zone_items) ? data.zone_items : []);
            })
            .catch((err) => {
                console.error('Zone inventory error', err);
                setError('Unable to load inventory');
            })
            .finally(() => setLoading(false));
    }, [zone, apiUrl, boundsQuery]);

    if (!zone) return null;

    return (
        <div className="zone-modal" role="dialog" aria-modal="true">
            <div className="zone-modal-content">
                <div className="zone-modal-header">
                    <div>
                        <h3>{zone.name}</h3>
                        <p className="text-xs text-gray-400">
                            Rows {formatRange(zone.rowMin, zone.rowMax)}, Cols {formatRange(zone.colMin, zone.colMax)}, Layers {formatRange(zone.layerMin, zone.layerMax)}
                        </p>
                    </div>
                    <button type="button" onClick={onClose}>Close</button>
                </div>
                <div className="zone-modal-body">
                    {loading && <p className="text-xs text-gray-500">Loading…</p>}
                    {error && <p className="text-xs text-red-500">{error}</p>}
                    {!loading && !error && items.length === 0 && (
                        <p className="text-xs text-gray-500">No scans for this zone yet.</p>
                    )}
                    {!loading && items.length > 0 && (
                        <div className="zone-items">
                            {items.map((item, index) => (
                                <div key={`${item.barcode}-${index}`} className="zone-item">
                                    <div className="zone-item-row">
                                        <span className="zone-item-label">SKU</span>
                                        <span className="zone-item-value">{item.barcode}</span>
                                    </div>
                                    <div className="zone-item-row">
                                        <span className="zone-item-label">Quantity</span>
                                        <span className="zone-item-value">{item.quantity}</span>
                                    </div>
                                    <div className="zone-item-row">
                                        <span className="zone-item-label">Slot</span>
                                        <span className="zone-item-value">
                                            R{item.slot?.row} C{item.slot?.col} L{item.slot?.layer}
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
