const express = require('express');
const rpio = require('rpio');
const { spawn } = require('node:child_process');

const app = express();

const PORT = 4321;

let playerScore = 0;
let botScore    = 0;

const botGoalPin    = 5;
const playerGoalPin = 6;

rpio.init({mapping: 'gpio'});
rpio.open(botGoalPin, rpio.INPUT);
rpio.open(playerGoalPin, rpio.INPUT);
const ledDriver = spawn('python', ['ledDriver/driver.py'])

app.use('/resources', express.static('resources'));
app.use('/script', express.static('script'));
app.use('/style', express.static('style'));

app.get('/', (req, res) => {
    res.sendFile('index.html', { root: __dirname });
});

function onGoalSensor(pin) {
    if (rpio.read(pin)) { // only give points when puck entered light barrier
        if (pin === playerGoalPin)
            botScore++;
        else if (pin == botGoalPin)
            playerScore++;
    }
    rpio.msleep(50);
}

app.get('/state', (req, res) => {
    res.json({"playerScore": playerScore, "botScore": botScore});
});

let counter = 0;
let animationInterval;

app.get('/animation', (req, res) => {
    clearInterval(animationInterval);
    counter = 0;
    animationInterval = setInterval(() => {
        if (counter == 200) {
            counter = 0;
            clearInterval(animationInterval);
        } else {
            ledDriver.stdin.write("0,0,0;".repeat(counter) + "0,0,255\n");
            counter++;
        }
    }, 15);
    
    res.json({"animation": "ok"});
});

/// Set scores to 0.
app.get('/resetScores', (req, res) => { playerScore = botScore = 0; res.send("scores reset.") });
/// Start counting scores.
app.get('/start', (req, res) => { rpio.poll(botGoalPin, onGoalSensor); rpio.poll(playerGoalPin, onGoalSensor); res.send("started."); });
/// Stop counting scores.
app.get('/stop' , (req, res) => { rpio.poll(botGoalPin, null);         rpio.poll(playerGoalPin, null);         res.send("stopped.");});

app.listen(PORT, () => console.log("Server listening on port", PORT));
