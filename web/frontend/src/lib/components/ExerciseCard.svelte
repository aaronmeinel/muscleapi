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
        
        <div class="space-y-3">
            {#each exercise.prescribed_sets as prescribed, i}
                <div class="card bg-base-200" class:bg-success={i < exercise.logged_sets.length} class:bg-opacity-20={i < exercise.logged_sets.length}>
                    <div class="card-body p-4">
                        <div class="flex justify-between items-center mb-2">
                            <span class="font-semibold">Set {i + 1}</span>
                            {#if i < exercise.logged_sets.length}
                                <span class="text-2xl">✅</span>
                            {/if}
                        </div>

                        {#if i < exercise.logged_sets.length}
                            <!-- Completed set -->
                            <div class="text-lg font-bold text-success">
                                {exercise.logged_sets[i].reps} reps × {exercise.logged_sets[i].weight} kg
                            </div>
                        {:else}
                            <!-- Input form for pending set -->
                            <div class="form-control space-y-2">
                                <div class="grid grid-cols-2 gap-2">
                                    <div>
                                        <label class="label py-1">
                                            <span class="label-text font-semibold">Reps</span>
                                        </label>
                                        <input 
                                            type="number" 
                                            bind:value={setInputs[i].reps}
                                            class="input input-bordered w-full"
                                            min="0"
                                            step="1"
                                        />
                                    </div>
                                    <div>
                                        <label class="label py-1">
                                            <span class="label-text font-semibold">Weight (kg)</span>
                                        </label>
                                        <input 
                                            type="number" 
                                            bind:value={setInputs[i].weight}
                                            class="input input-bordered w-full"
                                            min="0"
                                            step="0.5"
                                        />
                                    </div>
                                </div>
                                <button 
                                    class="btn btn-primary btn-sm"
                                    on:click={() => onCompleteSet(i)}
                                >
                                    ✓ Complete Set
                                </button>
                            </div>
                        {/if}

                        <div class="text-xs text-base-content opacity-60 mt-2">
                            Prescribed: {prescribed.prescribed_reps ?? '?'} reps × {prescribed.prescribed_weight ?? '?'} kg
                        </div>
                    </div>
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

