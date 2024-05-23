const gameTime = 600; // 10 Mins
let gameStopped = true;

setInterval(() => {
    fetch("state").then((res) => res.json().then((json) => {
        const playerIncrement = json.playerScore - playerScoreField.value;
        const botIncrement    = json.botScore    - botScoreField.value;
        const playerLead      = json.playerScore - json.botScore;

        if (playerIncrement > 0) {
            if (playerLead == 2) {
                playGIF('losingteeth');
                goalAudio.src = 'resources/sounds/godlike.wav';
                goalAudio.play();
            } else if (playerLead > 4) {
                playGIF('dominance');
                goalAudio.src = 'resources/sounds/dominating.wav';
                goalAudio.play();
            }
        }
        if (botIncrement > 0)
        {
            if (playerLead == -2) {
                playGIF('pulp');
                goalAudio.src = 'resources/sounds/unstoppable.wav';
                goalAudio.play();
            } else if (playerLead < -4) {
                playGIF('godzilla');
                goalAudio.src = 'resources/sounds/rampage.wav';
                goalAudio.play();
            }
        }

        playerScoreField.value = json.playerScore;
        botScoreField.value = json.botScore;
    }))
}, 500);

async function startGame() {
    await fetch("resetScores");
    await fetch("start");
    startAudio.play();
    backgroundAudio.play();
    gameStopped = false;
    startTimer(gameTime);
};

async function stopGame() {
    await fetch("stop");
    backgroundAudio.pause();
    backgroundAudio.currentTime = 0;
    gameStopped = true;
};

function startTimer(duration) {
    let timer = duration;
    let minutes, seconds;
    let intervalId;

  intervalId = setInterval(function () {
    minutes = parseInt(timer / 60, 10);
    seconds = parseInt(timer % 60, 10);

    minutes = minutes < 10 ? "0" + minutes : minutes;
    seconds = seconds < 10 ? "0" + seconds : seconds;

    countdown.value = minutes + ":" + seconds;

        if (--timer < 0) {
            timer = duration;
        }

        if (gameStopped) {
            clearInterval(intervalId);
        }
    }, 1000);
};

function playGIF(gifName) {
    const gifElement = document.getElementById('score-gif');
    const scoreboard = document.getElementById('scoreboard');

    if (gifName === 'pulp') {
        gifElement.src = 'resources/gifs/pulp.gif';
    } else if (gifName === 'losingteeth') {
        gifElement.src = 'resources/gifs/losingteeth.gif';
    } else if (gifName === 'godzilla') {
        gifElement.src = 'resources/gifs/godzilla.gif';
    } else if (gifName === 'dominance') {
        gifElement.src = 'resources/gifs/dominance.gif';
    }

    scoreboard.style.display = 'block';

    setTimeout(() => {
        scoreboard.style.display = 'none';
    }, 3000);
};

function animation() {
    fetch("animation");
};
