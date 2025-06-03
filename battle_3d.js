console.log('battle_3d.js: script file loaded (top of file)');
import DiceBox from "https://unpkg.com/@3d-dice/dice-box@1.1.3/dist/dice-box.es.min.js";

const collections = {
    "B": ["1d6", "1d10", "1d20"],
    "A": ["1d4", "1d8", "1d12"]
}

let Box = null;

// Add UI state
let currentCollection = null;

// Render the UI immediately
const app = document.getElementById("app");
if (!app) {
  document.body.innerHTML = '<div style="color:red;">Error: #app element not found. Script is running.</div>';
  throw new Error("#app element not found");
}
app.innerHTML = `
  <div id="dice-results" style="text-align:center; font-size:1.2em; margin-top:1em; margin-bottom:1em;"></div>
  <div id="collection-select" style="text-align:center; margin-top:3em;">
    <h2>Choose a Dice Collection</h2>
    <button id="chooseA" class="collection-btn">Collection A</button>
    <button id="chooseB" class="collection-btn">Collection B</button>
  </div>
  <div id="dice-ui" style="display:none;">
    <div id="dice-box"></div>
    <div style="text-align:center; margin-top:1em;">
      <button id="rollem">Roll Dice</button>
      <button id="reroll">Reroll</button>
      <button id="back">Back to Collection Select</button>
      <div id="reroll-buttons" style="margin-top:1em;"></div>
    </div>
  </div>
`;

document.getElementById("chooseA").onclick = () => startDiceUI("A");
document.getElementById("chooseB").onclick = () => startDiceUI("B");

function startDiceUI(collectionKey) {
  currentCollection = collectionKey;
  // Update dice results text immediately to show which collection is active
  const resultsDiv = document.getElementById('dice-results');
  resultsDiv.textContent = `Selected: Collection ${collectionKey}`;
  document.getElementById("collection-select").style.display = "none";
  document.getElementById("dice-ui").style.display = "block";
  // Create DiceBox only after #dice-box exists
  if (!Box) {
    Box = new DiceBox({
      assetPath: "assets/",
      origin: "https://unpkg.com/@3d-dice/dice-box@1.1.3/dist/",
      container: "#dice-box",
      theme: "smooth",
      themeColor: get_random(colors),
      externalThemes: {
        diceOfRolling: "https://www.unpkg.com/@3d-dice/theme-dice-of-rolling@0.2.1",
        smooth: "https://www.unpkg.com/@3d-dice/theme-smooth@0.2.1",
      },
      offscreen: true,
      scale: 15,
      // physics settings that must be set - defaults are buggy
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
    // Clear the dice results text when returning home
    document.getElementById('dice-results').textContent = `Selected: Collection ${collectionKey}`;
    // If already initialized, just roll the current collection';
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

// Track which dice are currently being rerolled
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
      // Disable 'rollem' and 'reroll' while any reroll is in progress
      setMainButtonsDisabled(true);
      // Pass the whole die object (notation object) to reroll
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
          // Only re-enable main buttons if no rerolls are in progress
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

// Button event listeners
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
    // Clear the dice results text when returning home
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

// Add a global error handler for debugging
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
  // Disable/enable reroll die buttons
  const rerollDiv = document.getElementById('reroll-buttons');
  if (rerollDiv) {
    Array.from(rerollDiv.querySelectorAll('button')).forEach(btn => {
      btn.disabled = disabled;
    });
  }
}
