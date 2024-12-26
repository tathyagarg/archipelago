<script lang="ts">
  let innerWidth = 0;
  let innerHeight = 0;

  import { onMount } from "svelte";
  import "../../../app.css";

  import big_shipper from "$lib/badges/big_shipper.png";
  import really_big_shipper from "$lib/badges/really_big_shipper.png";
  import ship_happy from "$lib/badges/ship_happy.png";
  import update_master from "$lib/badges/update_master.png";

  let { data }: { data: any } = $props();
  console.log(data);

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

let badges = new Map();
if (biggest_ship.hours >= 20) {
  badges.set("Big Shipper (Shipped a project with 20+ hours)", "🚢");
}

if (biggest_ship.hours >= 50) {
  badges.set("Really Big Shipper (Shipped a project with 50+ hours)", "🚀");
}

if (data.user.ships.length >= 10) {
  badges.set("Ship happy (Shipped 10+ projects)", "🔫");
}

for (let ship of data.user.ships) {
  if (ship.updates.length >= 10) {
    badges.set("Update Master (Updated a project 10+ times)", "🔨");
  }
}

let ship_positions = [1, 2];
</script>

<svelte:window bind:innerWidth bind:innerHeight />

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
      <a href="https://hackclub.slack.com/team/{data.user.id}">
        <img
          src="https://cdn-icons-png.flaticon.com/512/2111/2111615.png"
          alt="slack logo"
          height="30"
        />
      </a>
    </div>
    <h2>Badges</h2>
    <div id="badges">
      {#each badges as badge}
        <div id="badge" title={badge[0]}>
          <span>{badge[1]}</span>
        </div>
      {/each}
    </div>
    <h2>Stats</h2>
    <table id="stats">
      <thead>
        <tr>
          <td>Stat</td>
          <td>Value</td>
        </tr>
      </thead>
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
          <td
            >{data.doubloons.current === -1
              ? "Not found"
              : data.doubloons.current}</td
          >
        </tr>
        <tr>
          <td>All time doubloons</td>
          <td
            >{data.doubloons.all_time === -1
              ? "Not found"
              : data.doubloons.all_time}</td
          >
        </tr>
      </tbody>
    </table>
  </div>
  <div id="seas">
    <canvas id="noise"></canvas>
    <h1 id="title">{data.all.display_name}'s Island</h1>
    <div id="ships">
    </div>
  </div>
</div>

<style>
  :root {
    --seas: #006994;
    --land: #359b0b;

    --base: #24273a;
    --base2: #1e2030;
    --base3: #181926;

    --accent: #8aadf4;
    --light-accent: #8aadf450;
  }

  #ships {
    position: absolute;
    height: 90%;
    width: 65%;

    box-sizing: border-box;
  }

  #ship {
    position: absolute;

    background-image: url("images/ship.png");
    background-size: cover;
    height: 200px;
    width: 100px;
  }

  #badges {
    height: 70px;
    display: flex;
    align-items: center;
    gap: 1em;
    position: relative;
  }

  #badge {
    position: relative;
    display: block;
    overflow: hidden;
    margin: 0;
    display: flex;
    align-items: start;
    aspect-ratio: 1;

    font-size: 2em;
    background-color: var(--accent);
    padding: 0.5em;
    border-radius: 1em;
    border: 3px solid var(--base3);

    box-shadow: 0 0 10px 1px var(--light-accent);
  }

  #pfp-holder {
    width: 100%;
    display: flex;
    justify-content: center;
  }

  #pfp {
    border-radius: 10px;
    box-shadow: 0 0 10px 1px var(--light-accent);
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
    width: 100%;

    border-spacing: 0 1px;
    border-collapse: seperate;
    border-radius: 10px !important;
    overflow: hidden;
    box-shadow: 0 0 10px 1px var(--light-accent);

    & td {
      width: 50%;
      padding: 12px 15px;
      text-align: left;
    }
  }

  #stats thead tr td {
    background-color: var(--base3) !important;
    border-bottom: 2px solid var(--accent) !important;
  }

  #stats tr:nth-of-type(odd) {
    background-color: var(--base2);
  }

  #stats tr:nth-of-type(even) {
    background-color: var(--base3);
  }

  #stats tbody tr {
    border-bottom: 1px solid var(--base);
  }

  #title {
    position: absolute;
    text-shadow: 0 0 8px black;
  }
</style>
