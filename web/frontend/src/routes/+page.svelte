<script lang="ts">
    import { onMount } from 'svelte';
    import ExerciseCard from '$lib/components/ExerciseCard.svelte';
    import FeedbackModal from '$lib/components/FeedbackModal.svelte';

    interface LoggedSet {
        reps: number;
        weight: number;
    }

    interface PrescribedSet {
        prescribed_reps: number | null;
        prescribed_weight: number | null;
    }

    interface Exercise {
        name: string;
        prescribed_sets: PrescribedSet[];
        logged_sets: LoggedSet[];
        is_started: boolean;
        is_completed: boolean;
    }

    interface CurrentWorkout {
        week_index: number;
        workout_index: number;
        exercises: Exercise[];
    }

    interface SetInput {
        weight: number;
        reps: number;
    }

    let workout: CurrentWorkout | null = null;
    let loading = true;
    let error = '';
    let setInputs: Record<string, Record<number, SetInput>> = {};
    
    let showFeedbackModal = false;
    let feedbackExerciseName = '';

    onMount(async () => {
        await loadWorkout();
    });

    async function loadWorkout() {
        loading = true;
        error = '';
        
        try {
            const response = await fetch('/api/current-workout');
            if (!response.ok) throw new Error('Failed to fetch workout');
            
            workout = await response.json();
            
            if (workout) {
                setInputs = {};
                workout.exercises.forEach(exercise => {
                    setInputs[exercise.name] = {};
                    for (let i = exercise.logged_sets.length; i < exercise.prescribed_sets.length; i++) {
                        const prescribed = exercise.prescribed_sets[i];
                        setInputs[exercise.name][i] = {
                            weight: prescribed.prescribed_weight ?? 0,
                            reps: prescribed.prescribed_reps ?? 0
                        };
                    }
                });
            }
        } catch (e) {
            error = e instanceof Error ? e.message : 'Unknown error';
        } finally {
            loading = false;
        }
    }

    async function completeSet(exerciseName: string, setIndex: number) {
        const input = setInputs[exerciseName][setIndex];
        
        if (!input || input.weight < 0 || input.reps <= 0) {
            error = 'Please enter valid weight and reps';
            return;
        }

        try {
            const response = await fetch('/api/log-set', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    exercise: exerciseName,
                    weight: input.weight,
                    reps: input.reps
                })
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Failed to log set');
            }

            await loadWorkout();
            error = '';
        } catch (e) {
            error = e instanceof Error ? e.message : 'Failed to log set';
        }
    }

    function openFeedbackModal(exerciseName: string) {
        feedbackExerciseName = exerciseName;
        showFeedbackModal = true;
    }

    function closeFeedbackModal() {
        showFeedbackModal = false;
        feedbackExerciseName = '';
    }

    async function submitFeedback(feedback: any) {
        try {
            const response = await fetch('/api/complete-exercise', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    exercise: feedbackExerciseName,
                    joint_pain: feedback.joint_pain,
                    pump: feedback.pump,
                    workload: feedback.workload
                })
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Failed to complete exercise');
            }

            closeFeedbackModal();
            await loadWorkout();
            error = '';
        } catch (e) {
            error = e instanceof Error ? e.message : 'Failed to complete exercise';
        }
    }

    async function completeWorkout() {
        try {
            const response = await fetch('/api/complete-workout', {
                method: 'POST'
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Failed to complete workout');
            }

            await loadWorkout();
            error = '';
        } catch (e) {
            error = e instanceof Error ? e.message : 'Failed to complete workout';
        }
    }

    function canCompleteWorkout(): boolean {
        return workout?.exercises.every(e => e.is_completed) ?? false;
    }
</script>

<main class="container mx-auto max-w-2xl p-4">
    <h1 class="text-4xl font-bold text-center mb-6 text-primary">💪 Muscle API</h1>

    {#if loading}
        <div class="flex justify-center">
            <span class="loading loading-spinner loading-lg"></span>
        </div>
    {:else if error}
        <div class="alert alert-error">
            <span>{error}</span>
            <button class="btn btn-sm" on:click={loadWorkout}>Retry</button>
        </div>
    {:else if workout}
        <div class="hero bg-gradient-to-r from-purple-500 to-pink-500 rounded-2xl mb-6 text-white">
            <div class="hero-content text-center py-8">
                <div>
                    <h2 class="text-3xl font-bold">Week {workout.week_index + 1}, Workout {workout.workout_index + 1}</h2>
                </div>
            </div>
        </div>

        <div class="space-y-6">
            {#each workout.exercises as exercise}
                <ExerciseCard 
                    {exercise}
                    setInputs={setInputs[exercise.name]}
                    onCompleteSet={(setIndex) => completeSet(exercise.name, setIndex)}
                    onCompleteExercise={() => openFeedbackModal(exercise.name)}
                />
            {/each}
        </div>

        {#if canCompleteWorkout()}
            <button class="btn btn-success btn-lg btn-block mt-8 shadow-lg" on:click={completeWorkout}>
                🎉 Complete Workout
            </button>
        {/if}
    {/if}
</main>

{#if showFeedbackModal}
    <FeedbackModal 
        exerciseName={feedbackExerciseName}
        onSubmit={submitFeedback}
        onClose={closeFeedbackModal}
    />
{/if}

