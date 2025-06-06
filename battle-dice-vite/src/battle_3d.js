/*
    This file contains the logic from your original battle_3d.js, adapted for Vite.
    - The DiceBox import is now handled by Vite (see top of file).
    - Asset paths may need to be updated to match the Vite public/ directory structure.
*/

import DiceBox from "@3d-dice/dice-box";
import { startDiceUI } from './diceBoxManager.js';
import { updateDiceResults, updateRerollButtons, setMainButtonsDisabled } from './ui.js';
import { colors, get_random, setupGlobalErrorHandler } from './utils.js';

setupGlobalErrorHandler();

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

document.getElementById("chooseA").onclick = () => startDiceUI("A", setMainButtonsDisabled, (a, b) => updateRerollButtons(setMainButtonsDisabled, updateDiceResults), updateDiceResults);
document.getElementById("chooseB").onclick = () => startDiceUI("B", setMainButtonsDisabled, (a, b) => updateRerollButtons(setMainButtonsDisabled, updateDiceResults), updateDiceResults);

// Button event listeners for roll, reroll, back
// These must use the modular functions and pass the correct parameters

document.addEventListener("click", (e) => {
    if (e.target.id === "rollem") {
        // Roll all dice
        import('./diceBoxManager.js').then(({ rollCurrentCollection }) => {
            rollCurrentCollection(setMainButtonsDisabled, (a, b) => updateRerollButtons(setMainButtonsDisabled, updateDiceResults), updateDiceResults);
        });
    } else if (e.target.id === "reroll") {
        // Reroll all dice
        import('./diceBoxManager.js').then(({ rollCurrentCollection }) => {
            rollCurrentCollection(setMainButtonsDisabled, (a, b) => updateRerollButtons(setMainButtonsDisabled, updateDiceResults), updateDiceResults);
        });
    } else if (e.target.id === "back") {
        document.getElementById("dice-ui").style.display = "none";
        document.getElementById("collection-select").style.display = "block";
        import('./diceBoxManager.js').then(({ getBox }) => {
            const Box = getBox();
            if (Box) Box.clear();
        });
        document.getElementById('reroll-buttons').innerHTML = '';
        document.getElementById('dice-results').textContent = '';
        import('./ui.js').then(({ resetRerollingDice }) => {
            resetRerollingDice();
        });
        setMainButtonsDisabled(false);
    }
});
