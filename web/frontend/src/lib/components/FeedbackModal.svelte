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

