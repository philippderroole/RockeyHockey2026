const gameTime = 600; // 10 Mins
let gameStopped = true;
let scoreGpio5 = 0;
let scoreGpio6 = 0;

setInterval(() => {
    fetch("state").then((res) => res.json().then((json) => {
        if (json.gpio5 === "1") {
            scoreGpio5++;
        }
        if (json.gpio6 === "1") {
            scoreGpio6++;
        }

        gpio5.value = scoreGpio5; //bot?
        gpio6.value = scoreGpio6; //prof?

        let difference = Math.abs(gpio5.value - gpio6.value);

        if (gpio5.value > gpio6.value && difference > 2) {
            godlikeAudio.play();
            playGIF('bot');
        } else if (gpio5.value < gpio6.value && difference > 2) {
            unstoppableAudio.play();
            playGIF('prof');
        }
    }))
}, 500);

function startGame() {
    scoreGpio5 = scoreGpio6 = 0;
    startAudio.play();
    backgroundAudio.play();
    gameStopped = false;
    startTimer(gameTime);
};

function stopGame() {
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

function playGIF(player) {
    const gifElement = document.getElementById('score-gif');
    const scoreboard = document.getElementById('scoreboard');

    if (player === 'prof') {
        gifElement.src = 'resources/gifs/pulp.gif';
    } else if (player === 'bot') {
        gifElement.src = 'resources/gifs/losingteeth.gif';
    }

    scoreboard.style.display = 'block';

    setTimeout(() => {
        scoreboard.style.display = 'none';
    }, 3000);
};

function animation() {
    fetch("animation");
};
