<script lang="ts">
  import '../app.css';
  import { onMount } from 'svelte';

  let theme = 'light';

  onMount(() => {
    // Load saved theme or default to light
    theme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', theme);
  });

  function toggleTheme() {
    theme = theme === 'light' ? 'dark' : 'light';
    localStorage.setItem('theme', theme);
    document.documentElement.setAttribute('data-theme', theme);
  }
</script>

<div class="relative min-h-screen">
  <!-- Theme toggle button in top-right corner -->
  <button
    on:click={toggleTheme}
    class="fixed top-4 right-4 btn btn-circle btn-sm z-50"
    aria-label="Toggle theme"
  >
    {#if theme === 'light'}
      🌙
    {:else}
      ☀️
    {/if}
  </button>

  <slot />
</div>