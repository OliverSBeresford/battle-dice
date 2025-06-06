import { getBox, isRollingAll } from './diceBoxManager.js';

let rerollingDice = new Set();

export function updateDiceResults() { 
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

export function updateRerollButtons(setMainButtonsDisabled, updateDiceResults) {
    const rerollDiv = document.getElementById('reroll-buttons');
    rerollDiv.innerHTML = '';
    if (!window.lastRollResults || !Array.isArray(window.lastRollResults)) return;
    const Box = getBox();
    const rollingAll = isRollingAll();
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
                    updateRerollButtons(setMainButtonsDisabled, updateDiceResults);
                    updateDiceResults();
                })
                .finally(() => {
                    rerollingDice.delete(idx);
                    if (rerollingDice.size === 0 && !isRollingAll()) setMainButtonsDisabled(false);
                    updateRerollButtons(setMainButtonsDisabled, updateDiceResults);
                });
        };
        rerollDiv.appendChild(btn);
    });
    updateDiceResults();
}

export function resetRerollingDice() {
    rerollingDice.clear();
}

export function setMainButtonsDisabled(disabled) {
    ["rollem", "reroll", "back"].forEach(id => {
        const btn = document.getElementById(id);
        if (btn) btn.disabled = disabled;
    });
}


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
