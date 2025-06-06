/*
  This file contains the logic from your original battle_3d.js, adapted for Vite.
  - The DiceBox import is now handled by Vite (see top of file).
  - Asset paths may need to be updated to match the Vite public/ directory structure.
*/

import DiceBox from "@3d-dice/dice-box";

const collections = {
    "B": ["1d6", "1d10", "1d20"],
    "A": ["1d4", "1d8", "1d12"]
};

let Box = null;
let currentCollection = null;

const app = document.getElementById("app");
if (!app) {
  document.body.innerHTML = '<div style="color:red;">Error: #app element not found. Script is running.</div>';
  throw new Error("#app element not found");
}
app.innerHTML = `
  <div id="dice-results" style="text-align:center; font-size:1.2em; margin-top:1em; margin-bottom:1em; position:relative; z-index:2;"></div>
  <div id="collection-select" style="text-align:center; margin-top:3em; position:relative; z-index:2;">
    <h2>Choose a Dice Collection</h2>
    <button id="chooseA" class="collection-btn">Collection A</button>
    <button id="chooseB" class="collection-btn">Collection B</button>
  </div>
  <div id="dice-ui" style="display:none; position:fixed; top:0; left:0; width:100vw; height:100vh; z-index:0;">
    <div id="dice-box" style="position:absolute; top:0; left:0; width:100vw; height:100vh; z-index:0;"></div>
    <div style="position:fixed; left:0; bottom:0; width:100vw; z-index:2; text-align:center; pointer-events:none;">
      <div style="margin-bottom:2em; pointer-events:auto;">
        <button id="rollem">Roll Dice</button>
        <button id="reroll">Reroll</button>
        <button id="back">Back to Collection Select</button>
        <div id="reroll-buttons" style="margin-top:1em;"></div>
      </div>
    </div>
  </div>
`;

document.getElementById("chooseA").onclick = () => startDiceUI("A");
document.getElementById("chooseB").onclick = () => startDiceUI("B");

function startDiceUI(collectionKey) {
  currentCollection = collectionKey;
  const resultsDiv = document.getElementById('dice-results');
  resultsDiv.textContent = `Selected: Collection ${collectionKey}`;
  document.getElementById("collection-select").style.display = "none";
  document.getElementById("dice-ui").style.display = "block";
  if (!Box) {
    Box = new DiceBox({
      assetPath: "/assets/dice-box/", // Vite serves public/ as root
      container: "#dice-box",
      theme: "theme-smooth",
      themeColor: get_random(colors),
      offscreen: true,
      scale: 15,
      throwForce: 5,
      gravity: 3,
      mass: 1,
      spinForce: 10,
    });
  }
  if (!Box._initialized) {
    Box.init().then(() => {
      Box._initialized = true;
      rollCurrentCollection();
    });
  } else {
    document.getElementById('dice-results').textContent = `Selected: Collection ${collectionKey}`;
    rollCurrentCollection();
  }
}

function updateDiceResults() {
  const resultsDiv = document.getElementById('dice-results');
  if (!window.lastRollResults || !Array.isArray(window.lastRollResults) || window.lastRollResults.length === 0) {
    resultsDiv.textContent = '';
    return;
  }
  let total = 0;
  let details = window.lastRollResults.map((die, idx) => {
    const value = die.value || die.result || die.total || 0;
    total += value;
    return `${die.sides}-sided: <b>${value}</b>`;
  }).join(' &nbsp; | &nbsp; ');
  resultsDiv.innerHTML = `Dice: ${details} &nbsp; &nbsp; <span style='font-weight:bold;'>Total: ${total}</span>`;
}

let rerollingDice = new Set();
let rollingAll = false;

function setMainButtonsDisabled(disabled) {
  ["rollem", "reroll", "back"].forEach(id => {
    const btn = document.getElementById(id);
    if (btn) btn.disabled = disabled;
  });
}

function updateRerollButtons() {
  const rerollDiv = document.getElementById('reroll-buttons');
  rerollDiv.innerHTML = '';
  if (!window.lastRollResults || !Array.isArray(window.lastRollResults)) return;
  window.lastRollResults.forEach((die, idx) => {
    const btn = document.createElement('button');
    btn.textContent = `Reroll ${die.sides}-sided Die #${idx+1}`;
    btn.disabled = rollingAll || rerollingDice.has(idx);
    btn.onclick = () => {
      rerollingDice.add(idx);
      btn.disabled = true;
      setMainButtonsDisabled(true);
      Box.reroll(die, { remove: true, newStartPoint: true })
        .then((rerolledDiceArr) => {
          if (window.lastRollResults && Array.isArray(window.lastRollResults)) {
            window.lastRollResults[idx] = rerolledDiceArr[0];
          }
          updateRerollButtons();
          updateDiceResults();
        })
        .finally(() => {
          rerollingDice.delete(idx);
          if (rerollingDice.size === 0 && !rollingAll) setMainButtonsDisabled(false);
          updateRerollButtons();
        });
    };
    rerollDiv.appendChild(btn);
  });
  updateDiceResults();
}

function rollCurrentCollection() {
  Box.clear();
  rollingAll = true;
  setMainButtonsDisabled(true);
  updateRerollButtons();
  Box.roll(collections[currentCollection])
    .then((rollResults) => {
      window.lastRollResults = rollResults;
      updateRerollButtons();
      updateDiceResults();
    })
    .finally(() => {
      rollingAll = false;
      setMainButtonsDisabled(false);
      updateRerollButtons();
    });
}

document.addEventListener("click", (e) => {
  if (e.target.id === "rollem") {
    rollingAll = true;
    setMainButtonsDisabled(true);
    updateRerollButtons();
    Box.roll(collections[currentCollection], {
      themeColor: get_random(colors),
    }).then((rollResults) => {
      window.lastRollResults = rollResults;
      updateRerollButtons();
      updateDiceResults();
    }).finally(() => {
      rollingAll = false;
      setMainButtonsDisabled(false);
      updateRerollButtons();
    });
  } else if (e.target.id === "reroll") {
    rollingAll = true;
    setMainButtonsDisabled(true);
    updateRerollButtons();
    Box.roll(collections[currentCollection], {
      themeColor: get_random(colors),
    }).then((rollResults) => {
      window.lastRollResults = rollResults;
      updateRerollButtons();
      updateDiceResults();
    }).finally(() => {
      rollingAll = false;
      setMainButtonsDisabled(false);
      updateRerollButtons();
    });
  } else if (e.target.id === "back") {
    document.getElementById("dice-ui").style.display = "none";
    document.getElementById("collection-select").style.display = "block";
    Box.clear();
    document.getElementById('reroll-buttons').innerHTML = '';
    document.getElementById('dice-results').textContent = '';
    rerollingDice.clear();
    rollingAll = false;
    setMainButtonsDisabled(false);
  }
});

const colors = [
  "#348888",
  "#22BABB",
  "#9EF8EE",
  "#FA7F08",
  "#F24405",
  "#F25EB0",
  "#B9BF04",
  "#F2B705",
  "#F27405",
  "#F23005",
];

function get_random(list) {
  return list[Math.floor(Math.random() * list.length)];
}

window.addEventListener('error', function(e) {
  const errDiv = document.createElement('div');
  errDiv.style = 'color:red;white-space:pre-wrap;';
  errDiv.textContent = 'JS Error: ' + e.message + '\n' + (e.error && e.error.stack ? e.error.stack : '');
  document.body.appendChild(errDiv);
});

function setButtonsDisabled(disabled) {
  ["rollem", "reroll", "back"].forEach(id => {
    const btn = document.getElementById(id);
    if (btn) btn.disabled = disabled;
  });
  const rerollDiv = document.getElementById('reroll-buttons');
  if (rerollDiv) {
    Array.from(rerollDiv.querySelectorAll('button')).forEach(btn => {
      btn.disabled = disabled;
    });
  }
}
