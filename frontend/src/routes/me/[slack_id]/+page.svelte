<script lang="ts">
  import { onMount } from "svelte";
  import type { PageData } from "./$types";
  import { perlin } from "$lib/perlin.ts";

  let { data }: { data: PageData } = $props();
  console.log(data);

  onMount(() => {
    const canvas = document.getElementById("noise") as HTMLCanvasElement;
    canvas.width = canvas.height = 512;
    let ctx = canvas.getContext("2d") as CanvasRenderingContext2D;

    const GRID_SIZE = 1;
    const RESOLUTION = 512;
    const COLOR_SCALE = 250;

    let pixel_size = canvas.width / RESOLUTION;
    let num_pixels = GRID_SIZE / RESOLUTION;

    for (let y = 0; y < GRID_SIZE; y += num_pixels / GRID_SIZE) {
      for (let x = 0; x < GRID_SIZE; x += num_pixels / GRID_SIZE) {
        let v = Math.abs(perlin.get(x, y) * COLOR_SCALE);
        let visible = 255 * +(v >= 30);
        ctx.fillStyle = `rgb(${visible}, ${visible}, ${visible})`;
        ctx.fillRect(
          (x / GRID_SIZE) * canvas.width,
          (y / GRID_SIZE) * canvas.width,
          pixel_size,
          pixel_size,
        );
      }
    }
  });
</script>

<canvas id="noise"></canvas>
