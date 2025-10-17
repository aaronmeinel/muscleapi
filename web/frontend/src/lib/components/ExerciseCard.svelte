<script lang="ts">
    export let exercise: any;
    export let setInputs: Record<number, any>;
    export let onCompleteSet: (setIndex: number) => void;
    export let onCompleteExercise: () => void;

    function canComplete(): boolean {
        return exercise.logged_sets.length === exercise.prescribed_sets.length && !exercise.is_completed;
    }
</script>

<div class="card bg-base-100 shadow-xl" class:border-success={exercise.is_completed} class:border-2={exercise.is_completed}>
    <div class="card-body">
        <h3 class="card-title">
            {exercise.name}
            {#if exercise.is_completed}
                <div class="badge badge-success">Complete</div>
            {/if}
        </h3>
        
        <div class="space-y-2">
            {#each exercise.prescribed_sets as prescribed, i}
                <div class="flex items-center gap-3 p-3 rounded-lg bg-base-200" class:bg-success={i < exercise.logged_sets.length} class:bg-opacity-20={i < exercise.logged_sets.length}>
                    {#if i < exercise.logged_sets.length}
                        <!-- Completed set - single line -->
                        <span class="font-semibold min-w-[60px]">Set {i + 1}</span>
                        <span class="text-lg font-bold text-success flex-grow">
                            {exercise.logged_sets[i].reps} reps × {exercise.logged_sets[i].weight} kg
                        </span>
                        <span class="text-xl">✅</span>
                    {:else}
                        <!-- Input form for pending set - single line -->
                        <span class="font-semibold min-w-[60px]">Set {i + 1}</span>
                        <input 
                            type="number" 
                            bind:value={setInputs[i].reps}
                            class="input input-bordered input-sm w-20"
                            placeholder="Reps"
                            min="0"
                            step="1"
                        />
                        <span class="text-sm">×</span>
                        <input 
                            type="number" 
                            bind:value={setInputs[i].weight}
                            class="input input-bordered input-sm w-24"
                            placeholder="kg"
                            min="0"
                            step="0.5"
                        />
                        <button 
                            class="btn btn-primary btn-sm ml-auto"
                            on:click={() => onCompleteSet(i)}
                        >
                            ✓
                        </button>
                    {/if}
                </div>
            {/each}
        </div>

        {#if canComplete()}
            <button class="btn btn-success btn-block mt-4" on:click={onCompleteExercise}>
                ✓ Complete {exercise.name}
            </button>
        {/if}
    </div>
</div>

