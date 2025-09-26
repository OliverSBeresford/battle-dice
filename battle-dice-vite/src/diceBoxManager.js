// diceBoxManager.js
import DiceBox from "@3d-dice/dice-box";
import { colors, get_random } from './utils.js';

class DiceBoxManager {
    constructor() {
        this.Box = null;
        this.currentCollection = null;
        this.rollingAll = false;
        this.collections = {
            "B": ["1d6", "1d10", "1d20"],
            "A": ["1d4", "1d8", "1d12"]
        };
        this.lastRollResults = [];
    }

    startDiceUI(collectionKey, uiManager) {
        this.currentCollection = collectionKey;
        uiManager.setResultsText(`Selected: Collection ${collectionKey}`);
        uiManager.showDiceUI();
        if (!this.Box) {
            this.Box = new DiceBox({
                assetPath: "/assets/dice-box/",
                container: "#dice-box",
                theme: "theme-smooth",
                themeColor: get_random(colors),
                offscreen: true,
                scale: 13,
                throwForce: 5,
                gravity: 3,
                mass: 1,
                spinForce: 10,
            });
        }
        if (!this.Box._initialized) {
            this.Box.init().then(() => {
                this.Box._initialized = true;
                this.rollCurrentCollection(uiManager);
            });
        } else {
            this.Box.updateConfig({
                themeColor: get_random(colors)
            })
            this.rollCurrentCollection(uiManager);
        }
    }

    rollCurrentCollection(uiManager) {
        if (!this.Box) return;
        this.Box.clear();
        this.rollingAll = true;
        uiManager.setMainButtonsDisabled(true);
        uiManager.updateRerollButtons(this);
        this.Box.roll(this.collections[this.currentCollection])
            .then((rollResults) => {
                this.lastRollResults = rollResults;
                uiManager.updateRerollButtons(this);
                uiManager.updateDiceResults(this);
            })
            .finally(() => {
                this.rollingAll = false;
                uiManager.setMainButtonsDisabled(false);
                uiManager.updateRerollButtons(this);
            });
    }

    getBox() {
        return this.Box;
    }

    getCurrentCollection() {
        return this.currentCollection;
    }

    isRollingAll() {
        return this.rollingAll;
    }

    getLastRollResults() {
        return this.lastRollResults;
    }

    clear() {
        if (this.Box) this.Box.clear();
        this.lastRollResults = [];
    }
}

export const diceBoxManager = new DiceBoxManager();
