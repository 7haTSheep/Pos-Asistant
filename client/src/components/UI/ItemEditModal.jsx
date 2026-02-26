import React, { useEffect, useMemo, useState } from 'react';

const toNumber = (value, fallback) => {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
};

const radToDeg = (rad) => (rad * 180) / Math.PI;
const degToRad = (deg) => (deg * Math.PI) / 180;

export const ItemEditModal = ({ item, onClose, onSave, onDelete }) => {
    const initialValues = useMemo(() => {
        const meta = item?.meta || {};
        const rotationDeg = Math.round(radToDeg(item?.rotation?.[1] || 0));
        return {
            width: String(item?.size?.[0] ?? 1),
            itemHeight: String(item?.size?.[1] ?? 1),
            depth: String(item?.size?.[2] ?? 1),
            verticalTopCm: String(meta.verticalTopCm ?? 86),
            verticalBottomCm: String(meta.verticalBottomCm ?? 85),
            heightCm: String(meta.heightCm ?? 1),
            rotationDeg: String(meta.rotationDeg ?? rotationDeg),
            customName: meta.customName ?? '',
            tag: meta.tag ?? '',
            note: meta.note ?? '',
        };
    }, [item]);

    const [form, setForm] = useState(initialValues);

    useEffect(() => {
        setForm(initialValues);
    }, [initialValues]);

    if (!item) return null;

    const setField = (key, value) => {
        setForm((prev) => ({ ...prev, [key]: value }));
    };

    const handleSave = () => {
        const rx = item.rotation?.[0] || 0;
        const rz = item.rotation?.[2] || 0;
        const rotationDeg = toNumber(form.rotationDeg, 0);
        const nextSize = [
            Math.max(0.2, toNumber(form.width, item?.size?.[0] ?? 1)),
            Math.max(0.2, toNumber(form.itemHeight, item?.size?.[1] ?? 1)),
            Math.max(0.2, toNumber(form.depth, item?.size?.[2] ?? 1)),
        ];
        const nextMeta = {
            ...(item.meta || {}),
            verticalTopCm: toNumber(form.verticalTopCm, 86),
            verticalBottomCm: toNumber(form.verticalBottomCm, 85),
            heightCm: toNumber(form.heightCm, 1),
            rotationDeg,
            customName: form.customName.trim(),
            tag: form.tag.trim(),
            note: form.note.trim(),
        };

        onSave({
            size: nextSize,
            rotation: [rx, degToRad(rotationDeg), rz],
            meta: nextMeta,
        });
    };

    return (
        <div className="item-modal-backdrop" onClick={onClose}>
            <div className="item-modal" onClick={(e) => e.stopPropagation()}>
                <h3>Symbol settings</h3>

                <label className="item-modal-row">
                    <span>Width</span>
                    <div className="item-modal-unit">
                        <input
                            type="number"
                            step="0.1"
                            min="0.2"
                            value={form.width}
                            onChange={(e) => setField('width', e.target.value)}
                        />
                        <span>m</span>
                    </div>
                </label>

                <label className="item-modal-row">
                    <span>Item height</span>
                    <div className="item-modal-unit">
                        <input
                            type="number"
                            step="0.1"
                            min="0.2"
                            value={form.itemHeight}
                            onChange={(e) => setField('itemHeight', e.target.value)}
                        />
                        <span>m</span>
                    </div>
                </label>

                <label className="item-modal-row">
                    <span>Depth</span>
                    <div className="item-modal-unit">
                        <input
                            type="number"
                            step="0.1"
                            min="0.2"
                            value={form.depth}
                            onChange={(e) => setField('depth', e.target.value)}
                        />
                        <span>m</span>
                    </div>
                </label>

                <label className="item-modal-row">
                    <span>Vertical position (top)</span>
                    <div className="item-modal-unit">
                        <input
                            type="number"
                            value={form.verticalTopCm}
                            onChange={(e) => setField('verticalTopCm', e.target.value)}
                        />
                        <span>cm</span>
                    </div>
                </label>

                <label className="item-modal-row">
                    <span>Vertical position (bottom)</span>
                    <div className="item-modal-unit">
                        <input
                            type="number"
                            value={form.verticalBottomCm}
                            onChange={(e) => setField('verticalBottomCm', e.target.value)}
                        />
                        <span>cm</span>
                    </div>
                </label>

                <label className="item-modal-row">
                    <span>Height</span>
                    <div className="item-modal-unit">
                        <input
                            type="number"
                            value={form.heightCm}
                            onChange={(e) => setField('heightCm', e.target.value)}
                        />
                        <span>cm</span>
                    </div>
                </label>

                <label className="item-modal-row">
                    <span>Rotation</span>
                    <div className="item-modal-unit">
                        <input
                            type="number"
                            value={form.rotationDeg}
                            onChange={(e) => setField('rotationDeg', e.target.value)}
                        />
                        <span>deg</span>
                    </div>
                </label>

                <label className="item-modal-row">
                    <span>Custom name</span>
                    <input
                        type="text"
                        value={form.customName}
                        onChange={(e) => setField('customName', e.target.value)}
                    />
                </label>

                <label className="item-modal-row">
                    <span>Tag</span>
                    <input
                        type="text"
                        value={form.tag}
                        onChange={(e) => setField('tag', e.target.value)}
                    />
                </label>

                <label className="item-modal-row">
                    <span>Note</span>
                    <input
                        type="text"
                        value={form.note}
                        onChange={(e) => setField('note', e.target.value)}
                    />
                </label>

                <div className="item-modal-actions">
                    {onDelete && (
                        <button type="button" onClick={onDelete}>Delete</button>
                    )}
                    <button type="button" onClick={handleSave}>OK</button>
                    <button type="button" onClick={onClose}>Cancel</button>
                </div>
            </div>
        </div>
    );
};

