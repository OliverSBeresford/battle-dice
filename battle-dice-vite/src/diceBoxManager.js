// diceBoxManager.js
// Usage:
//   import { startDiceUI, rollCurrentCollection, getBox, getCurrentCollection, isRollingAll } from './diceBoxManager.js';
//
//   startDiceUI(collectionKey, setMainButtonsDisabled, updateRerollButtons, updateDiceResults);
//     - Initializes and shows the dice UI for the given collectionKey (e.g. 'A' or 'B').
//     - Requires you to pass UI update functions: setMainButtonsDisabled, updateRerollButtons, updateDiceResults.
//
//   rollCurrentCollection(setMainButtonsDisabled, updateRerollButtons, updateDiceResults);
//     - Rolls the dice for the current collection. Also requires UI update functions.
//
//   getBox();
//     - Returns the DiceBox instance (for advanced control or rerolling individual dice).
//
//   getCurrentCollection();
//     - Returns the current collection key (e.g. 'A' or 'B').
//
//   isRollingAll();
//     - Returns true if a roll is in progress.

import DiceBox from "@3d-dice/dice-box";
import { colors, get_random } from './utils.js';

let Box = null;
let currentCollection = null;
let rollingAll = false;
let collections = {
    "B": ["1d6", "1d10", "1d20"],
    "A": ["1d4", "1d8", "1d12"]
};

export function startDiceUI(collectionKey, setMainButtonsDisabled, updateRerollButtons, updateDiceResults) {
    currentCollection = collectionKey;
    const resultsDiv = document.getElementById('dice-results');
    resultsDiv.textContent = `Selected: Collection ${collectionKey}`;
    document.getElementById("collection-select").style.display = "none";
    document.getElementById("dice-ui").style.display = "block";
    if (!Box) {
        Box = new DiceBox({
            assetPath: "/assets/dice-box/", // Vite serves public/ as root
            container: "#dice-box",
            theme: "theme-dice-of-rolling",
            themeColor: get_random(colors),
            offscreen: true,
            scale: 13,
            throwForce: 5,
            gravity: 3,
            mass: 1,
            spinForce: 10,
        });
    }
    if (!Box._initialized) {
        Box.init().then(() => {
            Box._initialized = true;
            rollCurrentCollection(setMainButtonsDisabled, updateRerollButtons, updateDiceResults);
        });
    } else {
        document.getElementById('dice-results').textContent = `Selected: Collection ${collectionKey}`;
        rollCurrentCollection(setMainButtonsDisabled, updateRerollButtons, updateDiceResults);
    }
}

export function rollCurrentCollection(setMainButtonsDisabled, updateRerollButtons, updateDiceResults) {
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

export function getBox() {
    return Box;
}

export function getCurrentCollection() {
    return currentCollection;
}

export function isRollingAll() {
    return rollingAll;
}
