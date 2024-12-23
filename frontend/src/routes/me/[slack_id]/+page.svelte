<script lang="ts">
  import { onMount } from "svelte";
  import type { PageData } from "./$types";

  let { data }: { data: PageData } = $props();
  console.log(data);

  onMount(() => {
    const canvas = document.getElementById("noise") as HTMLCanvasElement;
    const ctx = canvas.getContext("2d") as CanvasRenderingContext2D;
    canvas.width = 300;
    canvas.height = 300;

    const image_data = data.island;
    for (let i = 0; i < image_data.length; i++) {
      for (let j = 0; j < image_data[i].length; j++) {
        ctx.fillStyle = image_data[i][j] === 1 ? "black" : "white";
        ctx.fillRect(i, j, 1, 1);
      }
    }
  });
</script>

<canvas id="noise"></canvas>
