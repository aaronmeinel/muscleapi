<script lang="ts">
    export let exerciseName: string;
    export let onSubmit: (feedback: any) => void;
    export let onClose: () => void;

    let feedback = {
        joint_pain: 0,
        pump: 2,
        workload: 2
    };

    function handleSubmit() {
        onSubmit(feedback);
    }

    const labels = ['None', 'Low', 'Med', 'High'];
    const pumpLabels = ['None', 'Low', 'Good', 'Insane'];
    const workloadLabels = ['Easy', 'Moderate', 'Hard', 'Max'];
</script>

<div class="modal modal-open">
    <div class="modal-box">
        <h3 class="font-bold text-2xl mb-2">Complete {exerciseName}</h3>
        <p class="text-sm opacity-70 mb-6">Rate your experience (0-3)</p>

        <div class="space-y-6">
            <!-- Joint Pain -->
            <div class="form-control">
                <div class="flex justify-between items-center mb-2">
                    <label class="label-text text-lg font-semibold">💢 Joint Pain</label>
                    <span class="badge badge-lg">{feedback.joint_pain}/3</span>
                </div>
                <input 
                    type="range" 
                    min="0" 
                    max="3" 
                    bind:value={feedback.joint_pain}
                    class="range range-error"
                    step="1"
                />
                <div class="w-full flex justify-between text-xs px-2 opacity-70">
                    {#each labels as label}
                        <span>{label}</span>
                    {/each}
                </div>
            </div>

            <!-- Pump -->
            <div class="form-control">
                <div class="flex justify-between items-center mb-2">
                    <label class="label-text text-lg font-semibold">💪 Pump</label>
                    <span class="badge badge-lg">{feedback.pump}/3</span>
                </div>
                <input 
                    type="range" 
                    min="0" 
                    max="3" 
                    bind:value={feedback.pump}
                    class="range range-secondary"
                    step="1"
                />
                <div class="w-full flex justify-between text-xs px-2 opacity-70">
                    {#each pumpLabels as label}
                        <span>{label}</span>
                    {/each}
                </div>
            </div>

            <!-- Workload -->
            <div class="form-control">
                <div class="flex justify-between items-center mb-2">
                    <label class="label-text text-lg font-semibold">🔥 Workload/RPE</label>
                    <span class="badge badge-lg">{feedback.workload}/3</span>
                </div>
                <input 
                    type="range" 
                    min="0" 
                    max="3" 
                    bind:value={feedback.workload}
                    class="range range-warning"
                    step="1"
                />
                <div class="w-full flex justify-between text-xs px-2 opacity-70">
                    {#each workloadLabels as label}
                        <span>{label}</span>
                    {/each}
                </div>
            </div>
        </div>

        <div class="modal-action">
            <button class="btn btn-ghost" on:click={onClose}>
                Cancel
            </button>
            <button class="btn btn-success" on:click={handleSubmit}>
                ✓ Complete Exercise
            </button>
        </div>
    </div>
    <div class="modal-backdrop" on:click={onClose}></div>
</div>

<style>
    .modal-open {
        display: flex;
        align-items: center;
        justify-content: center;
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        z-index: 1050;
        overflow: hidden;
    }

    .modal-box {
        background: white;
        border-radius: 12px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        max-width: 500px;
        width: 100%;
        padding: 2rem;
        position: relative;
    }

    .modal-backdrop {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.7);
        z-index: 1040;
    }

    .font-bold {
        font-weight: 700;
    }

    .text-2xl {
        font-size: 1.5rem;
    }

    .mb-2 {
        margin-bottom: 0.5rem;
    }

    .text-sm {
        font-size: 0.875rem;
    }

    .opacity-70 {
        opacity: 0.7;
    }

    .mb-6 {
        margin-bottom: 1.5rem;
    }

    .space-y-6 > * {
        margin-bottom: 1.5rem;
    }

    .form-control {
        display: flex;
        flex-direction: column;
    }

    .label-text {
        font-size: 1.125rem;
        margin-bottom: 0.5rem;
    }

    .badge {
        padding: 0.5rem 1rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 500;
        display: inline-block;
        min-width: 2.5rem;
        text-align: center;
    }

    .range {
        -webkit-appearance: none;
        appearance: none;
        width: 100%;
        height: 8px;
        border-radius: 4px;
        background: #e0e0e0;
        outline: none;
    }

    .range-error {
        background: linear-gradient(to right, #dc3545 0%, #ffc107 100%);
    }

    .range-secondary {
        background: linear-gradient(to right, #007bff 0%, #6610f2 100%);
    }

    .range-warning {
        background: linear-gradient(to right, #28a745 0%, #ffc107 100%);
    }

    .range::-webkit-slider-thumb {
        -webkit-appearance: none;
        appearance: none;
        width: 16px;
        height: 16px;
        border-radius: 50%;
        background: white;
        cursor: pointer;
        border: 2px solid currentColor;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
    }

    .range::-moz-range-thumb {
        width: 16px;
        height: 16px;
        border-radius: 50%;
        background: white;
        cursor: pointer;
        border: 2px solid currentColor;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
    }

    .text-xs {
        font-size: 0.75rem;
    }

    .px-2 {
        padding-left: 0.5rem;
        padding-right: 0.5rem;
    }

    .btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        transition: background 0.2s, transform 0.2s;
    }

    .btn-ghost {
        background: transparent;
        color: #333;
        border: 2px solid #333;
    }

    .btn-success {
        background: #28a745;
        color: white;
        border: none;
    }

    .btn-ghost:hover {
        background: #333;
        color: white;
    }

    .btn-success:hover {
        background: #218838;
    }

    .modal-action {
        display: flex;
        justify-content: flex-end;
        gap: 1rem;
    }
</style>