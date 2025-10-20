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

    function selectValue(category: 'joint_pain' | 'pump' | 'workload', value: number) {
        feedback[category] = value;
    }

    const painLabels = ['None', 'Low', 'Med', 'High'];
    const pumpLabels = ['None', 'Low', 'Good', 'Insane'];
    const workloadLabels = ['Easy', 'Pretty good', 'Pushed my limits', 'Too much'];
</script>

<div class="modal modal-open">
    <div class="modal-box max-w-md rounded">
        <h3 class="font-semibold text-lg mb-6">Complete {exerciseName}</h3>
        
        <!-- Joint Pain -->
        <div class="mb-6">
            <label class="text-sm font-medium mb-3 flex items-center gap-2">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                Joint Pain
            </label>
            <div class="grid grid-cols-4 gap-2">
                {#each [0, 1, 2, 3] as value}
                    <button
                        type="button"
                        class="btn h-14 rounded flex flex-col justify-center items-center gap-0.5"
                        class:btn-primary={feedback.joint_pain === value}
                        class:btn-outline={feedback.joint_pain !== value}
                        on:click={() => selectValue('joint_pain', value)}
                    >
                        <span class="text-lg font-semibold">{value}</span>
                        <span class="text-[10px] opacity-60">{painLabels[value]}</span>
                    </button>
                {/each}
            </div>
        </div>

        <!-- Pump -->
        <div class="mb-6">
            <label class="text-sm font-medium mb-3 flex items-center gap-2">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Pump
            </label>
            <div class="grid grid-cols-4 gap-2">
                {#each [0, 1, 2, 3] as value}
                    <button
                        type="button"
                        class="btn h-14 rounded flex flex-col justify-center items-center gap-0.5"
                        class:btn-secondary={feedback.pump === value}
                        class:btn-outline={feedback.pump !== value}
                        on:click={() => selectValue('pump', value)}
                    >
                        <span class="text-lg font-semibold">{value}</span>
                        <span class="text-[10px] opacity-60">{pumpLabels[value]}</span>
                    </button>
                {/each}
            </div>
        </div>

        <!-- Workload -->
        <div class="mb-6">
            <label class="text-sm font-medium mb-3 flex items-center gap-2">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                Workload
            </label>
            <div class="grid grid-cols-4 gap-2">
                {#each [0, 1, 2, 3] as value}
                    <button
                        type="button"
                        class="btn h-14 rounded flex flex-col justify-center items-center gap-0.5"
                        class:btn-accent={feedback.workload === value}
                        class:btn-outline={feedback.workload !== value}
                        on:click={() => selectValue('workload', value)}
                    >
                        <span class="text-lg font-semibold">{value}</span>
                        <span class="text-[10px] opacity-60">{workloadLabels[value]}</span>
                    </button>
                {/each}
            </div>
        </div>

        <div class="modal-action">
            <button class="btn btn-ghost rounded" on:click={onClose}>
                Cancel
            </button>
            <button class="btn btn-success rounded" on:click={handleSubmit}>
                Complete Exercise
            </button>
        </div>
    </div>
    <div class="modal-backdrop" on:click={onClose}></div>
</div>