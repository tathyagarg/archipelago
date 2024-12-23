<script lang="ts">
  import { onMount } from "svelte";
  import "../../../app.css";

  let { data }: { data: any } = $props();

  const SEAS = "#00000000";
  const LAND = "#359B0B";

  onMount(() => {
    const canvas = document.getElementById("noise") as HTMLCanvasElement;
    const ctx = canvas.getContext("2d") as CanvasRenderingContext2D;
    canvas.width = 600;
    canvas.height = 600;

    const image_data = data.island;
    for (let i = 0; i < image_data.length; i++) {
      for (let j = 0; j < image_data[i].length; j++) {
        ctx.fillStyle = image_data[i][j] === 1 ? LAND : SEAS;
        ctx.fillRect(i * 2, j * 2, 2, 2);
      }
    }
  });

  let times = new Map();
  for (let i = 0; i < data.user.ships.length; i++) {
    times.set(data.user.ships[i].name, data.user.ships[i].hours);
    for (let j = 0; j < data.user.ships[i].updates.length; j++) {
      times.set(
        data.user.ships[i].name,
        times.get(data.user.ships[i].name) +
          data.user.ships[i].updates[j].hours,
      );
    }
  }

  let biggest_ship = { name: "", hours: 0 };
  for (const [key, val] of times) {
    if (val > biggest_ship.hours) {
      biggest_ship = { name: key, hours: val };
    }
  }
</script>

<div id="page">
  <div id="sidebar">
    <div id="pfp-holder">
      <img
        src={data.all.image_192}
        alt="{data.all.display_name}'s PFP"
        id="pfp"
      />
    </div>
    <div id="namebar">
      <h1>{data.all.display_name}</h1>
      <a href="https://hackclub.slack.com/team/U{data.user.id}">
        <img
          src="https://cdn-icons-png.flaticon.com/512/2111/2111615.png"
          alt="slack logo"
          height="30"
        />
      </a>
    </div>
    <h2>Stats</h2>
    <table id="stats">
      <tbody>
        <tr>
          <td>Ships made</td>
          <td>{data.user.ships.length}</td>
        </tr>
        <tr>
          <td>Biggest ship</td>
          <td>
            {biggest_ship.name} ({biggest_ship.hours} hours)
          </td>
        </tr>
        <tr>
          <td>Doubloons</td>
          <td>{data.user.doubloons === -1 ? "Not found" : data.doubloons}</td>
        </tr>
      </tbody>
    </table>
  </div>
  <div id="seas">
    <canvas id="noise"></canvas>
    <h1 id="title">{data.all.display_name}'s Island</h1>
  </div>
</div>

<style>
  :root {
    --seas: #006994;
    --land: #359b0b;

    --base: #24273a;
  }

  #pfp-holder {
    width: 100%;
    display: flex;
    justify-content: center;
  }

  #page {
    display: flex;
    flex-direction: row;
  }

  #namebar {
    display: flex;

    & > * {
      margin: 0.67em 0 0 0;
    }

    & > a > img {
      margin: 0.67em;
    }
  }

  #sidebar {
    width: 25%;
    min-height: 100vh;
    padding: 2%;
    box-sizing: border-box;

    background-color: var(--base);
  }

  #seas {
    max-height: 100vh;
    min-height: 100vh;
    width: 75%;
    background-color: var(--seas);

    display: flex;
    align-items: center;
    justify-content: center;

    background-image: url("images/wave.png");
    animation: bg-move 60s infinite linear;
  }

  @keyframes bg-move {
    from {
      background-position: 0 0;
    }
    to {
      background-position: 100% 100%;
    }
  }

  #stats {
    background-color: red;
    width: 100%;

    border: none;
    border-collapse: collapse;

    & td {
      width: 50%;
      padding: 0.5em;
    }

    & td:first-child {
      border-right: 1px solid white;
    }
  }

  #title {
    position: absolute;
    text-shadow: 0 0 8px black;
  }
</style>
