/*
    This file contains the logic from your original battle_3d.js, adapted for Vite.
    - The DiceBox import is now handled by Vite (see top of file).
    - Asset paths may need to be updated to match the Vite public/ directory structure.
*/

import DiceBox from "@3d-dice/dice-box";
import { diceBoxManager } from './diceBoxManager.js';
import { UIManager } from './ui.js';
import { setupGlobalErrorHandler } from './utils.js';

setupGlobalErrorHandler();

class DiceApp {
    constructor() {
        this.uiManager = new UIManager();
        this.diceBoxManager = diceBoxManager;
        this.initUI();
        this.setupEventListeners();
    }

    initUI() {
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
    }

    setupEventListeners() {
        document.getElementById("chooseA").onclick = () => {
            this.showDiceUI('A');
        };
        document.getElementById("chooseB").onclick = () => {
            this.showDiceUI('B');
        };
        document.getElementById("rollem").onclick = () => {
            this.diceBoxManager.rollCurrentCollection(this.uiManager);
            this.uiManager.updateRerollButtons(this.diceBoxManager);
        };
        document.getElementById("reroll").onclick = () => {
            this.diceBoxManager.rollCurrentCollection(this.uiManager);
            this.uiManager.updateRerollButtons(this.diceBoxManager);
        };
        document.getElementById("back").onclick = () => {
            this.hideDiceUI();
        };
    }

    showDiceUI(collectionKey) {
        document.getElementById("collection-select").style.display = "none";
        document.getElementById("dice-ui").style.display = "block";
        this.uiManager.resetRerollingDice();
        this.diceBoxManager.startDiceUI(collectionKey, this.uiManager);
        this.uiManager.updateRerollButtons(this.diceBoxManager);
    }

    hideDiceUI() {
        document.getElementById("dice-ui").style.display = "none";
        document.getElementById("collection-select").style.display = "block";
        this.diceBoxManager.clear();
        document.getElementById('reroll-buttons').innerHTML = '';
        document.getElementById('dice-results').textContent = '';
        this.uiManager.resetRerollingDice();
        this.uiManager.setMainButtonsDisabled(false);
        this.uiManager.updateRerollButtons(this.diceBoxManager);
    }
}

new DiceApp();
