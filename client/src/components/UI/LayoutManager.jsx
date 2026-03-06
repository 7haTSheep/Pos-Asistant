import { useCallback, useEffect, useState } from 'react';
import { useStore } from '../../store/store';

export const LayoutManager = ({ apiUrl }) => {
    const serializeLayout = useStore((state) => state.serializeLayout);
    const loadLayout = useStore((state) => state.loadLayout);
    const [plans, setPlans] = useState([]);
    const [planName, setPlanName] = useState('');
    const [status, setStatus] = useState('');
    const [saving, setSaving] = useState(false);
    const [loadingPlans, setLoadingPlans] = useState(false);

    const fetchPlans = useCallback(async () => {
        if (!apiUrl) {
            setPlans([]);
            return;
        }
        setLoadingPlans(true);
        try {
            const response = await fetch(`${apiUrl}/floorplan`);
            if (response.ok) {
                const data = await response.json();
                setPlans(data);
            } else {
                console.error('Failed to load floor plans', response.statusText);
            }
        } catch (error) {
            console.error('Floor plan fetch error', error);
        } finally {
            setLoadingPlans(false);
        }
    }, [apiUrl]);

    useEffect(() => {
        fetchPlans();
    }, [apiUrl, fetchPlans]);

    const handleSave = async () => {
        if (!apiUrl) return;
        if (!planName.trim()) {
            setStatus('Name cannot be empty');
            return;
        }
        setSaving(true);
        setStatus('');
        try {
            const payload = {
                name: planName.trim(),
                layout_json: serializeLayout(),
                activate: true,
            };
            const response = await fetch(`${apiUrl}/floorplan/save`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            if (response.ok) {
                setPlanName('');
                await fetchPlans();
                setStatus('Saved');
            } else {
                setStatus('Save request failed');
            }
        } catch (error) {
            console.error('Save floor plan error', error);
            setStatus('Save failed');
        } finally {
            setSaving(false);
        }
    };

    const handleLoad = async (planId) => {
        if (!apiUrl) return;
        setStatus('');
        try {
            const response = await fetch(`${apiUrl}/floorplan/load/${planId}`, {
                method: 'PUT',
            });
            if (response.ok) {
                const data = await response.json();
                loadLayout(data.layout_json);
                await fetchPlans();
                setStatus(`Loaded plan ${planId}`);
            } else {
                setStatus('Failed to load plan');
            }
        } catch (error) {
            console.error('Load floor plan error', error);
            setStatus('Load failed');
        }
    };

    return (
        <div className="layout-manager">
            <div className="layout-manager-header">
                <h2>Layout Library</h2>
            </div>
            {!apiUrl && <p className="text-xs text-gray-500">Backend not connected — start the server to enable saves.</p>}
            <div className="space-y-2">
                <input
                    value={planName}
                    onChange={(event) => setPlanName(event.target.value)}
                    placeholder="Layout name"
                    className="w-full"
                    disabled={!apiUrl || saving}
                />
                <button
                    onClick={handleSave}
                    disabled={!apiUrl || saving}
                    className="w-full"
                >
                    {saving ? 'Saving…' : 'Save Layout'}
                </button>
            </div>
            {status && (
                <p className="text-xs text-gray-500 mt-2">{status}</p>
            )}
            <div className="mt-3">
                <h3 className="text-xs uppercase text-gray-400 mb-2">Saved plans</h3>
                {loadingPlans && <p className="text-xs text-gray-400">Fetching plans…</p>}
                {!loadingPlans && plans.length === 0 && (
                    <p className="text-xs text-gray-400">No plans saved yet.</p>
                )}
                <div className="space-y-1">
                    {plans.map((plan) => (
                        <div key={plan.id} className="plan-row flex items-center justify-between gap-2">
                            <div>
                                <p className="text-sm font-semibold">{plan.name}</p>
                                <p className="text-xs text-gray-400">
                                    Saved {new Date(plan.created_at).toLocaleString()}
                                </p>
                            </div>
                            <div className="flex items-center gap-1">
                                {plan.is_active && (
                                    <span className="text-xs text-emerald-600">Active</span>
                                )}
                                <button
                                    type="button"
                                    onClick={() => handleLoad(plan.id)}
                                    className="text-xs"
                                >
                                    Load
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};
