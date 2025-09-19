export class UIManager {
    constructor() {
        this.rerollingDice = new Set();
    }

    setResultsText(text) {
        const resultsDiv = document.getElementById('dice-results');
        if (resultsDiv) {
            resultsDiv.textContent = text;
            console.log("Results updated:", text);
        } else {
            console.error("Results div not found");
        }
    }


    showDiceUI () {
        document.getElementById("collection-select").style.display = "none";
        document.getElementById("dice-ui").style.display = "block";
    }

    updateDiceResults(diceBoxManager) { 
        const resultsDiv = document.getElementById('dice-results');
        const results = diceBoxManager.getLastRollResults();
        if (!results || !Array.isArray(results) || results.length === 0) {
            resultsDiv.textContent = '';
            return;
        }
        let total = 0;
        let details = results.map((die, idx) => {
            const value = die.value || die.result || die.total || 0;
            total += value;
            return `${die.sides}-sided: <b>${value}</b>`;
        }).join(' &nbsp; | &nbsp; ');
        resultsDiv.innerHTML = `Dice: ${details} &nbsp; &nbsp; <span style='font-weight:bold;'>Total: ${total}</span>`;
    }

    updateRerollButtons(diceBoxManager) {
        const rerollDiv = document.getElementById('reroll-buttons');
        rerollDiv.innerHTML = '';
        const results = diceBoxManager.getLastRollResults();
        if (!results || !Array.isArray(results)) return;
        const Box = diceBoxManager.getBox();
        const rollingAll = diceBoxManager.isRollingAll();
        results.forEach((die, idx) => {
            const btn = document.createElement('button');
            btn.textContent = `Reroll ${die.sides}-sided Die #${idx+1}`;
            btn.disabled = rollingAll || this.rerollingDice.has(idx);
            btn.onclick = () => {
                this.rerollingDice.add(idx);
                btn.disabled = true;
                this.setMainButtonsDisabled(true);
                Box.reroll(die, { remove: true, newStartPoint: true })
                    .then((rerolledDiceArr) => {
                        if (Array.isArray(rerolledDiceArr) && rerolledDiceArr[0]) {
                            const allResults = diceBoxManager.getLastRollResults();
                            allResults[idx] = rerolledDiceArr[0];
                        }
                        this.updateRerollButtons(diceBoxManager);
                        this.updateDiceResults(diceBoxManager);
                    })
                    .finally(() => {
                        this.rerollingDice.delete(idx);
                        if (this.rerollingDice.size === 0 && !diceBoxManager.isRollingAll()) this.setMainButtonsDisabled(false);
                        this.updateRerollButtons(diceBoxManager);
                    });
            };
            rerollDiv.appendChild(btn);
        });
        this.updateDiceResults(diceBoxManager);
    }

    resetRerollingDice() {
        this.rerollingDice.clear();
    }

    setMainButtonsDisabled(disabled) {
        ["rollem", "reroll", "back"].forEach(id => {
            const btn = document.getElementById(id);
            if (btn) btn.disabled = disabled;
        });
    }

    setButtonsDisabled(disabled) {
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
}
