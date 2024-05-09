var gameStopped = true;
const gameTime = 600; // 10 Mins

setInterval(() => {
    fetch("state").then((res) => res.json().then((json) => {
        gpio5.value = json.gpio5;
        gpio6.value = json.gpio6;
    }))
}, 500);

function startGame() {
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
    var timer = duration;
    var minutes, seconds;
    var intervalId; // Store the interval ID

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
}