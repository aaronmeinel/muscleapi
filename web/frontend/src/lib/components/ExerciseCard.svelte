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

<style>
    .exercise-card {
        background: white;
        border: 2px solid #e0e0e0;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }

    .exercise-card.completed {
        background: #d4edda;
        border-color: #28a745;
    }

    .exercise-card h3 {
        margin: 0 0 1rem 0;
        color: #333;
    }

    .sets {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .set-card {
        background: #f8f9fa;
        border: 2px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        transition: all 0.3s;
    }

    .set-card.logged {
        background: #e7f5e7;
        border-color: #28a745;
    }

    .set-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }

    .checkmark {
        font-size: 1.2rem;
    }

    .set-result {
        font-size: 1.1rem;
        color: #28a745;
        font-weight: 600;
        padding: 0.5rem 0;
    }

    .set-inputs {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.5rem;
        margin-bottom: 0.5rem;
    }

    .set-inputs label {
        display: flex;
        flex-direction: column;
        font-size: 0.9rem;
        font-weight: 600;
        color: #555;
    }

    .set-inputs input {
        margin-top: 0.25rem;
        padding: 0.5rem;
        border: 1px solid #ccc;
        border-radius: 4px;
        font-size: 1rem;
    }

    .complete-set-btn {
        grid-column: 1 / -1;
        background: #007bff;
        color: white;
        border: none;
        padding: 0.75rem;
        border-radius: 6px;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        transition: background 0.2s;
    }

    .complete-set-btn:hover {
        background: #0056b3;
    }

    .prescription-hint {
        font-size: 0.85rem;
        color: #6c757d;
        margin-top: 0.5rem;
        font-style: italic;
    }

    .complete-exercise-btn {
        width: 100%;
        background: #28a745;
        color: white;
        border: none;
        padding: 1rem;
        border-radius: 8px;
        font-size: 1.1rem;
        font-weight: 600;
        margin-top: 1rem;
        cursor: pointer;
        transition: background 0.2s;
    }

    .complete-exercise-btn:hover {
        background: #218838;
    }
</style>